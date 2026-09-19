# GitHub Copilot Instructions — NBA Stats Aggregator

## Project Overview
Python data-aggregation project that scrapes and processes NBA statistics from multiple sources
(Basketball-Reference, NBA.com, Cleaning the Glass, Spotrac, etc.) and exports them for use
in a WordPress/SportPress site. Core stack: **Python 3.11+**, pandas, requests, BeautifulSoup,
Selenium, PyYAML, rich.

---

## General Principles

- Follow **PEP 8** for style: 4-space indentation, max 120-character line length, two blank lines
  between top-level definitions.
- Prefer **explicit over implicit**: clear variable names, no magic numbers, no unexplained booleans.
- Keep functions and methods **small and focused** — each should do exactly one thing.
- Favour **composition over inheritance**; use classes only when encapsulating state makes sense.
- Never use mutable default arguments (`def f(data=[])`); use `None` and assign inside the body.

---

## Naming Conventions

| Symbol | Convention | Example |
|--------|------------|---------|
| Module | `snake_case` | `game_logs_processor.py` |
| Class | `PascalCase` | `GameLogsProcessor` |
| Function / method | `snake_case` | `get_season_from_year()` |
| Constant | `UPPER_SNAKE_CASE` | `DEFAULT_HEADERS` |
| Private helper | leading underscore | `_parse_row()` |
| Boolean variable | `is_`, `has_`, `can_` prefix | `is_valid`, `has_data` |

---

## Type Hints

- **Always** annotate function signatures (parameters + return type).
- Use `from __future__ import annotations` at the top of the file when forward references are needed.
- Prefer built-in generic types (`list[str]`, `dict[str, int]`) over `typing.List`/`typing.Dict`
  (Python 3.9+).
- Use `X | Y` union syntax instead of `Optional[X]` / `Union[X, Y]` (Python 3.10+).

```python
# ✅ Good
def get_season_from_year(season: int, delimiter: str = "-") -> str:
    return f"{season - 1}{delimiter}{season}"

# ❌ Avoid
def get_season_from_year(season, delimiter='-'):
    return str(season - 1) + delimiter + str(season)
```

---

## Docstrings

- Use **Google-style** docstrings for all public functions, classes, and modules.
- One-liner docstrings are acceptable for trivial helpers.

```python
def get_all_seasons_between(min_year: int, max_year: int, separator: str = "_") -> list[str]:
    """Return a list of season strings between two years.

    Args:
        min_year: First season end year (inclusive).
        max_year: Last season end year (inclusive).
        separator: Character used to join the two years.

    Returns:
        List of season strings, e.g. ["2021_2022", "2022_2023"].
    """
```

---

## Error Handling

- Raise **specific, built-in exceptions** (`ValueError`, `RuntimeError`, `KeyError`) with descriptive
  messages rather than the bare `Exception`.
- Never silently swallow exceptions; at minimum log them before re-raising.
- Use `logging` (not `print`) for diagnostic output in library/module code.
- Reserve `print` / `rich.print` for top-level script output only.

```python
# ✅ Good
if len(years) < 2:
    raise ValueError(f"Invalid season string '{season}': expected 'YYYY{separator}YYYY'.")

# ❌ Avoid
raise Exception("Invalid season : " + season)
```

---

## Imports

- Group imports in this order, separated by a blank line:
  1. Standard library
  2. Third-party packages
  3. Local / project modules
- Use absolute imports; avoid relative imports (`from . import`) except inside packages.
- Never use wildcard imports (`from module import *`).

```python
# ✅ Good
import csv
import re
from datetime import date

import pandas as pd
import requests
from bs4 import BeautifulSoup

from config.config import get_config
from src.common.utils import get_season_from_year
```

---

## Functions & Classes

- Maximum **20–25 lines** per function body; extract helpers if longer.
- Avoid more than **3 positional parameters**; use a dataclass or keyword-only args beyond that.
- Prefer **pure functions** (no side effects) for data transformations.
- Use `@dataclass` or `@dataclass(frozen=True)` for plain data holders instead of verbose `__init__`.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SeasonRange:
    min_year: int
    max_year: int
    separator: str = "_"
```

---

## Data Processing (pandas)

- Chain DataFrame operations with method chaining and intermediate variable names for readability.
- Avoid iterating over rows with `for` loops; prefer vectorised operations or `DataFrame.apply`.
- Always specify `dtype` when reading CSVs where the column type matters.
- Name intermediate DataFrames descriptively (`raw_df`, `filtered_df`, `result_df`).

```python
# ✅ Good
result_df = (
    pd.read_csv(file_path, sep=";", dtype={"season": str})
    .rename(columns={"player_name": "name"})
    .dropna(subset=["name"])
    .reset_index(drop=True)
)
```

---

## Web Scraping (requests / BeautifulSoup / Selenium)

- Always set a **User-Agent** and reasonable **timeout** on every `requests.get` / `session.get` call.
- Implement **retry logic with exponential back-off** rather than a fixed `time.sleep`.
- Separate HTTP fetching from HTML parsing — keep them in distinct functions.
- Close Selenium `WebDriver` instances in a `try/finally` block or use a context manager.

```python
# ✅ Good — separate concerns
def fetch_page(url: str) -> str:
    response = get_url_response(url)
    return response.text

def parse_player_table(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    return _extract_rows(soup.find("table", id="per_game"))
```

---

## Configuration

- Load configuration **once** at startup via `config/config.py`; never hard-code paths or seasons
  inside source files.
- Use `local.yaml` for environment-specific overrides; never commit secrets.
- Access config values through typed helper functions, not raw dictionary access scattered in code.

---

## File I/O

- Always use `pathlib.Path` instead of `os.path` for file operations.
- Open files with an explicit `encoding` parameter (`encoding="utf-8"`).
- Use context managers (`with open(...) as f`) for all file reads/writes.

```python
from pathlib import Path

output_path = Path("data/bbref") / f"sas_calendar_{season}.csv"
with output_path.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
```

---

## Testing

- Place tests under a `tests/` directory mirroring `src/` structure.
- Use **pytest**; one test file per source module (`tests/common/test_utils.py`).
- Name test functions `test_<what>_<condition>_<expected>`.
- Mock external HTTP calls and file I/O; never make real network requests in unit tests.

```python
def test_get_season_from_year_default_delimiter_returns_hyphenated_string():
    assert get_season_from_year(2024) == "2023-2024"
```

---

## Code Smells to Avoid

| Smell | Remedy |
|-------|--------|
| Magic numbers (`retry < 3`) | Named constant (`MAX_RETRIES = 3`) |
| Long parameter lists | Dataclass / config object |
| Deeply nested `if` blocks | Early returns / guard clauses |
| Duplicate string literals | Module-level constant |
| `print` in library code | `logging.getLogger(__name__)` |
| `except Exception: pass` | Log and re-raise or handle specifically |
| Bare `str` concatenation for paths | `pathlib.Path` |

