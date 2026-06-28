# App Store ASO Snowball Tool

Local Streamlit MVP for finding long-tail, lower-competition iOS App Store keywords.

## What it does

- Fetches Apple App Store autocomplete suggestions with the snowball method.
- Expands a seed keyword by appending letters from a selected alphabet.
- Supports multiple App Store locales.
- Checks competition through the iTunes Search API `resultCount`.
- Sorts keywords by lowest competition first.
- Lets you select table rows and copy selected keywords as a comma-separated list.

## Run locally

### Prerequisites

Make sure you have:

- Python 3.10 or newer
- `pip`
- Internet access, because the app calls Apple endpoints directly
- A terminal app, such as Terminal or iTerm on macOS

Check your Python version:

```bash
python3 --version
```

If the command prints Python 3.10+, you are good to go.

### Install

Clone the repository:

```bash
git clone https://github.com/nvsoftlab/aso-snowball.git
cd aso-snowball
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Start the app

```bash
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

## Notes

The iTunes Search API is public and does not require an API key. Apple can still rate-limit requests or change autocomplete responses, so the app includes a small delay and basic error handling.

Competition is based on `resultCount` with `limit=200`, so treat `200` as "200 or more" rather than an exact total.
