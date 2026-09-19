# Testing Guidelines

- Use `pytest` for all new tests in this repository.
- Structure each test with explicit **Given / When / Then** sections, using short comments when that improves readability.
- Name test functions in snake case with the format `test_should_<expected_result>_when_<condition>`.
- Keep one behavior per test; split scenarios instead of branching inside a single test.
- Prefer deterministic tests: patch randomness, sleeps, backups, current time, and network calls when they are not the subject of the test.
- Never perform real network requests in tests; use `data/stub/`, existing generated files under `data/`, or local temporary files.
- Use `tmp_path` for writable outputs and compare against known-good CSV/JSON samples when possible.
- Use `monkeypatch` or fixtures to isolate environment variables, `sys.argv`, filesystem paths, and imported collaborators.
- Assert observable outcomes first: generated files, parsed rows, CLI exit codes, and downstream function calls.
- Prefer small reusable helpers in `tests/conftest.py` over repeating setup in each test module.
- Mirror the production structure under `tests/` when adding coverage for a new module or script.
- Keep fixture data minimal unless the real files in `data/` are the behavior being validated.

