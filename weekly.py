#!/usr/bin/env python

# Run without arguments for usage help.

import sys;
from datetime import date, datetime, timedelta;
import calendar;
# from http://www.pymysql.org/
import pymysql;

DATE_FORMAT = "%Y-%m-%d";
SHORT_MONTH_FORMAT = "%b";
AMO_DB = "addons_mozilla_org";
SQL_POINTS = "\
  SELECT sum(rs.score) AS total, \
       CASE WHEN sum(rs.score) >= 3000000  THEN 9 \
            WHEN sum(rs.score) >= 1200000  THEN 8 \
            WHEN sum(rs.score) >=  300000  THEN 7 \
            WHEN sum(rs.score) >=   96000  THEN 6 \
            WHEN sum(rs.score) >=   45000  THEN 5 \
            WHEN sum(rs.score) >=   21000  THEN 4 \
            WHEN sum(rs.score) >=    8700  THEN 3 \
            WHEN sum(rs.score) >=    4320  THEN 2 \
            WHEN sum(rs.score) >=    2160  THEN 1 \
            ELSE 0 END AS level, \
       u.display_name \
    FROM reviewer_scores AS rs, users AS u \
    WHERE rs.user_id = u.id AND \
        u.id NOT IN (\
          SELECT DISTINCT(gu.user_id) FROM groups_users AS gu \
          WHERE gu.group_id IN (50000, 50066)) AND \
        u.id IN (\
          SELECT DISTINCT(gu.user_id) FROM groups_users AS gu \
          WHERE gu.group_id = 50002) \
    GROUP BY rs.user_id \
    ORDER BY total DESC;";
SQL_CONTRIBUTIONS_TOTAL ="\
  SELECT u.id, u.display_name, count(*) AS editortotal \
  FROM log_activity AS l, users AS u \
  WHERE l.action IN (21, 42, 43, 22, 23, 44, 45) AND l.user_id = u.id AND \
        l.user_id != 4757633 AND l.arguments LIKE '%%\"addons.addon\"%%' AND \
        l.created >= %s AND l.created < %s \
  GROUP BY l.user_id \
  ORDER BY editortotal DESC;";
SQL_CONTRIBUTIONS_REVIEW ="\
  SELECT l.user_id, count(*) AS editortotal \
  FROM log_activity AS l \
  WHERE l.action IN (21, 42, 43, 22) AND l.user_id != 4757633 AND \
        l.details LIKE %s AND \
        l.arguments LIKE '%%\"addons.addon\"%%' AND \
        l.created >= %s AND l.created < %s \
  GROUP BY l.user_id \
  ORDER BY editortotal DESC;";
SQL_CONTRIBUTIONS_TYPE_NOMINATION = "%\"reviewtype\": \"nominated\",%";
SQL_CONTRIBUTIONS_TYPE_UPDATE = "%\"reviewtype\": \"pending\",%";
SQL_CONTRIBUTIONS_TYPE_PRELIMINARY = "%\"reviewtype\": \"preliminary\",%";
SQL_CONTRIBUTIONS_ADMIN ="\
  SELECT l.user_id, count(*) AS editortotal \
  FROM log_activity AS l \
  WHERE l.action IN (23, 45) AND l.user_id != 4757633 AND \
        l.arguments LIKE '%%\"addons.addon\"%%' AND \
        l.created >= %s AND l.created < %s \
  GROUP BY l.user_id \
  ORDER BY editortotal DESC;";
SQL_CONTRIBUTIONS_INFO ="\
  SELECT l.user_id, count(*) AS editortotal \
  FROM log_activity AS l \
  WHERE l.action IN (44) AND l.user_id != 4757633 AND \
        l.arguments LIKE '%%\"addons.addon\"%%' AND \
        l.created >= %s AND l.created < %s \
  GROUP BY l.user_id \
  ORDER BY editortotal DESC;";
SQL_CONTRIBUTIONS_SUM = "\
  SELECT count(*) \
  FROM log_activity AS l \
  WHERE l.action IN (21, 42, 43, 22, 23, 44, 45) AND \
        l.arguments LIKE '%%\"addons.addon\"%%' AND \
        l.created >= %s AND l.created < %s;";
