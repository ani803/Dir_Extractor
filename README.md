# Director Extractor

Director Extractor reads an Excel list of companies, finds each company's website, crawls likely leadership or governance pages, extracts director names, and writes the result to an Excel file.

## Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
```

Add any search API keys you have to `.env`:

```text
GOOGLE_API_KEY=...
GOOGLE_CSE_ID=...
BING_API_KEY=...
SERPAPI_KEY=...
```

If the input workbook already has a website column, the app can use it without search API keys.

## Run

```powershell
py -3.12 src/main.py
```

Useful options:

```powershell
py -3.12 src/main.py --input input\List of NBFCs.xlsx --output output\directors.xlsx
py -3.12 src/main.py --limit 5
py -3.12 src/main.py --no-verify
```

## Input

The input workbook should include one company-name column such as `Company Name`, `Company`, `Name`, `Entity`, or `NBFC Name`.

Optional website columns include `Website`, `Website URL`, `URL`, `Official Website`, or `Company Website`.

## Output

Results are written to `output/directors.xlsx` by default, with one row per extracted director. Companies without directors are still included with their status.
