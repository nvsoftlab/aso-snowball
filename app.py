"""
App Store ASO Snowball Tool

How to run:
1. pip install streamlit pandas requests
2. streamlit run app.py
"""

from __future__ import annotations

import plistlib
import string
import time
from typing import Any

import pandas as pd
import requests
import streamlit as st


HINTS_URL = "https://search.itunes.apple.com/WebObjects/MZSearchHints.woa/wa/hints"
SEARCH_URL = "https://itunes.apple.com/search"
DELAY_SECONDS = 0.5
TIMEOUT_SECONDS = 10
LATIN_ALPHABET = list(string.ascii_lowercase)
UKRAINIAN_CYRILLIC_ALPHABET = list("абвгґдеєжзиіїйклмнопрстуфхцчшщьюя")
RUSSIAN_CYRILLIC_ALPHABET = list("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
SNOWBALL_ALPHABET_MODES = [
    "Auto (detect from seed)",
    "Latin a-z",
    "Ukrainian Cyrillic",
    "Russian Cyrillic",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.0 Safari/605.1.15"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
}

LOCALES = [
    {"label": "United States - English", "country": "us", "language": "en-US", "storefront": "143441"},
    {"label": "United Kingdom - English", "country": "gb", "language": "en-GB", "storefront": "143444"},
    {"label": "Canada - English", "country": "ca", "language": "en-CA", "storefront": "143455"},
    {"label": "Australia - English", "country": "au", "language": "en-AU", "storefront": "143460"},
    {"label": "Croatia - Croatian", "country": "hr", "language": "hr-HR", "storefront": "143494"},
    {"label": "Czechia - Czech", "country": "cz", "language": "cs-CZ", "storefront": "143489"},
    {"label": "Denmark - Danish", "country": "dk", "language": "da-DK", "storefront": "143458"},
    {"label": "Germany - German", "country": "de", "language": "de-DE", "storefront": "143443"},
    {"label": "France - French", "country": "fr", "language": "fr-FR", "storefront": "143442"},
    {"label": "Canada - French", "country": "ca", "language": "fr-CA", "storefront": "143455"},
    {"label": "Spain - Spanish", "country": "es", "language": "es-ES", "storefront": "143454"},
    {"label": "Italy - Italian", "country": "it", "language": "it-IT", "storefront": "143450"},
    {"label": "Greece - Greek", "country": "gr", "language": "el-GR", "storefront": "143448"},
    {"label": "Hungary - Hungarian", "country": "hu", "language": "hu-HU", "storefront": "143482"},
    {"label": "Indonesia - Indonesian", "country": "id", "language": "id-ID", "storefront": "143476"},
    {"label": "Norway - Norwegian", "country": "no", "language": "no-NO", "storefront": "143457"},
    {"label": "Poland - Polish", "country": "pl", "language": "pl-PL", "storefront": "143478"},
    {"label": "Portugal - Portuguese", "country": "pt", "language": "pt-PT", "storefront": "143453"},
    {"label": "Romania - Romanian", "country": "ro", "language": "ro-RO", "storefront": "143487"},
    {"label": "Russia - Russian", "country": "ru", "language": "ru-RU", "storefront": "143469"},
    {"label": "Slovakia - Slovak", "country": "sk", "language": "sk-SK", "storefront": "143496"},
    {"label": "Ukraine - Ukrainian", "country": "ua", "language": "uk-UA", "storefront": "143492"},
    {"label": "Netherlands - Dutch", "country": "nl", "language": "nl-NL", "storefront": "143452"},
    {"label": "Brazil - Portuguese", "country": "br", "language": "pt-BR", "storefront": "143503"},
    {"label": "Mexico - Spanish", "country": "mx", "language": "es-MX", "storefront": "143468"},
    {"label": "Sweden - Swedish", "country": "se", "language": "sv-SE", "storefront": "143456"},
    {"label": "Turkey - Turkish", "country": "tr", "language": "tr-TR", "storefront": "143480"},
    {"label": "Japan - Japanese", "country": "jp", "language": "ja-JP", "storefront": "143462"},
    {"label": "Korea - Korean", "country": "kr", "language": "ko-KR", "storefront": "143466"},
]


def build_headers(locale: dict[str, str]) -> dict[str, str]:
    language = locale["language"]
    language_root = language.split("-")[0]
    headers = HEADERS.copy()
    headers["Accept-Language"] = f"{language},{language_root};q=0.9,en;q=0.7"
    headers["X-Apple-Store-Front"] = f"{locale['storefront']}-1,29"
    return headers


def contains_cyrillic(text: str) -> bool:
    return any("\u0400" <= character <= "\u04ff" for character in text)


def get_snowball_alphabet(
    seed_keyword: str,
    alphabet_mode: str,
    locale: dict[str, str],
) -> tuple[list[str], str]:
    if alphabet_mode == "Latin a-z":
        return LATIN_ALPHABET, "Latin a-z"
    if alphabet_mode == "Ukrainian Cyrillic":
        return UKRAINIAN_CYRILLIC_ALPHABET, "Ukrainian Cyrillic"
    if alphabet_mode == "Russian Cyrillic":
        return RUSSIAN_CYRILLIC_ALPHABET, "Russian Cyrillic"

    if contains_cyrillic(seed_keyword):
        if locale["language"].startswith("ru"):
            return RUSSIAN_CYRILLIC_ALPHABET, "Russian Cyrillic (auto)"
        return UKRAINIAN_CYRILLIC_ALPHABET, "Ukrainian Cyrillic (auto)"
    return LATIN_ALPHABET, "Latin a-z (auto)"


def extract_hint_terms(payload: Any) -> list[str]:
    """Extract string terms from Apple's JSON or plist hints payload."""
    if isinstance(payload, dict):
        items = payload.get("hints", [])
    elif isinstance(payload, list):
        items = payload
    else:
        return []

    terms: list[str] = []
    for item in items:
        if isinstance(item, str):
            term = item
        elif isinstance(item, dict):
            term = (
                item.get("term")
                or item.get("displayTerm")
                or item.get("searchTerm")
                or item.get("name")
            )
        else:
            term = None

        if isinstance(term, str) and term.strip():
            terms.append(term.strip())

    return terms


def fetch_suggestions(keyword: str, locale: dict[str, str]) -> tuple[list[str], str | None]:
    params = {
        "clientApplication": "Software",
        "term": keyword,
        "cc": locale["country"],
        "l": locale["language"],
    }

    try:
        response = requests.get(
            HINTS_URL,
            params=params,
            headers=build_headers(locale),
            timeout=TIMEOUT_SECONDS,
        )
        if response.status_code == 403:
            return [], f"403 Forbidden while fetching suggestions for '{keyword}'."

        response.raise_for_status()

        try:
            payload = response.json()
        except ValueError:
            payload = plistlib.loads(response.content)

        return extract_hint_terms(payload), None

    except requests.Timeout:
        return [], f"Timeout while fetching suggestions for '{keyword}'."
    except requests.RequestException as exc:
        return [], f"Network error while fetching suggestions for '{keyword}': {exc}"
    except (ValueError, plistlib.InvalidFileException) as exc:
        return [], f"Invalid hints response for '{keyword}': {exc}"


def check_competition(keyword: str, locale: dict[str, str]) -> tuple[int | None, str | None]:
    params = {
        "term": keyword,
        "country": locale["country"],
        "entity": "software",
        "limit": 200,
    }

    try:
        response = requests.get(
            SEARCH_URL,
            params=params,
            headers=build_headers(locale),
            timeout=TIMEOUT_SECONDS,
        )
        if response.status_code == 403:
            return None, f"403 Forbidden while checking competition for '{keyword}'."

        response.raise_for_status()
        result_count = response.json().get("resultCount")

        if isinstance(result_count, int):
            return result_count, None
        return None, f"Missing resultCount while checking competition for '{keyword}'."

    except requests.Timeout:
        return None, f"Timeout while checking competition for '{keyword}'."
    except requests.RequestException as exc:
        return None, f"Network error while checking competition for '{keyword}': {exc}"
    except ValueError:
        return None, f"Invalid JSON while checking competition for '{keyword}'."


def build_keyword_list(
    seed_keyword: str,
    enable_snowball: bool,
    alphabet_mode: str,
    locale: dict[str, str],
    status,
) -> tuple[list[str], list[str]]:
    keywords = {seed_keyword}
    errors: list[str] = []

    if not enable_snowball:
        status.info(
            f"Snowball disabled. Checking exact keyword only: {seed_keyword} "
            f"({locale['label']})"
        )
        return sorted(keywords), errors

    alphabet, alphabet_label = get_snowball_alphabet(seed_keyword, alphabet_mode, locale)
    status.info(f"Using snowball alphabet: {alphabet_label}")
    time.sleep(DELAY_SECONDS)

    search_terms = [seed_keyword] + [f"{seed_keyword} {letter}" for letter in alphabet]

    for index, term in enumerate(search_terms):
        if index == 0:
            status.info(f"Fetching suggestions for: {term}")
        else:
            letter = term.rsplit(" ", maxsplit=1)[-1]
            status.info(f"Fetching suggestions for letter: {letter.upper()} ({term})")

        suggestions, error = fetch_suggestions(term, locale)
        keywords.update(suggestions)
        if error:
            errors.append(error)
        time.sleep(DELAY_SECONDS)

    return sorted(keywords), errors


def collect_competition_data(
    keywords: list[str],
    locale: dict[str, str],
    status,
    progress,
) -> tuple[pd.DataFrame, list[str]]:
    rows: list[dict[str, int | str]] = []
    errors: list[str] = []

    for index, keyword in enumerate(keywords, start=1):
        status.info(f"Checking competition {index}/{len(keywords)}: {keyword} ({locale['label']})")
        result_count, error = check_competition(keyword, locale)

        if result_count is not None:
            rows.append({"Keyword": keyword, "Competitors (resultCount)": result_count})
        if error:
            errors.append(error)

        progress.progress(index / len(keywords))
        time.sleep(DELAY_SECONDS)

    dataframe = pd.DataFrame(rows, columns=["Keyword", "Competitors (resultCount)"])
    if not dataframe.empty:
        dataframe = dataframe.sort_values("Competitors (resultCount)", ascending=True)
        dataframe = dataframe.reset_index(drop=True)

    return dataframe, errors


def get_selected_keywords(table_event: dict[str, Any], dataframe: pd.DataFrame) -> list[str]:
    selection = table_event.get("selection", {})
    selected_rows = selection.get("rows", [])
    selected_cells = selection.get("cells", [])

    keywords: list[str] = []

    for row_index in selected_rows:
        if 0 <= row_index < len(dataframe):
            keywords.append(str(dataframe.iloc[row_index]["Keyword"]))

    for row_index, column_name in selected_cells:
        if column_name == "Keyword" and 0 <= row_index < len(dataframe):
            keywords.append(str(dataframe.iloc[row_index]["Keyword"]))

    return list(dict.fromkeys(keywords))


def render_results(dataframe: pd.DataFrame, locale_label: str | None = None) -> None:
    if locale_label:
        st.caption(f"Last search locale: {locale_label}")

    table_event = st.dataframe(
        dataframe,
        width="stretch",
        hide_index=True,
        key="keyword_results_table",
        on_select="rerun",
        selection_mode=["multi-row", "multi-cell"],
    )

    selected_keywords = get_selected_keywords(table_event, dataframe)
    comma_separated_keywords = ", ".join(selected_keywords)

    st.text_area(
        "Selected keywords, comma-separated",
        value=comma_separated_keywords,
        height=90,
        placeholder="Select rows or Keyword cells in the table to generate a comma-separated list.",
    )


def main() -> None:
    st.set_page_config(page_title="App Store ASO Snowball Tool", layout="wide")
    st.title("App Store ASO Snowball Tool")

    if "results_dataframe" not in st.session_state:
        st.session_state.results_dataframe = pd.DataFrame()
    if "request_errors" not in st.session_state:
        st.session_state.request_errors = []
    if "results_locale_label" not in st.session_state:
        st.session_state.results_locale_label = ""

    with st.sidebar:
        seed_keyword = st.text_input(
            "Enter Seed Keyword",
            value="truth or dare",
            placeholder="alias, party game",
        )
        selected_locale = st.selectbox(
            "App Store Locale",
            LOCALES,
            index=0,
            format_func=lambda locale: locale["label"],
        )
        enable_snowball = st.checkbox("Enable Snowball (a-z loop)", value=True)
        alphabet_mode = st.selectbox(
            "Snowball Alphabet",
            SNOWBALL_ALPHABET_MODES,
            index=0,
            disabled=not enable_snowball,
        )
        start_search = st.button("Start Search", type="primary")

    status = st.empty()
    progress_slot = st.empty()

    if not start_search:
        if st.session_state.results_dataframe.empty:
            st.info("Enter a seed keyword and click Start Search.")
        else:
            render_results(
                st.session_state.results_dataframe,
                st.session_state.results_locale_label,
            )
        return

    seed_keyword = seed_keyword.strip()
    if not seed_keyword:
        st.warning("Please enter a seed keyword before starting the search.")
        return

    with st.spinner("Running App Store keyword research..."):
        progress = progress_slot.progress(0)
        keywords, suggestion_errors = build_keyword_list(
            seed_keyword,
            enable_snowball,
            alphabet_mode,
            selected_locale,
            status,
        )

        status.success(f"Found {len(keywords)} unique keywords. Checking competition...")
        dataframe, competition_errors = collect_competition_data(
            keywords,
            selected_locale,
            status,
            progress,
        )

    status.success("Search complete.")
    st.session_state.results_dataframe = dataframe
    st.session_state.request_errors = suggestion_errors + competition_errors
    st.session_state.results_locale_label = selected_locale["label"]

    if dataframe.empty:
        st.warning("No competition data was collected.")
    else:
        render_results(dataframe, selected_locale["label"])

    errors = st.session_state.request_errors
    if errors:
        with st.expander(f"Warnings and skipped requests ({len(errors)})"):
            for error in errors:
                st.warning(error)


if __name__ == "__main__":
    main()
