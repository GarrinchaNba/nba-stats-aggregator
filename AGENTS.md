# AGENTS.md

## Big-picture architecture
- This repo is a Python ETL/scraping pipeline for NBA data (Basketball-Reference, CTG, NBA.com, 538, Basketball Index, Spotrac) that exports CSV/JSON for SportPress/WordPress.
- Entrypoints are thin CLI scripts in `src/*/*.py`; core logic is in paired `*_processor.py` modules.
- Shared infrastructure is in `src/common/`: `constant.py` (URLs/paths), `data_collector.py` (HTTP + BeautifulSoup), `file_processor.py` (CSV/JSON writes + backups), `stub.py` (offline fixtures).
- Top100 is an orchestrated chain: `src/top100/top100.py` -> `src/top100/top100_utils.py::generate_full` -> `bbref/top100.py` -> `538/top100.py` -> `bbindex/top100.py` -> `spotrac/top100.py` -> JSON export in `data/export/`.
- Team game exports are staged: `bbref/team_calendar_processor.py` -> `sportpress/team_calendar_processor.py` -> `sportpress/team_games_processor.py`.

## Critical workflows
- Use `run.sh` first: it auto-creates `.venv`, reinstalls when `requirements.txt` hash changes, and dispatches known scripts.
- Typical commands:
```bash
./run.sh help
./run.sh top100 2023 2024 local
./run.sh bbref_team_calendar sas 2024 local
./run.sh sportpress_team_games sas 2024 local
./run.sh ctg_game_logs 2024 local
```
- `run.sh` does not expose every module; Spotrac cap/contracts and NBA.com scripts are direct entrypoints under `src/spotrac/` and `src/nbacom/`.
- There is no `tests/` directory right now; practical validation is running the relevant pipeline and checking artifacts under `data/`.

## Project-specific coding conventions
- Follow `.github/copilot-instructions.md`: typed signatures, Google-style docstrings for public APIs, explicit naming, and `pathlib.Path` for new file IO.
- Keep the existing CLI/environment pattern: positional args + optional `local|prod`, parsed through `config/config.py` (`Environment`, `get_environment`).
- Preserve stub behavior: processors commonly gate network calls through `get_is_stubbed(environment)` and use fixtures in `data/stub/`.
- Respect delimiter split: analytics exports are usually `;` (default writer), SportPress/team metadata is often `,` (explicit in processors).
- Preserve backup semantics in writers (`file_processor.backup_file`) unless intentionally changing file lifecycle behavior.

## Integrations and caveats
- Credentials come from `config/<env>.yaml` via `config/config.py` (`ctg.sessionId`, `ctg.cookieValue`, `nbacom.ocpApimSubscriptionKey`, `is_stubbed`); keep secrets out of source.
- Ranking enrichment from `src/bbref/data_processor.py::get_rankings` is reused by both BBRef and CTG game-log processors.
- Team/country normalization depends on lookup CSVs in `data/common/` via `file_processor.get_*_mapping` helpers.
- `src/nbacom/playbyplay_processor.py` is WIP (prototype extraction path, no completed output write path); do not rely on it as production-ready.

