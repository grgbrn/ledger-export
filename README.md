# ledger-export

ledger-export exports monthly expense data from [ledger-cli](https://www.ledger-cli.org/) into a CSV format suitable for Google Sheets (and probably other spreadsheets too).
Separates expenses by currency, and generates one CSV per currency.

## Getting Started

It's assumed that you're a ledger user and have a working copy of ledger on your machine, with a valid LEDGER_FILE set

### Prerequisites

- Python 3.7+
- A recent copy of ledger-cli

### Running

The **extract.py** script is pretty self-contained, just copy it to wherever you want. 

Give it the starting month, and it will generate monthly summary data until present 

```
python3 ledger-cli 2018 5
```

TODO: actually put an example here of what the output looks like when imported into google sheets

### Development

***ledger-cli*** uses python type annotations, so benefits greatly from using [mypy](http://mypy-lang.org/) as a linter

### Running the tests

This was a one-off for personal use, so not a lot of tests :(

```
python3 extract_test.py
```

Pay attention to the mypy output and you won't need so many tests.


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

