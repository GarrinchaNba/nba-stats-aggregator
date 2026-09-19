from __future__ import annotations

import json

from bs4 import BeautifulSoup

from config.config import Environment
from src.nbacom.nbacom import extract_photo


def test_should_extract_images_from_stub_roster_cards(monkeypatch) -> None:
    # Given
    captured_calls: list[tuple[str, str, str, str]] = []

    monkeypatch.setattr("src.nbacom.nbacom.get_is_stubbed", lambda environment: True)
    monkeypatch.setattr("src.nbacom.nbacom.wait_random_duration", lambda: None)

    def _save_image(byte_array, first_name: str, last_name: str, team_name: str, year: str) -> None:
        captured_calls.append((first_name, last_name, team_name, year))

    monkeypatch.setattr("src.nbacom.nbacom.save_image", _save_image)

    # When
    extract_photo("sas", "2024", Environment.LOCAL)

    # Then
    assert captured_calls[0] == ("Jordan", "McLaughlin", "sas", "2024")
    assert "Victor" in {first_name for first_name, _, _, _ in captured_calls}
    assert len(captured_calls) > 1


def test_should_fall_back_to_image_alt_text_for_player_names(monkeypatch) -> None:
    # Given
    captured_calls: list[tuple[str, str, str, str]] = []
    player_card = BeautifulSoup(
        """
        <div data-testid="player-card">
            <img alt="Ja'Kobi Gillespie headshot" src="https://cdn.nba.com/headshots/nba/latest/1040x760/204123.png" />
        </div>
        """,
        "html.parser",
    )
    stub_soup = BeautifulSoup(
        f"<main id='page'><div>{player_card.decode()}</div></main>",
        "html.parser",
    )

    monkeypatch.setattr("src.nbacom.nbacom.get_is_stubbed", lambda environment: True)
    monkeypatch.setattr("src.nbacom.nbacom.get_stub_soup", lambda file_name: stub_soup)
    monkeypatch.setattr("src.nbacom.nbacom.wait_random_duration", lambda: None)

    def _save_image(byte_array, first_name: str, last_name: str, team_name: str, year: str) -> None:
        captured_calls.append((first_name, last_name, team_name, year))

    monkeypatch.setattr("src.nbacom.nbacom.save_image", _save_image)

    # When
    extract_photo("sas", "2024", Environment.LOCAL)

    # Then
    assert captured_calls == [("Ja'Kobi", "Gillespie", "sas", "2024")]


def test_should_fall_back_to_next_data_roster_payload_when_cards_are_absent(monkeypatch) -> None:
    # Given
    captured_calls: list[tuple[str, str, str, str]] = []
    script_payload = {
        "props": {
            "pageProps": {
                "rosterData": {
                    "roster": [{"id": 1628989, "firstName": "Victor", "lastName": "Wembanyama"}]
                }
            }
        }
    }
    page_html = (
        "<html><body><script id='__NEXT_DATA__' type='application/json'>"
        f"{json.dumps(script_payload)}</script></body></html>"
    )

    monkeypatch.setattr("src.nbacom.nbacom.get_is_stubbed", lambda environment: True)
    monkeypatch.setattr("src.nbacom.nbacom.get_stub_soup", lambda file_name: BeautifulSoup(page_html, "html.parser"))
    monkeypatch.setattr("src.nbacom.nbacom.wait_random_duration", lambda: None)

    def _save_image(byte_array, first_name: str, last_name: str, team_name: str, year: str) -> None:
        captured_calls.append((first_name, last_name, team_name, year))

    monkeypatch.setattr("src.nbacom.nbacom.save_image", _save_image)

    # When
    extract_photo("sas", "2024", Environment.LOCAL)

    # Then
    assert captured_calls == [("Victor", "Wembanyama", "sas", "2024")]
