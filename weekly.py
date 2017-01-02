#!/usr/bin/env python

import subprocess;
import getpass;
import re;
from datetime import date, datetime, timedelta;

AMO_DB = "addons_mozilla_org";
AMO_DB_USER = "jvillalobos";
AMO_DB_SERVER = "db-slave-amoprod1.amo.us-west-2.prod.mozaws.net";
DATE_FORMAT = "%Y-%m-%d";
SHORT_MONTH_FORMAT = "%b";

# this is where we'll store all the DB results.
results = {};

def main():
  endDate = date.today();
  startDate = endDate - timedelta(days=7);
  startDateStr = startDate.strftime(DATE_FORMAT);
  endDateStr = endDate.strftime(DATE_FORMAT);
  endDateMonthStr = endDate.strftime(SHORT_MONTH_FORMAT);

  # get password from standard input.
  pwd = getpass.getpass();

  if (re.match("^\w+$", pwd)):
    # internal add-ons report.
    print("Waiting times\n");
    print(runScript("waiting.sql", pwd));
    print("Add-on and version creation\n");
    print(runScript("creation.sql", pwd));
    print("WebExtensions\n");
    print(runScript("webextensions.sql", pwd));
    # internal reviewer report (also used in public forum posting).
    processPoints(runScript("points.sql", pwd));
    processContributions(runScript("contributions.sql", pwd));
    processTotals(runScript("totals.sql", pwd));
    processMonthly(runScript("monthly.sql", pwd));

    email = getEmailOutput(startDateStr, endDateStr, endDateMonthStr);

    print("Reviewer report\n");
    print(
      "SUBJECT: Weekly Add-on Reviews Report, v 0.12, " + endDateStr + "\n");
    print(email);
  else:
    print("Invalid password.");

  return;

def runScript(filename, password):
  script = open(filename);
  output = subprocess.check_output(
    [ "mysql", ("-h" + AMO_DB_SERVER), AMO_DB, ("-u" + AMO_DB_USER),
     ("-p" + password) ],
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

main();