SQL_CONTRIBUTIONS_SUM_COMMUNITY = "\
  SELECT count(*) \
  FROM log_activity AS l \
  WHERE l.action IN (21, 42, 43, 22, 23, 44, 45) AND \
        l.arguments LIKE '%%\"addons.addon\"%%' AND \
        l.created >= %s AND l.created < %s AND \
        l.user_id NOT IN ( \
          SELECT DISTINCT(gu.user_id) FROM groups_users AS gu \
          WHERE gu.group_id IN (50000, 50066))";
SQL_CONTRIBUTIONS_SUM_AUTOMATIC = "\
  SELECT count(*) \
  FROM log_activity AS l \
  WHERE l.action IN (21, 42, 43, 22, 23, 44, 45) AND l.user_id = 4757633 AND \
        l.arguments LIKE '%%\"addons.addon\"%%' AND \
        l.created >= %s AND l.created < %s;";
SQL_MONTH_TOTAL ="\
  SET @from_date=%s;SET @to_date=%s; \
  SELECT \
    (SELECT COUNT(*) \
     FROM log_activity AS l \
     WHERE l.action IN (21, 42, 43, 22) AND l.arguments LIKE '%%\"addons.addon\"%%' AND \
       l.details LIKE '%%\"reviewtype\": \"nominated\",%%' AND \
       l.created >= @from_date AND l.created < @to_date) As 'Nominations', \
    (SELECT COUNT(*) \
     FROM log_activity AS l \
     WHERE l.action IN (21, 42, 43, 22) AND l.arguments LIKE '%%\"addons.addon\"%%' AND \
       l.details LIKE '%%\"reviewtype\": \"pending\",%%' AND \
       l.created >= @from_date AND l.created < @to_date) AS 'Updates', \
    (SELECT COUNT(*) \
     FROM log_activity AS l \
     WHERE l.action IN (21, 42, 43, 22) AND l.arguments LIKE '%%\"addons.addon\"%%' AND \
       l.details LIKE '%%\"reviewtype\": \"preliminary\",%%' AND \
       l.created >= @from_date AND l.created < @to_date) AS 'Preliminary', \
    (SELECT COUNT(*) \
     FROM log_activity AS l \
     WHERE l.action IN (23,45) AND l.arguments LIKE '%%\"addons.addon\"%%' AND \
       l.created >= @from_date AND l.created < @to_date) AS 'Super Review', \
    (SELECT COUNT(*) \
     FROM log_activity AS l \
     WHERE l.action = 44 AND l.arguments LIKE '%%\"addons.addon\"%%' AND \
       l.created >= @from_date AND l.created < @to_date) AS 'Info Request', \
    (SELECT COUNT(*) \
     FROM log_activity AS l \
     WHERE l.action IN (21, 42, 43, 22, 23, 44, 45) AND l.arguments LIKE '%%\"addons.addon\"%%' AND \
       l.created >= @from_date AND l.created < @to_date) AS 'Total';"

results = {};

def main():
  print(
    "Warning: Using a password on the command line interface can be insecure.");
  if (5 == len(sys.argv)):
    try:
      endDate = datetime.strptime(sys.argv[4], DATE_FORMAT);
    except ValueError:
      print("Invalid end date");
  elif (4 == len(sys.argv)):
    endDate = date.today();
    print("No date specified, using today: " + endDate.strftime(DATE_FORMAT));
  else:
    print("Usage: " + sys.argv[0] + " host username password [endDate]");
    print("Examples:");
    print("\t" + sys.argv[0] + " db.example.com johndoe hunter2");
    print("\t" + sys.argv[0] + " db.example.com johndoe hunter2 2014-04-27");

  if ('endDate' in locals()):
    runReports(endDate);

  return;

