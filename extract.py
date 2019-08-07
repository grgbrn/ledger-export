import csv
import dataclasses
import datetime
import enum
import os
import subprocess

from typing import Dict, Tuple, Iterator, List, Set, Optional

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

class Currency(enum.Enum):
    USD = 1
    EUR = 2

def guess_currency(s: str) -> Optional[Currency]:
    if s.startswith("$"):
        return Currency.USD
    elif s.endswith(" EUR"):
        return Currency.EUR
    else:
        return None

@dataclasses.dataclass
class MonthlyReport:
    year: int
    month: int

    # store category->balance amounts per-currency
    data: Dict[Currency, Dict[str,str]] = dataclasses.field(default_factory=dict)

    def add(self, category:str, amount:str):
        "add a (category,amount) pair into the correct currency dict"
        c = guess_currency(amount)
        if c is None:
            assert False, "unknown currency:" + amount

        d = self.data.get(c, None)
        if d is None:
            d = {}
            self.data[c] = d
        d[category] = amount

    def get_currencies(self) -> List[Currency]:
        return list(self.data.keys())

    def get_all_categories(self) -> List[str]:
        "return all categories for all currencies"
        all_categories: Set[str] = set()
        for currency, dat in self.data.items():
            all_categories.update(dat.keys())
        return list(all_categories)


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
    print(">> ", ' '.join(cmd))

    proc = subprocess.run(cmd, capture_output=True)
    proc.check_returncode()

    report = MonthlyReport(year, month)

    # XXX mypy can't catch a missing '.items()' here
    # XXX it should theoretically check that this unpacking
    # XXX is legitimate
    for k,v in parse_ledger_output(proc.stdout).items():
        report.add(k,v)

    return report

def find_split_index(lines: List[str]) -> int:
    for line in lines:
        ix = line.find("Expenses")
        if ix != -1:
            return ix
    assert False, "can't figure out how to split output"

def parse_ledger_output(output: bytes) -> Dict[str, str]:
    "XXX need to decide exactly what this returns now"
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

        # XXX this would (and should) cause a collision except i'm parsing it wrong
        assert category not in dat
        dat[category] = currency

    return dat

def main(start_year: int, start_month: int):

    reports = [ledger_monthly(year, month)
        for year, month in until_now(start_year,start_month)]

    # find the complete set of categories & currencies
    # across all months
    all_categories: Set[str] = set()
    all_currencies: Set[Currency] = set()

    for report in reports:
        all_categories.update(report.get_all_categories())
        all_currencies.update(report.get_currencies())

    print("=" * 60)
    print(all_currencies)
    print(sorted(all_categories))
    print("=" * 60)

    # XXX this sort of works but needs to be cleaned up
    # XXX definitely needs per-currency categories
    for currency in all_currencies:
        print(currency)

        ledger_dicts = [report.data[currency] for report in reports]

        # now use master category list to generate sparse csv
        # header row containing date column labels
        header = ['Category']
        header.extend(["{:d}/{:02d}".format(r.year, r.month) for r in reports])
        print(header)

        # then a row for each category, values for each monthly report
        for cat in sorted(all_categories):
            row = [cat]
            row.extend([dat.get(cat, '') for dat in ledger_dicts])
            print(row)

def test():
    ledger_monthly(2019, 5)

if __name__=='__main__':
    main(2018, 5)
    #test()
