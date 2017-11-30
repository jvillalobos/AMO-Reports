#!/usr/bin/env python

import sys;
import subprocess;
import getpass;
import re;
from datetime import date, datetime, timedelta;

AMO_DB = "addons_mozilla_org";
DATE_FORMAT = "%Y-%m-%d";
SHORT_MONTH_FORMAT = "%b";

# DB access information.
db_access = { "host" : "", "user" : "", "password" : ""};
# this is where we'll store all the DB results.
results = {};

def main():
  if (3 == len(sys.argv)):
    if ((None != re.match("^[\w\.\-]+$", sys.argv[1])) &
        (None != re.match("^\w+$", sys.argv[2]))):
      # get password from standard input.
      pwd = getpass.getpass();

      if (re.match("^\w+$", pwd)):
          db_access["host"] = sys.argv[1];
          db_access["user"] = sys.argv[2];
          db_access["password"] = pwd;
          runReport();
      else:
        print("Invalid password.");
    else:
      print("Invalid host or username.");
  else:
    print("Usage: " + sys.argv[0] + " host username");
    print("Example:");
    print("\t" + sys.argv[0] + " db.example.com johndoe");

  return;

def runReport():
  endDate = date.today();
  startDate = endDate - timedelta(days=7);
  startDateStr = startDate.strftime(DATE_FORMAT);
  endDateStr = endDate.strftime(DATE_FORMAT);
  endDateMonthStr = endDate.strftime(SHORT_MONTH_FORMAT);

  # run all the scripts first to get the server warnings out of the way.
  creation = runScript("creation.sql");
  webextensions = runScript("webextensions.sql");
  points = runScript("points.sql");
  contributions = runScript("contributions.sql");
  totals = runScript("totals.sql");
  monthly = runScript("monthly.sql");
  post = runScript("post.sql");

  # internal add-ons report.
  print("\nAdd-on and version creation\n");
  print(creation);
  print("WebExtensions\n");
  print(webextensions);

  # internal reviewer report (also used in public forum posting).
  processPoints(points);
  processContributions(contributions);
  processTotals(totals);
  processMonthly(monthly);
  processPostReview(post);

  email = getEmailOutput(startDateStr, endDateStr, endDateMonthStr);

  print(
    "Weekly Add-on Reviews Report, v1.1, " + endDateStr + "\n");
  print(email);
  return;

def runScript(filename):
  script = open(filename);
  output = subprocess.check_output(
    [ "mysql", ("-h" + db_access["host"]), AMO_DB, ("-u" + db_access["user"]),
     ("-p" + db_access["password"]) ],
    stdin=script);
  script.close();
  #print("Output:\n" + output);
  return output;

def processPoints(output):
  results["points"] = [];
  lines = output.splitlines();
  del lines[0];

  for line in lines:
      columns = line.split(None, 2);
      results["points"].append(
        { "total" : columns[0], "level" : columns[1], "name": columns[2] });
  return;

def processContributions(output):
  results["contributions"] = [];
  lines = output.splitlines();
  del lines[0];

  for line in lines:
      columns = line.split(None, 2);
      results["contributions"].append(
        { "total" : columns[0], "admin": columns[1], "name" : columns[2] });
  return;

def processTotals(output):
  lines = output.splitlines();
  columns = lines[1].split();
  results["totals"] = {
    "total" : columns[0], "community" : columns[1], "auto": columns[2] };
  return;

def processMonthly(output):
  lines = output.splitlines();
  results["monthly"] = lines[1];
  return;

def processPostReview(output):
  # remove fist line.
  lines = output.splitlines()[1:];

  results["post_review"] = {};
  total = 0;

  for line in lines:
    columns = line.split();
    results["post_review"][columns[0]] = int(columns[1]);
    total += int(columns[1]);

  results["post_review"]["total"] = str(total);
  return;

def getReportOutput(startDateStr, endDateStr):
  output = "Add-ons report\n";
  output += getDoubleTextLine() + "\n";

  return output;

def getEmailOutput(startDateStr, endDateStr, endDateMonthStr):
  output = "WEEKLY ADD-ON REVIEWS REPORT\n";
  output += startDateStr + " - " + endDateStr + "\n";
  output += getDoubleTextLine() + "\n";
  output += "SCORES AND LEVELS (level 1 and above):\n"
  output += getTextLine() + "\n";
  output += "  Total  Level   Name\n";

  for pointEntry in results["points"]:
    level = int(pointEntry["level"]);

    if (0 < level):
      output += pointEntry["total"].rjust(7) + pointEntry["level"].rjust(7);
      output += "   " + pointEntry["name"] + "\n";
    else:
      break;

  output += "\nSee also: https://addons.mozilla.org/editors/leaderboard/\n\n";
  output += "CONTRIBUTIONS (5 reviews or more, code or content):\n"
  output += getTextLine() + "\n";
  output += "Total   Name\n";

  for contribEntry in results["contributions"]:
    total = int(contribEntry["total"]);

    if (5 <= total):
      output += contribEntry["total"].rjust(5);
      output += "   " + contribEntry["name"];

      if ("1" == contribEntry["admin"]):
        output += " *";

      output += "\n";
    else:
      break;

  output += "\n* - Non-volunteers\n";
  output += "\nVolunteer contribution ratio:\n";

  totalHuman = int(results["totals"]["total"]) - int(results["totals"]["auto"]);

  output += "\nTotal reviews: " + str(totalHuman);
  output += "\nVolunteer reviews: " + results["totals"]["community"];
  output += " (" + str(rate(results["totals"]["community"], totalHuman)) + "%)";
  output += "\n\nAutomatic reviews: " + str(results["totals"]["auto"]);

  output += "\n\nTotal contributions (listed):\n\n";
  output += endDateMonthStr.ljust(5)
  output += str(results["monthly"]);

  output += "\n\nPOST-REVIEW:\n"
  output += getTextLine();

  output += "\nTotal: " + results["post_review"]["total"] + "\n";
  output += "\n* Risk *";
  output += ("\nHighest:").ljust(10) + str(postRateStr("highest")).rjust(11);
  output += ("\nHigh:").ljust(10) + str(postRateStr("high")).rjust(11);
  output += ("\nMedium:").ljust(10) + str(postRateStr("medium")).rjust(11);
  output += ("\nLow:").ljust(10) + str(postRateStr("low")).rjust(11);

  return output;

def getTextLine():
  return "----------------------------------------------------------\n";

def getDoubleTextLine():
  return "==========================================================\n";

def rate(part, total):
  return int(round((float(part) / float(total)) * 100));

def postRateStr(risk):
  count = 0;

  if (risk in results["post_review"]):
    count = results["post_review"][risk];

  rateStr = str(count) + " (";
  rateStr += str(rate(count, results["post_review"]["total"])) + "%)";

  return rateStr;

main();