def runReports(endDate):
  weekDelta = timedelta(days=7);
  startDate = endDate - weekDelta;
  firstOfMonth = endDate.replace(day=1);
  firstOfNextMonth = getFirstOfNextMonth(endDate);

  startDateStr = startDate.strftime(DATE_FORMAT);
  endDateStr = endDate.strftime(DATE_FORMAT);
  endDateMonthStr = endDate.strftime(SHORT_MONTH_FORMAT);

  firstOfMonthStr = firstOfMonth.strftime(DATE_FORMAT);
  firstOfNextMonthStr = firstOfNextMonth.strftime(DATE_FORMAT);
  #print("Start: " + startDateStr);
  #print("End: " + endDateStr);
  #print("First of month: " + firstOfMonthStr);
  #print("First of next month: " + firstOfNextMonthStr);

  db = pymysql.connect(
    host = sys.argv[1], passwd = sys.argv[3], user = sys.argv[2], db = AMO_DB);

  print("Getting points data...");
  getPointsData(db);
  print("Getting contribution data...");
  getContributionData(db, startDateStr, endDateStr);
  print("Getting monthly totals data...");
  getMonthTotalData(db, firstOfMonthStr, firstOfNextMonthStr);

  db.close();

  print("Writing files...");
  emailOutput = getEmailOutput(startDateStr, endDateStr, endDateMonthStr);
  print(emailOutput);

  print("All done!");

  return;

def getFirstOfNextMonth(date):
  dayDelta = timedelta(days=1);
  daysInMonth = calendar.monthrange(date.year, date.month)[1];
  lastOfMonth = date.replace(day=daysInMonth);
  firstOfNextMonth = lastOfMonth + dayDelta;

  return firstOfNextMonth;

def getPointsData(db):
  cursor = db.cursor();
  cursor.execute(SQL_POINTS);
  results["points"] = cursor.fetchall();
  cursor.close();
  #print(results["points"]);

  return;

def getContributionData(db, startDateStr, endDateStr):
  cursor = db.cursor();
  cursor.execute(SQL_CONTRIBUTIONS_TOTAL, (startDateStr, endDateStr));
  results["contribTotal"] = cursor.fetchall();
  cursor.close();
  #print(results["contribTotal"]);

  cursor = db.cursor();
  cursor.execute(
    SQL_CONTRIBUTIONS_REVIEW,
    (SQL_CONTRIBUTIONS_TYPE_NOMINATION, startDateStr, endDateStr));
  results["contribNominations"] = cursor.fetchall();
  cursor.close();
  #print(results["contribNominations"]);

  cursor = db.cursor();
  cursor.execute(
    SQL_CONTRIBUTIONS_REVIEW,
    (SQL_CONTRIBUTIONS_TYPE_UPDATE, startDateStr, endDateStr));
  results["contribUpdates"] = cursor.fetchall();
  cursor.close();
  #print(results["contribUpdates"]);

  cursor = db.cursor();
  cursor.execute(
    SQL_CONTRIBUTIONS_REVIEW,
    (SQL_CONTRIBUTIONS_TYPE_PRELIMINARY, startDateStr, endDateStr));
  results["contribPreliminary"] = cursor.fetchall();
  cursor.close();
  #print(results["contribPreliminary"]);

  cursor = db.cursor();
  cursor.execute(SQL_CONTRIBUTIONS_ADMIN, (startDateStr, endDateStr));
  results["contribAdmin"] = cursor.fetchall();
  cursor.close();
  #print(results["contribAdmin"]);

  cursor = db.cursor();
  cursor.execute(SQL_CONTRIBUTIONS_INFO, (startDateStr, endDateStr));
  results["contribInfo"] = cursor.fetchall();
  cursor.close();
  #print(results["contribInfo"]);

  cursor = db.cursor();
  cursor.execute(SQL_CONTRIBUTIONS_SUM, (startDateStr, endDateStr));
  results["contribSum"] = cursor.fetchone()[0];
  cursor.close();
  #print(results["contribSum"]);

  cursor = db.cursor();
  cursor.execute(SQL_CONTRIBUTIONS_SUM_COMMUNITY, (startDateStr, endDateStr));
  results["contribSumCommunity"] = cursor.fetchone()[0];
  cursor.close();
  #print(results["contribSumCommunity"]);

  cursor = db.cursor();
  cursor.execute(SQL_CONTRIBUTIONS_SUM_AUTOMATIC, (startDateStr, endDateStr));
  results["contribSumAutomatic"] = cursor.fetchone()[0];
  cursor.close();
  #print(results["contribSumAutomatic"]);

  return;

