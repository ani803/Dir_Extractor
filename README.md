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

### Optional: AI-assisted verification

Low-confidence director candidates (regex/NLP score below `AI_VERIFICATION_THRESHOLD`)
can be double-checked by Claude before they're written to the output. Candidates
for one company are batched into a single request each (`AI_VERIFICATION_BATCH_SIZE`,
default 20), and every verified candidate is cached to `cache/ai_verifications.json`
so repeat/`--resume` runs never re-verify the same candidate twice.

```text
ANTHROPIC_API_KEY=sk-ant-...
AI_VERIFICATION_ENABLED=true
AI_VERIFICATION_MODEL=claude-sonnet-5
AI_VERIFICATION_THRESHOLD=75
AI_VERIFICATION_BATCH_SIZE=20
AI_VERIFICATION_MAX_RETRIES=3
AI_VERIFICATION_TIMEOUT=30
```

If the key or the `anthropic` package is missing, or a request keeps failing
after retries, the pipeline logs a warning and falls back to the heuristic
confidence scores -- it never crashes a run over this. The output workbook
gets two extra columns, `AI Verified` (Yes/No/Not checked) and `AI Reasoning`
(the one-line justification the model gave), so every verified row is
auditable.

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
