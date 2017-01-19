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

  # internal add-ons report.
  print("Waiting times\n");
  print(runScript("waiting.sql"));
  print("Add-on and version creation\n");
  print(runScript("creation.sql"));
  print("WebExtensions\n");
  print(runScript("webextensions.sql"));

  # internal reviewer report (also used in public forum posting).
  processPoints(runScript("points.sql"));
  processContributions(runScript("contributions.sql"));
  processTotals(runScript("totals.sql"));
  processMonthly(runScript("monthly.sql"));
  processQueues(runScript("queues.sql"));

  email = getEmailOutput(startDateStr, endDateStr, endDateMonthStr);

  print("Reviewer report\n");
  print(
    "SUBJECT: Weekly Add-on Reviews Report, v 0.12, " + endDateStr + "\n");
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
      columns = line.split(None, 5);
      results["contributions"].append(
        { "total" : columns[0], "new" : columns[1], "updates": columns[2],
          "admin" : columns[3], "info": columns[4], "name": columns[5] });
  return;

def processTotals(output):
  lines = output.splitlines();
  columns = lines[1].split();
  results["totals"] = {
    "total" : columns[0], "community" : columns[1], "auto": columns[2] };
  return;

def processMonthly(output):
  lines = output.splitlines();
  columns = lines[1].split();
  results["monthly"] = {
    "new" : columns[0], "updates" : columns[1], "admin": columns[2],
    "info" : columns[3], "total": columns[4] };
  return;

def processQueues(output):
  lines = output.splitlines();
  green = lines[1].split();
  yellow = lines[2].split();
  red = lines[3].split();
  results["queue_new"] = {
    "green" : green[1], "yellow" : yellow[1], "red": red[1],
    "total" : str(int(green[1]) + int(yellow[1]) + int(red[1])) };
  results["queue_updates"] = {
    "green" : green[2], "yellow" : yellow[2], "red": red[2],
    "total" : str(int(green[2]) + int(yellow[2]) + int(red[2])) };
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
  output += "CONTRIBUTIONS (5 reviews or more):\n"
  output += getTextLine() + "\n";
  output += "Total   New   Upd   Adm   Inf   Name\n";

  for contribEntry in results["contributions"]:
    total = int(contribEntry["total"]);

    if (5 <= total):
      output += contribEntry["total"].rjust(5);
      output += contribEntry["new"].rjust(6);
      output += contribEntry["updates"].rjust(6);
      output += contribEntry["admin"].rjust(6);
      output += contribEntry["info"].rjust(6);
      output += "   " + contribEntry["name"] + "\n";
    else:
      break;

  output += "\n* - Non-volunteers\n\n";

  output += "New - New add-ons, approved or denied.\n";
  output += "Upd - Updates, approved or denied.\n";
  output += "Adm - Escalations for admin review.\n";
  output += "Inf - Information requests to authors for updates and nominations.\n";
  output += "\nVolunteer contribution ratio:\n";

  totalHuman = int(results["totals"]["total"]) - int(results["totals"]["auto"]);

  output += "\nTotal reviews: " + str(totalHuman);
  output += "\nVolunteer reviews: " + results["totals"]["community"];
  output += " (" + str(rate(results["totals"]["community"], totalHuman)) + "%)";
  output += "\n\nAutomatic (unlisted) reviews: " + str(results["totals"]["auto"]);

  output += "\n\nTotal contributions (listed):\n\n";
  output += "     New add-ons    Updates  Admin flag    Info req  Total\n";
  output += endDateMonthStr.ljust(5)
  output += str(monthlyRateStr("new")).rjust(11);
  output += str(monthlyRateStr("updates")).rjust(11)
  output += str(monthlyRateStr("admin")).rjust(12);
  output += str(monthlyRateStr("info")).rjust(12);
  output += str(results["monthly"]["total"]).rjust(7);

  output += "\n\nREVIEW QUEUE STATE:\n"
  output += getTextLine();

  output += "\n* New add-ons *\n";
  output += "\nQueue length by waiting times:\n";
  output += "\n             10 days+     5-10 days       5 days-    Total\n";
  output += "Now    ";
  output += str(queueRateStr("queue_new", "red")).rjust(14);
  output += str(queueRateStr("queue_new", "yellow")).rjust(14);
  output += str(queueRateStr("queue_new", "green")).rjust(14);
  output += str(results["queue_new"]["total"]).rjust(9);

  output += "\n\n* Updates *\n";
  output += "\nQueue length by waiting times:\n";
  output += "\n             10 days+     5-10 days       5 days-    Total\n";
  output += "Now    ";
  output += str(queueRateStr("queue_updates", "red")).rjust(14);
  output += str(queueRateStr("queue_updates", "yellow")).rjust(14);
  output += str(queueRateStr("queue_updates", "green")).rjust(14);
  output += str(results["queue_updates"]["total"]).rjust(9);

  output += "\n\nMORE:\n";
  output += getTextLine();
  output += "https://addons.mozilla.org/editors/performance\n";

  return output;

def getTextLine():
  return "----------------------------------------------------------\n";

def getDoubleTextLine():
  return "==========================================================\n";

def rate(part, total):
  return int(round((float(part) / float(total)) * 100));

def monthlyRateStr(index):
  monthItem = results["monthly"][index];
  rateStr = monthItem + " (";
  rateStr += str(rate(monthItem, results["monthly"]["total"])) + "%)";

  return rateStr;

def queueRateStr(queue, color):
  queueItem = results[queue][color];
  rateStr = queueItem + " (";
  rateStr += str(rate(queueItem, results[queue]["total"])) + "%)";

  return rateStr;

main();