def getMonthTotalData(db, firstOfMonthStr, firstOfNextMonthStr):
  cursor = db.cursor();
  cursor.execute(SQL_MONTH_TOTAL, (firstOfMonthStr, firstOfNextMonthStr));
  # There are 2 SET operations that return empty sets.
  cursor.nextset();
  cursor.nextset();
  results["monthTotal"] = cursor.fetchone();
  cursor.close();
  print(results["monthTotal"]);

  return;

def getEmailOutput(startDateStr, endDateStr, endDateMonthStr):
  output = "WEEKLY ADD-ON REVIEWS REPORT\n";
  output += startDateStr + " - " + endDateStr + "\n";
  output += getDoubleTextLine() + "\n";
  output += "SCORES AND LEVELS (level 1 and above):\n"
  output += getTextLine() + "\n";
  output += "Total    Level   Name\n";

  for pointEntry in results["points"]:
    level = pointEntry[1];

    if (0 < level):
      output += str(pointEntry[0]).rjust(7) + str(pointEntry[1]).rjust(7);
      output += "   " + pointEntry[2] + "\n";
    else:
      break;

  output += "\nSee also: https://addons.mozilla.org/editors/leaderboard/\n\n";
  output += "CONTRIBUTIONS (5 reviews or more):\n"
  output += getTextLine() + "\n";
  output += "Total   Nom   Upd   Pre   Sup   Inf   Name\n";

  merged = getMergedContributionData();

  for contribEntry in merged:
    total = contribEntry[2];

    if (5 <= total):
      output += str(total).rjust(5) + str(contribEntry[3]).rjust(6);
      output += str(contribEntry[4]).rjust(6) + str(contribEntry[5]).rjust(6);
      output += str(contribEntry[6]).rjust(6) + str(contribEntry[7]).rjust(6);
      output += "   " + contribEntry[1] + "\n";
    else:
      break;

  output += "\n* - Non-volunteers\n\n";

  output += "Nom - Nominations, approved or denied.\n";
  output += "Upd - Updates, approved or denied.\n";
  output += "Sup - Updates and nominations escalated to super-review\n";
  output += "Inf - Information requests to authors for updates and nominations\n";
  output += "\nVolunteer contribution ratio:\n";

  output += "\nTotal reviews: " + str(results["contribSum"]);
  output += "\nVolunteer reviews: " + str(results["contribSumCommunity"]);
  output += " (" + str(rate(results["contribSumCommunity"], results["contribSum"])) + "%)";
  output += "\nAutomatic reviews: " + str(results["contribSumAutomatic"]);
  output += " (" + str(rate(results["contribSumAutomatic"], results["contribSum"])) + "%)";

  output += "\n\nTotal contributions:\n\n";
  output += "     Nominations    Updates    Prelim.  Admin flag   Info req  Total\n";
  output += endDateMonthStr.ljust(5) + str(monthlyRateStr(0)).rjust(11);
  output += str(monthlyRateStr(1)).rjust(11) + str(monthlyRateStr(2)).rjust(11);
  output += str(monthlyRateStr(3)).rjust(12) + str(monthlyRateStr(4)).rjust(11);
  output += str(results["monthTotal"][5]).rjust(7);

  return output;

def getMergedContributionData():
  merged = [];
  resultSets = [ "contribNominations", "contribUpdates", "contribPreliminary",
                 "contribAdmin", "contribInfo" ];

  for contribEntry in results["contribTotal"]:
    merged.append([contribEntry[0], contribEntry[1], contribEntry[2],
                   0, 0, 0, 0, 0]);

  for i in range(5):
    resultSet = resultSets[i];

    for contribEntry in results[resultSet]:
      id = contribEntry[0];

      for mergedEntry in merged:
        if (id == mergedEntry[0]):
          mergedEntry[i + 3] = contribEntry[1];
          break;

  #print(merged);

  return merged;

def getTextLine():
  return "----------------------------------------------------------\n";

def getDoubleTextLine():
  return "==========================================================\n";

def rate(part, total):
  return int(round((float(part) / float(total)) * 100));

def monthlyRateStr(index):
  monthItem = results["monthTotal"][index];
  rateStr = str(monthItem) + " (";
  rateStr += str(rate(monthItem, results["monthTotal"][5])) + "%)";

  return rateStr;

main();
