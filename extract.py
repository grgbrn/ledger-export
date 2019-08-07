import csv
import dataclasses
import datetime
import enum
import os
import subprocess

from typing import Callable, Dict, Iterator, List, Optional, Set, Tuple

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
        "all currencies used in this report"
        return list(self.data.keys())

    def get_categories(self) -> List[str]:
        "all categories for all currencies in this report"
        all_categories: Set[str] = set()
        for currency, dat in self.data.items():
            all_categories.update(dat.keys())
        return list(all_categories)

    def categories_for(self, currency: Currency) -> List[str]:
        "get all categories used in a specific currency"
        return list(self.data_for(currency).keys())

    def data_for(self, currency: Currency) -> Dict[str,str]:
        "get category->amount map for a specific currency"
        return self.data.get(currency, dict())


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
    #print(">> ", ' '.join(cmd))

    proc = subprocess.run(cmd, capture_output=True)
    proc.check_returncode()

    report = MonthlyReport(year, month)

    for k,v in parse_ledger_output(proc.stdout):
        report.add(k,v)

    return report

def find_split_index(lines: List[str]) -> int:
    for line in lines:
        ix = line.find("Expenses")
        if ix != -1:
            return ix
    assert False, "can't figure out how to split output"

def parse_ledger_output(output: bytes) -> List[Tuple[str, str]]:
    s = output.decode('utf-8')

    result: List[Tuple[str, str]] = []

    # split lines and filter whitespace
    lines = [l for l in s.split(os.linesep) if len(l.strip()) > 0]

    # find where to split the lines - ledger output is
    # carefully indented
    assert len(lines) > 0
    split_index = find_split_index(lines)

    # process these backwards to make it easier to handle
    # omitted categories, but build up the result list
    # in the original order
    last_category: Optional[str] = None
    for line in reversed(lines):
        currency = line[0:split_index].strip()
        category = line[split_index:].strip()

        if category == "":
            assert last_category is not None, f"Can't determine category for amount:{currency}"
            category = last_category
        else:
            last_category = category

        result.insert(0, (category, currency))

    return result

def make_report_name(reports: List[MonthlyReport]) -> str:
    start = reports[0]
    end = reports[-1]
    return "report-{:d}{:02d}_{:d}{:02d}".format(start.year, start.month, end.year, end.month)

def get_csv_formatter(c: Currency) -> Optional[Callable[[str], str]]:
    """
    Returns an optional formatting function used to convert values from
    ledger format into something understood by the external spreadsheet
    """
    if c == Currency.EUR:
        def eur_format(s: str) -> str:
            if len(s) == 0:
                return ""
            assert s.endswith(' EUR'), f"Unexpected EUR value:{s}"
            # "€"
            return f"€{s[:-4]}"
        return eur_format
    else:
        return None

def main(start_year: int, start_month: int):

    reports = [ledger_monthly(year, month) for year, month
               in until_now(start_year,start_month)]

    # find complete set of currencies in all reports, so we
    # can generate one csv file per currency
    all_currencies: Set[Currency] = set()
    for report in reports:
        all_currencies.update(report.get_currencies())

    report_basename = make_report_name(reports)

    for currency in all_currencies:
        print(currency.name)

        ledger_dicts = [report.data_for(currency) for report in reports]
        all_categories: Set[str] = set()
        for report in reports:
            all_categories.update(report.categories_for(currency))

        value_formatter = get_csv_formatter(currency)

        report_filename = f"{report_basename}-{currency.name}.csv"
        print(f"generating {report_filename}")

        with open(report_filename, 'w', newline='') as f:
            csvfile = csv.writer(f, quoting=csv.QUOTE_MINIMAL)

            # now use master category list to generate sparse csv
            # header row containing date column labels
            header = ['Category']
            header.extend(["{:d}/{:02d}".format(r.year, r.month) for r in reports])
            csvfile.writerow(header)

            # then a row for each category, values for each monthly report
            for cat in sorted(all_categories):
                vals = [dat.get(cat, '') for dat in ledger_dicts]
                if value_formatter:
                    vals = [value_formatter(v) for v in vals]

                row = [cat]
                row.extend(vals)
                csvfile.writerow(row)

def test():
    ledger_monthly(2019, 5)

if __name__=='__main__':
    main(2018, 5)
    #test()
