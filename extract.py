import csv
import datetime
import os
import subprocess
from dataclasses import dataclass
from typing import Dict, Tuple, Iterator, List, Set

def until_now(year: int, month: int) -> Iterator[Tuple[int, int]]:
    "returns (year,month) tuples from starting point until now (inclusive)"
    now = datetime.datetime.now()
    end_tuple = (now.year, now.month)

    for val in dateiter(year, month):
        yield val
        if val == end_tuple:
            return

def dateiter(year: int, month: int) -> Iterator[Tuple[int,int]]:
    "return successive (year,month) tuples, inclusive of passed year,month"
    while True:
        yield (year, month)
        month += 1
        if month > 12:
            month = 1
            year += 1

@dataclass
class MonthlyReport:
    year: int
    month: int
    data: Dict[str,str]

def ledger_monthly(year: int, month: int) -> MonthlyReport:
    "call ledger to get category balance for a given month"
    # confirm that '-e' does what i think!

    # no easy way to add a month using just datetime?
    # add 32 days and just use that to get the year+month
    # values
    start = datetime.date(year=year, month=month, day=1)
    end = start + datetime.timedelta(days=32)

    start_str = "{:d}/{:02d}/01".format(start.year, start.month)
    end_str = "{:d}/{:02d}/01".format(end.year, end.month)

    cmd = ["ledger", "bal", "-s", "-b", start_str, "-e", end_str, "--flat", "--no-total", "Expenses"]
    # print(cmd)

    proc = subprocess.run(cmd, capture_output=True)
    proc.check_returncode()

    dat = parse_ledger_output(proc.stdout)

    return MonthlyReport(year, month, dat)

def find_split_index(lines: List[str]) -> int:
    for line in lines:
        ix = line.find("Expenses")
        if ix != -1:
            return ix
    assert False, "can't figure out how to split output"

def parse_ledger_output(output: bytes) -> Dict[str, str]:
    "return a dict "
    s = output.decode('utf-8')

    dat: Dict[str,str] = {}
    lines = s.split(os.linesep)

    # find where to split the lines - ledger output is
    # carefully indented
    assert len(lines) > 0
    split_index = find_split_index(lines)

    for line in s.split(os.linesep):
        currency = line[0:split_index].strip()
        category = line[split_index:].strip()

        if category == "":
            if currency != "":
                print(f"skipping unknown spending of amount:{currency}")
            continue

        # XXX this can cause a collision if there are two currency types?!?!
        dat[category] = currency

    return dat

if __name__=='__main__':
    start = (2019, 5)

    ledger_dicts = [ledger_monthly(year, month)
        for year, month in until_now(2018,5)]

    # find the complete set of categories listed
    # across all months
    all_categories: Set[str] = set()

    for report in ledger_dicts:
        all_categories.update(report.data.keys())
    #print(sorted(all_categories))

    # now use master category list to generate sparse csv
    # header row containing date column labels
    header = ['Category']
    header.extend(["{:d}/{:02d}".format(r.year, r.month) for r in ledger_dicts])
    print(header)

    # then a row for each category, values for each monthly report
    for cat in sorted(all_categories):
        row = [cat]
        row.extend([r.data.get(cat, '') for r in ledger_dicts])
        print(row)
