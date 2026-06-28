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

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

## Notes

The iTunes Search API is public and does not require an API key. Apple can still rate-limit requests or change autocomplete responses, so the app includes a small delay and basic error handling.

Competition is based on `resultCount` with `limit=200`, so treat `200` as "200 or more" rather than an exact total.
