#!/usr/bin/env python
from __future__ import print_function

import sys
import subprocess
import getpass
import re
import os
import csv
import calendar
import tempfile

from StringIO import StringIO
from datetime import date, timedelta


AMO_DB = "addons_mozilla_org"
DATE_FORMAT = "%Y-%m-%d"
JUICE = os.environ.get("JUICE", "juice")

# DB access information.
db_access = {"host": "", "user": "", "password": ""}


def main():
    if (3 == len(sys.argv)):
        if re.match("^[\w\.\-]+$", sys.argv[1]) and \
           re.match("^\w+$", sys.argv[2]):
            # get password from standard input.
            pwd = getpass.getpass()

            if (re.match("^\w+$", pwd)):
                db_access["host"] = sys.argv[1]
                db_access["user"] = sys.argv[2]
                db_access["password"] = pwd
                runReport()
            else:
                print("Invalid password.")
        else:
            print("Invalid host or username.")
    else:
        print("Usage: " + sys.argv[0] + " host username")
        print("Example:")
        print("\t" + sys.argv[0] + " db.example.com johndoe")


def runReport():
    endDate = date.today()
    startDate = endDate - timedelta(days=7)
    startDateStr = startDate.strftime(DATE_FORMAT)
    endDateStr = endDate.strftime(DATE_FORMAT)

    quarterNumber = (endDate.month - 1) / 3 + 1
    quarterEndMonth = quarterNumber * 3
    quarterStart = date(endDate.year, (quarterNumber - 1) * 3 + 1, 1)
    quarterEnd = date(endDate.year, quarterEndMonth,
                      calendar.monthrange(endDate.year, quarterEndMonth)[1])

    print(getEmailOutput(startDateStr, endDateStr, quarterStart, quarterEnd))


def runScript(filename):
    script = open(filename)

    output = subprocess.check_output([
        "mysql", ("-h" + db_access["host"]), AMO_DB,
        ("-u" + db_access["user"]), ("-p" + db_access["password"])
    ], stdin=script)

    script.close()
    # print("Output:\n" + output)
    return output


def table(headers, csvdata):
    html = ""
    html += "<table>\n"
    csvstream = StringIO(csvdata.strip())
    reader = csv.reader(csvstream, delimiter="\t", lineterminator="\n")
    html += "<tr><th>" + "</th><th>".join(headers) + "</th></tr>\n"

    for values in reader:
        html += "<tr><td>" + "</td><td>".join(values) + "</td></tr>\n"

    html += "</table>\n"
    return html


def section(name, tableheaders, filename):
    heading = "<h3>{}</h3>".format(name)
    tabledata = runScript(filename)
    return heading + table(tableheaders, tabledata)


def juiceit(html):
    with tempfile.NamedTemporaryFile() as htmlfile:
        with open(htmlfile.name, "w") as fd:
            fd.write(html)

        with tempfile.NamedTemporaryFile() as outfile:
            subprocess.check_call([JUICE, htmlfile.name, outfile.name])

            with open(outfile.name) as fd:
                output = fd.read()

    return output


def getEmailOutput(startDate, endDate, quarterStart, quarterEnd):
    html = """
      <style>
        * {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
              Helvetica, Arial, sans-serif, "Apple Color Emoji",
              "Segoe UI Emoji", "Segoe UI Symbol";
        }

        h1, h2 {
          margin: 0;
          padding: 0;
        }

        th {
          text-align: left;
          font-weight: bold;
        }

        td {
          font-weight: normal;
        }

        th, td {
          padding: 0 8px;
          white-space: nowrap;
        }

        td:not(:first-child) {
          text-align: right;
        }
      </style>
    """

    html += """
      <h1>Weekly Add-on Reviews Report</h1>
      <h2>{start} &ndash; {end}<h2>
    """.format(start=startDate, end=endDate)

    html += section(
        "Weekly Contributions, 5 Reviews or More",
        ("Name", "Staff", "Total Risk", "Average Risk", "Points",
         "Add-ons Reviewed"),
        "weekly.sql"
    )

    html += section(
        "Volunteer Contribution Ratio",
        ("Group", "Total Risk", "Average Risk", "Add-ons Reviewed"),
        "ratio.sql"
    )

    html += section(
        "Risk Profiles Reviewed",
        ("Risk Category", "All Reviewers", "Volunteers"),
        "risk.sql"
    )

    html += section(
        "Risk Profiles Reviewed",
        ("Risk Category", "All Reviewers", "Volunteers"),
        "risk.sql"
    )

    html += section(
        "Quarterly contributions ({} &ndash; {})".format(quarterStart,
                                                         quarterEnd),
        ("Name", "Points", "Add-ons Reviewed"),
        "quarterly.sql"
    )

    return juiceit(html)


if __name__ == "__main__":
    main()
