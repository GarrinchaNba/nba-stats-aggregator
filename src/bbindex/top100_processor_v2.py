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
    TOP100_DATA_DIRECTORY
from src.common.data_collector import get_content_from_soup, get_soup_from_html_content
from src.common.file_processor import generate_csv_from_list_dicts, build_top100_csv_file_name
from src.common.stub import get_stub_soup, get_stub_file
from src.common.utils import get_all_seasons_between, get_year_from_season, \
    wait_random_duration, Duration, get_current_season_year, remove_accents
import shutil, time
from selenium.common.exceptions import WebDriverException


SLIDER_MIN_YEAR = 2010
SLIDER_MAX_YEAR = get_current_season_year()
SLIDER_LEFT_KNOB_YEAR = SLIDER_MAX_YEAR - 11
SLIDER_RIGHT_KNOB_YEAR = SLIDER_MAX_YEAR
INTERVALS = SLIDER_MAX_YEAR - SLIDER_MIN_YEAR - 4 # 4 seems to be an arbitrary valid value for now

def generate_top100_v2(min_year: str, max_year: str, environment: Environment) -> None:
    is_stubbed = get_is_stubbed(environment)
    seasons = get_all_seasons_between(int(min_year), int(max_year), '-')
    print('Generate top 100 bbindex from year [' + min_year + '] to [' + max_year + ']')
    if int(min_year) >= 2023:
        input_file_basketlab = build_top100_csv_file_name(BASKETLAB_COMPLETE_FILE_BASE, min_year, max_year)
    else:
        input_file_basketlab = build_top100_csv_file_name(BASKETLAB_WITH_RAPTORS_FILE, min_year, max_year)

    output_file: str = build_top100_csv_file_name(BASKETLAB_WITH_BBINDEX_FILE, min_year, max_year)
    COLUMNS_BBINDEX = ['Offensive Archetype', 'Defensive Role', 'LEBRON WAR', 'LEBRON', 'O-LEBRON', 'D-LEBRON']
    FIXED_PLAYERS: dict[str, str] = {
        "robert williams": "robert williams iii",
        # "jakob poeltl": "jakob poltl"
    }
    soup_by_season: dict[str, BeautifulSoup] = {}

    options = webdriver.FirefoxOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument('--headless')
    # Use pre-installed geckodriver if available, fallback to webdriver_manager
    geckodriver_path = os.environ.get('GECKODRIVER_PATH') or shutil.which('geckodriver')
    for season in seasons:
        print("Load web driver for Firefox...")
        driver = None
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if geckodriver_path:
                    service = Service(executable_path=geckodriver_path)
                    driver = webdriver.Firefox(service=service, options=options)
                else:
                    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
                break
            except WebDriverException as e:
                print(f"WebDriver initialization failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    raise RuntimeError("Failed to initialize Firefox WebDriver after multiple attempts.")
        try:
            print("Access LEBRON database page...")
            if not is_stubbed:
                driver.get('https://bball-index.shinyapps.io/Lebron/')
            else:
                driver.get('file://' + get_stub_file('stub_bbindex_players_short'))
            print("Filter for season [" + season + "]")
            try:
                WebDriverWait(driver, 20, 3).until(
                    expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "#Years-label"))
                )
            except RuntimeError:
                print('Error while waiting for filter')
                return
            season_year = int(get_year_from_season(season, '-'))
            slider = driver.find_element(By.XPATH,
                                         "//label[@id='Years-label']/following-sibling::span//span[@class='irs-bar']")
            move = webdriver.ActionChains(driver)
            knob_left = driver.find_element(By.XPATH,
                                            "//label[@id='Years-label']/following-sibling::span/span[contains(@class, 'irs-handle from')]")
            left_before = knob_left.location['x']
            print('Position left knob before move : ' + str(left_before))
            slider_width = slider.size['width']
            offset = (slider_width / INTERVALS) * (season_year - SLIDER_LEFT_KNOB_YEAR)
            move.click_and_hold(knob_left).move_by_offset(offset, 0).release().perform()
            knob_left = driver.find_element(By.XPATH,
                                            "//label[@id='Years-label']/following-sibling::span/span[contains(@class, 'irs-handle from')]")
            left_after = knob_left.location['x']
            print('Position left knob after move : ' + str(left_after))
            knob_right = driver.find_element(By.XPATH,
                                             "//label[@id='Years-label']/following-sibling::span/span[contains(@class, 'irs-handle to')]")
            right_before = knob_right.location['x']
            print('Position right knob before move : ' + str(right_before))
            offset = (slider_width / INTERVALS) * (season_year - SLIDER_RIGHT_KNOB_YEAR)
            move.click_and_hold(knob_right).move_by_offset(offset, 0).release().perform()
            knob_right = driver.find_element(By.XPATH,
                                             "//label[@id='Years-label']/following-sibling::span/span[contains(@class, 'irs-handle to')]")
            right_after = knob_right.location['x']
            print('Position right knob after move : ' + str(right_after))
            wait_random_duration(Duration.SHORT)
            print("Click on 'Run query'...")
            try:
                WebDriverWait(driver, 10, 2).until(
                    expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "#make_table"))
                )
            except RuntimeError:
                print('Error while running query')
                return
            element = driver.find_element(By.CSS_SELECTOR, "#make_table")
            element.click()
            if not is_stubbed:
                print("Wait for 'show entries' dropdown to appear...")
                try:
                    WebDriverWait(driver, 10, 2).until(
                        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "#DataTables_Table_0_length"))
                    )
                except RuntimeError:
                    print('Error while waiting "show entries" dropdown')
                    return
                print("Select show 'All' entries")
                try:
                    element = driver.find_element(
                        By.XPATH,
                        "//div[@id='DataTables_Table_0_length']//select[@name='DataTables_Table_0_length']/option[@value='-1']"
                    )
                    element.click()
                except RuntimeError:
                    print('Error while waiting for table to refresh.')
                    return
                print('Wait for table to refresh after asking all data...')
                try:
                    WebDriverWait(driver, 10, 2).until(
                        expected_conditions.presence_of_element_located(
                            (By.XPATH, "//table[@id='DataTables_Table_0']/tbody/tr[26]"))
                    )
                except RuntimeError:
                    print('Error while waiting for table to refresh.')
                    return
                print('Get page content...')
                page_source = driver.page_source
                soup = get_soup_from_html_content(page_source)
                soup_by_season[season] = soup
            else:
                soup_by_season[season] = get_stub_soup('stub_bbindex_players')
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except Exception as e:
                    print(f"Warning: error quitting driver: {e}")
    print('Extract rows...')
    rows_bbindex = build_seasons_player_data(soup_by_season, 'DataTables_Table_0')

    rows_top100_with_bbindex: list[dict[str, str]] = []
    with open(input_file_basketlab, newline='') as csvfile_basketlab:
        rows_top100: list[dict[str, str]] = list(csv.DictReader(csvfile_basketlab, delimiter=';'))
        for row_top100 in rows_top100:
            player_name = row_top100['first_name'] + ' ' + row_top100['last_name']
            player_season = row_top100['season']
            print("# Player : " + player_name + " (season : " + player_season + ")")
            if player_name in FIXED_PLAYERS:
                player_name = FIXED_PLAYERS[player_name]
            if player_season not in rows_bbindex[player_name]:
                print(f"  No data found for player [{player_name}] for season [{player_season}], zero padding.")
                # Zero padding for missing data
                for column in COLUMNS_BBINDEX:
                    column_updated = column.lower().replace(' ', '_').replace('-', '_')
                    row_top100[column_updated] = '0'
            else:
                season_by_player_name = rows_bbindex[player_name][player_season]
                for column, value in season_by_player_name.items():
                    if column not in COLUMNS_BBINDEX:
                        continue
                    column_updated = column.lower().replace(' ', '_').replace('-', '_')
                    row_top100[column_updated] = value
                season_year = get_year_from_season(player_season, '-')
                if int(season_year) < 2014:
                    row_top100['defensive_role'] = 'N/A'
            rows_top100_with_bbindex.append(row_top100)
    generate_csv_from_list_dicts(rows_top100_with_bbindex, TOP100_DATA_DIRECTORY, output_file, 'w')
    if not os.path.exists(output_file):
        print("Complete players data with bbindex failed")
    else:
        print("Complete players data with bbindex successful")


def build_player_name(player: str):
    return remove_accents(player).replace('.', '').replace('\'', '').lower()


def build_seasons_player_data(soups: dict[str, BeautifulSoup], html_id: str) -> dict[str, dict[str, dict[str, str]]]:
    rows_data = {}
    for season, soup in soups.items():
        table = get_content_from_soup(soup, html_id, 'table', 'id')
        head_rows = table.select('thead > tr:nth-child(1) > th')
        index_player = 0
        output_columns = []
        for index, row in enumerate(head_rows):
            if index == 0:
                continue
            value = row.text.strip()
            if value == 'Player':
                index_player = index
            output_columns.append(value)
        rows = table.select('tbody > tr')
        for index_row, row in enumerate(rows):
            player_name = None
            row_data = {}
            columns = row.find_all('td')
            for index_column, column in enumerate(columns):
                if index_column == 0:
                    continue
                value = column.text.strip()
                row_data[output_columns[index_column - 1]] = value
                if index_column == index_player:
                    player_name = build_player_name(value)
            if row_data and player_name:
                if player_name not in rows_data:
                    rows_data[player_name] = {}
                rows_data[player_name][season] = row_data
    return rows_data
