import csv
import os

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager

from config.config import Environment, get_is_stubbed
from src.common.constant import BASKETLAB_COMPLETE_FILE_BASE, BASKETLAB_WITH_RAPTORS_FILE, BASKETLAB_WITH_BBINDEX_FILE, \
    BBINDEX_DATA_DIRECTORY, BASKETBALL_INDEX_URL
from src.common.data_collector import get_content_from_soup, get_soup_from_html_content
from src.common.file_processor import generate_csv_from_list_dicts, build_top100_csv_file_name
from src.common.stub import get_stub_soup, get_stub_file
from src.common.utils import get_all_seasons_between, get_shortened_season_name


def generate_top100(min_year: str, max_year: str, environment: Environment) -> None:
    is_stubbed = get_is_stubbed(environment)
    seasons = get_all_seasons_between(int(min_year), int(max_year), '-')
    print('Generate top 100 bbindex from year [' + min_year + '] to [' + max_year + ']')
    if int(min_year) >= 2023:
        input_file_basketlab = build_top100_csv_file_name(BASKETLAB_COMPLETE_FILE_BASE, min_year, max_year)
    else:
        input_file_basketlab = build_top100_csv_file_name(BASKETLAB_WITH_RAPTORS_FILE, min_year, max_year)

    output_file: str = build_top100_csv_file_name(BASKETLAB_WITH_BBINDEX_FILE, min_year, max_year)
    COLUMNS_BBINDEX = ['offensive-archetype', 'lebron', 'o-lebron', 'd-lebron', 'war', 'boxlebron', 'boxolebron',
                       'boxdlebron']
    FIXED_PLAYERS: dict[str, str] = {
        "robert williams": "robert williams iii"
    }
    soup_by_season: dict[str, BeautifulSoup] = {}

    print("Access LEBRON database page...")
    options = webdriver.FirefoxOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
    if not is_stubbed:
        driver.get(BASKETBALL_INDEX_URL + '/lebron-database/')
    else:
        driver.get('file://' + get_stub_file('stub_bbindex_players_short'))

    for season in seasons:
        print("Filter for season [" + season + "]")
        try:
            WebDriverWait(driver, 10, 2).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, ".column-season"))
            )
        except RuntimeError:
            driver.quit()
        element = driver.find_element(By.XPATH, "//*[@class='column-season']//input")
        element.send_keys(get_shortened_season_name(season, '-'))
        # wait_random_duration(Duration.SHORT)
        print("Wait for 'show entries' select to appear...")
        try:
            WebDriverWait(driver, 10, 2).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, ".filter-option"))
            )
        except RuntimeError:
            driver.quit()
        element = driver.find_element(By.CSS_SELECTOR, ".filter-option")
        element.click()

        if not is_stubbed:
            print("Wait for 'show entries' dropdown to appear...")
            try:
                WebDriverWait(driver, 10, 2).until(
                    expected_conditions.presence_of_element_located((By.CSS_SELECTOR, ".dropdown-menu.open.show"))
                )
            except RuntimeError:
                driver.quit()
            element = driver.find_element(By.XPATH,
                                          "//*[@class='dropdown-menu open show']//li[@data-original-index='6']")
            element.click()
            print('Wait for table to refresh after asking all data...')
            try:
                WebDriverWait(driver, 10, 2).until(
                    expected_conditions.presence_of_element_located((By.ID, "table_1"))
                )
            except RuntimeError:
                driver.quit()
            element = driver.find_element(By.XPATH, "//table[@id='table_1']//th[contains(@class, 'column-player')]")
            element.click()

            print('Wait for table to refresh after sorting...')
            try:
                WebDriverWait(driver, 15, 2).until(
                    expected_conditions.presence_of_element_located((By.ID, "table_1"))
                )
            except RuntimeError:
                driver.quit()
            print('Get page content...')
            page_source = driver.page_source
            soup = get_soup_from_html_content(page_source)
            soup_by_season[season] = soup
        else:
            soup_by_season[season] = get_stub_soup('stub_bbindex_players')
    print('Extract rows...')
    rows_bbindex = build_seasons_player_data(soup_by_season, 'table_1')

    rows_top100_with_bbindex: list[dict[str, str]] = []
    with open(input_file_basketlab, newline='') as csvfile_basketlab:
        rows_top100: list[dict[str, str]] = list(csv.DictReader(csvfile_basketlab, delimiter=';'))
        for row_top100 in rows_top100:
            player_name = row_top100['first_name'] + ' ' + row_top100['last_name']
            player_season = row_top100['season']
            print("# Player : " + player_name + " (season : " + player_season + ")")
            season_by_player_name = rows_bbindex[player_name][player_season]
            for column, value in season_by_player_name.items():
                if column not in COLUMNS_BBINDEX:
                    continue
                column_updated = column.replace('-', '_')
                row_top100[column_updated] = value
            rows_top100_with_bbindex.append(row_top100)
    generate_csv_from_list_dicts(rows_top100_with_bbindex, BBINDEX_DATA_DIRECTORY, output_file, 'w')
    if not os.path.exists(output_file):
        print("Complete players data with bbindex failed")
    else:
        print("Complete players data with bbindex successful")


def build_player_name(player: str):
    return player.replace('.', '').replace('\'', '').lower()


def build_seasons_player_data(soups: dict[str, BeautifulSoup], html_id: str) -> dict[str, dict[str, dict[str, str]]]:
    rows_data = {}
    for season, soup in soups.items():
        table = get_content_from_soup(soup, html_id, 'table', 'id', 'tbody')
        rows = table.find_all('tr')
        for row in rows:
            player_name = None
            row_data = {}
            columns = row.find_all('td')
            for column in columns:
                if column.text.strip() == '':
                    break
                klasses = column['class']
                output_column = ''
                for klass in klasses:
                    if 'column-' in klass:
                        output_column = klass[7:]
                        break
                if not output_column:
                    continue
                row_data[output_column] = column.text.strip()
                if output_column.lower() == 'player':
                    player_name = build_player_name(row_data[output_column])

            if row_data and player_name:
                if player_name not in rows_data:
                    rows_data[player_name] = {}
                rows_data[player_name][season] = row_data
    return rows_data
