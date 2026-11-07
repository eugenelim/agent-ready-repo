# Tidy Desk

Tidy Desk cleans up spreadsheets for office teams: it removes duplicate rows, fixes date formats, and writes a clean copy next to the original. It is meant for finance and operations staff who work in Excel every day and do not write code.

## Install

```
git clone https://example.invalid/tidy-desk.git
cd tidy-desk
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Use

```
tidy run budget.xlsx --dedupe --dates iso
```

The tool prints `done`. Open the output with your spreadsheet program.

## Configure

Set `TIDY_OUT` to change where files go, then export it in your shell profile.

## Contributing

Fork the repository, create a branch, and open a pull request.
