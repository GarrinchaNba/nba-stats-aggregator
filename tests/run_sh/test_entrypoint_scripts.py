from __future__ import annotations

import importlib
from typing import Any

import pytest

from config.config import Environment
from tests.conftest import PROJECT_ROOT, run_cli_script

VALID_ENTRYPOINT_CASES = [
    (
        "src/top100/top100.py",
        "top100_utils",
        "generate_full",
        ["2023", "2024", "prod"],
        ("2023", "2024", Environment.PROD),
    ),
    (
        "src/bbref/top100.py",
        "src.bbref.top100_processor",
        "generate_top100",
        ["2023", "2024", "prod"],
        ("2023", "2024", Environment.PROD),
    ),
    (
        "src/bbindex/top100.py",
        "src.bbindex.top100_processor_v2",
        "generate_top100_v2",
        ["2023", "2024", "prod"],
        ("2023", "2024", Environment.PROD),
    ),
    (
        "src/bbref/players.py",
        "src.bbref.players_processor",
        "generate_players",
        ["2024", "prod"],
        ("2024", Environment.PROD),
    ),
    (
        "src/bbref/game_logs.py",
        "src.bbref.game_logs_processor",
        "generate_game_logs",
        ["2023", "2024", "prod"],
        ("2023", "2024", Environment.PROD),
    ),
    (
        "src/bbref/team_calendar.py",
        "src.bbref.team_calendar_processor",
        "generate_calendars",
        ["SAS", "2024", "prod"],
        ("SAS", "2024", Environment.PROD),
    ),
    (
        "src/sportpress/team_calendar.py",
        "src.sportpress.team_calendar_processor",
        "generate_sportpress_calendars",
        ["SAS", "2024", "prod"],
        ("sas", "2024", Environment.PROD),
    ),
    (
        "src/sportpress/team_games.py",
        "src.sportpress.team_games_processor",
        "generate_games",
        ["SAS", "2024", "prod"],
        ("sas", "2024", Environment.PROD),
    ),
    (
        "src/ctg/game_logs.py",
        "src.ctg.game_logs_processor",
        "generate_game_logs",
        ["2023", "2024", "prod"],
        ("2023", "2024", Environment.PROD),
    ),
    (
        "src/ctg/transitions.py",
        "src.ctg.transitions_processor",
        "compute_transitions_data",
        ["2023", "2024", "prod"],
        ("2023", "2024", Environment.PROD),
    ),
]

INVALID_ENTRYPOINT_CASES = [
    ("src/top100/top100.py", ["abc"]),
    ("src/bbref/top100.py", ["abc"]),
    ("src/bbindex/top100.py", ["abc"]),
    ("src/bbref/players.py", ["abc"]),
    ("src/bbref/game_logs.py", ["abc"]),
    ("src/bbref/team_calendar.py", ["SA", "2024"]),
    ("src/sportpress/team_calendar.py", ["SA", "2024"]),
    ("src/sportpress/team_games.py", ["SA", "2024"]),
    ("src/ctg/game_logs.py", ["abc"]),
    ("src/ctg/transitions.py", ["abc"]),
]


def _patch_downstream_callable(
    monkeypatch: pytest.MonkeyPatch,
    relative_script_path: str,
    module_name: str,
    attribute_name: str,
) -> list[tuple[Any, ...]]:
    script_path = PROJECT_ROOT / relative_script_path
    monkeypatch.syspath_prepend(str(PROJECT_ROOT))
    monkeypatch.syspath_prepend(str(script_path.parent))
    module = importlib.import_module(module_name)
    captured_calls: list[tuple[Any, ...]] = []

    def _fake_callable(*args: Any) -> None:
        captured_calls.append(args)

    monkeypatch.setattr(module, attribute_name, _fake_callable)
    return captured_calls


@pytest.mark.parametrize(
    ("relative_script_path", "module_name", "attribute_name", "argv", "expected_args"),
    VALID_ENTRYPOINT_CASES,
)
def test_should_delegate_to_expected_processor_when_cli_arguments_are_valid(
    monkeypatch: pytest.MonkeyPatch,
    relative_script_path: str,
    module_name: str,
    attribute_name: str,
    argv: list[str],
    expected_args: tuple[Any, ...],
) -> None:
    # Given
    captured_calls = _patch_downstream_callable(
        monkeypatch,
        relative_script_path,
        module_name,
        attribute_name,
    )

    # When
    run_cli_script(monkeypatch, relative_script_path, argv)

    # Then
    assert captured_calls == [expected_args]


@pytest.mark.parametrize(("relative_script_path", "argv"), INVALID_ENTRYPOINT_CASES)
def test_should_exit_with_code_one_when_cli_arguments_are_invalid(
    monkeypatch: pytest.MonkeyPatch,
    relative_script_path: str,
    argv: list[str],
) -> None:
    # Given / When / Then
    with pytest.raises(SystemExit) as raised_error:
        run_cli_script(monkeypatch, relative_script_path, argv)

    assert raised_error.value.code == 1

