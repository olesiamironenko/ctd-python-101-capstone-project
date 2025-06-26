from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import re
import csv
import os
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.parse import urljoin
from urllib.parse import urlparse
from collections import defaultdict
from urllib.parse import urljoin
from pathlib import Path
import numpy as np

# ---------------------------------------------------------- #
# Driver settings
# ---------------------------------------------------------- #
opt = webdriver.ChromeOptions()
opt.add_argument("--headless=new")              # Chrome >= 118
opt.add_argument("--disable-gpu")
opt.add_argument("--blink-settings=imagesEnabled=false")
opt.add_argument("--disable-plugins-discovery")
opt.add_argument("--disable-extensions")
opt.add_argument("--disable-javascript")        # if tables are static
prefs = {
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.stylesheets": 1,  # keep CSS =1 or block =2
    "profile.managed_default_content_settings.fonts": 2,
    "profile.managed_default_content_settings.video": 2,
}
opt.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()),
    options=opt
)
driver.set_page_load_timeout(10) # fail fast if site hangs
# ---------------------------------------------------------- #

# ---------------------------------------------------------- #
# Helper variables
# ---------------------------------------------------------- #
# Keep base url to join with extracted later
base_url = 'https://www.baseball-almanac.com/'

url = 'https://www.baseball-almanac.com/yearmenu.shtml'
# ---------------------------------------------------------- #

# ---------------------------------------------------------- #
# Web Scraping
# ---------------------------------------------------------- #
try:
    # Common scraping activity using selenium and BeautifulSoup
    def scraping_page(url):
        try:
            # Load the web page
            driver.get(url)

            # Grab the surviving window handle (always the newest)
            driver.switch_to.window(driver.window_handles[-1])

            # Wait for the table to be loaded 
            get_html = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except TimeoutException:
            print("Timed-out waiting for the year list table.")
        
        try:
            # Get HTML 
            html = get_html.get_attribute('outerHTML')
            # print(div_container_html) 

        # Parse scraped html using beautiful soup 
            soup = BeautifulSoup(html, 'html.parser')
            # print(soup)
            return soup

        except Exception as e:
                print(f"\n ERROR in: Common scraping page activity: getting html")
                print(f"\n ERROR in: Common scraping page activity: retrning soup")
                print(f"{e}") 
    # ---------------------------------------------------------- #


    # ---------------------------------------------------------- #
    # Scrape yearly history
    # ---------------------------------------------------------- #
    # ---------------------------------------------------------- #
    # 1.1. Get years and links from 'Year to Year' page
    # ---------------------------------------------------------- #

    # Find table with class boxed
    try:  
        soup = scraping_page(url)
        years_table = soup.find('table', class_='boxed')


    # Find td.headers and subtables with year links
        # Find first 2 headers
        if years_table:
            # print(years_table) 
            t_headers = years_table.find_all('td', class_='header')
            header1 = t_headers[0]
            header2 = t_headers[1]
        else:
            print("No table with class 'boxed' was found")
    except Exception as e:
            print(f"\n ERROR in: Find table with class boxed")
            print(f"\n ERROR in: Find first 2 headers")
            print(f"{e}") 

    # Derive year links from year table - function
    def link_list(header):
        try:
            # Find parent of t_headers
            header_tr = header.find_parent('tr')

            # Loop over following siblings to find the one that have table.ba_sub
            for sibling in header_tr.find_next_siblings('tr'):
                td = sibling.find('td', class_='datacolBox')
                if td and td.find('table', class_='ba-sub'):
                    # print("Found <tr> with <td> containing a <table class='ba_sub'> inside:")
                    # print(sibling)
                    sub_table = td.find('table', class_='ba-sub')
                    break
            
            # Declare link_list
            year_link_list = []

            # Loop through the subtable and pull all years and links
            year_links = sub_table.find_all('a')
            # print(year_links)
            for year_link in year_links:
                year_href = urljoin(base_url, year_link['href'])
                year_text = year_link.text
                if len(year_href) >= 7: # char right before '.shtml'
                    if year_href[-7] == "a":
                        league_name = "American League"
                    elif year_href[-7] == "n":
                        league_name = "National League"
                    else:
                        continue
                # Append dicts to year_link_list
                year_link_list.append({
                    'year_href': year_href,
                    'year': year_text,
                    'league_name':league_name
                })
            
            return year_link_list
    
        except Exception as e:
            print(f"\n ERROR in: Derive year links function")
            print(f"{e}") 

    # Create link lists ussing link_list function, and merge them the lists
    try:
        year_link_list1 = link_list(header1)
        year_link_list2 = link_list(header2)

        year_link_list_full = year_link_list1 + year_link_list2
    except Exception as e:
            print(f"\n ERROR in: Creating link lists")
            print(f"{e}") 

    # Get links for last 5 years only
    try:
        # Step 1: Convert to int → find max year
        int_years = []
        for year_link in year_link_list_full:
            year = year_link['year']
            int_year = int(year)
            # print(int_year)
            int_years.append(int_year)
        last_year = max(int_years)
        # print(last_year)

        # Step 2: Build set of last 5 years
        last_5_years = set(range(last_year - 4, last_year + 1))
        # print(last_5_years)

        # Step 3: Filter original list
        last_5_years_links = []
        for year_link in year_link_list_full:
            year = int(year_link['year'])
            if year in last_5_years:
                last_5_years_links.append(year_link) 

        # print(last_5_years_links)

    except Exception as e:
        print(f"\n ERROR in: Finding 5 last years only")
        print(f"{e}") 

    # Create year link df out of 5 last years links list
    try:
        last_5_years_links_df = pd.DataFrame(last_5_years_links)
        # print(last_5_years_links_df)
        # last_5_years_links_df.info()

    except Exception as e:
            print(f"\n ERROR in: Creating link lists")
            print(f"{e}") 
    # ---------------------------------------------------------- #


    # ---------------------------------------------------------- #
    # 1.2. Scrape each year page of the last 5 years
    # ---------------------------------------------------------- #       
    try:
        # Declare lists for each table sscraping results
        last_5_ys_yealy_stats_1_list = []
        last_5_ys_yealy_stats_2_list = []
        
        # Loop through year links
        for year_link in last_5_years_links:
            year = year_link['year']
            league_name = year_link['league_name']
            year_href = year_link['year_href']

            print(f"Scraping {year} - {league_name} from {year_href}")

            # Get necessary html code from one page for further parsing
            y_l_soup = scraping_page(year_href)

            # Parse collected html
            try:
                # Find all tabls with class boxed
                y_stat_tables = y_l_soup.find_all("table", class_="boxed")
                # print(y_stat_tables)

                # Get only 2 tables: hitting stats and pitching stats
                # Assign tables to variables
                scrape_y_stat_table1 = y_stat_tables[0]
                scrape_y_stat_table2 = y_stat_tables[1]
            except Exception as e:
                print("ERROR: Find tabls with class boxed")
                print(f"{e}") 

            # Create stat list
            # - tr: td.header: h2: year -> column (name + data)
            # - tr: td.header: h2: league -> column (name + data)
            # - tr: td.header: p: stats title/type -> column (name + data)
            # - tr: td.banner: column names -> column names / first row
            # - tr: td.datacolBlue + tr.datacolBox: row name (td.datacolBlue) + data (datacolBox) -> rows

            def scrape_stats_table(table):
                # Declare all necessary lists and variables
                rows = []
                first_row = []
                y_stat_year = None
                y_stat_league = None
                y_stat_title = None

                # Scrape a table
                # Find all table rows and iterate through them
                trs = table.find_all('tr')

                for tr in trs:
                    # Step 1: Header info (only once)
                    header = tr.find('td', class_='header')
                    if header and not y_stat_year:
                        # Get year and league name
                        h2 = header.find('h2')
                        if h2:
                            h2_text = h2.get_text(strip=True)
                            year_match = re.search(r"^(\d{4})", h2_text)
                            league_match = re.search(r"^\d{4}\s+(\w+\s+\w+)", h2_text)
                            if year_match:
                                y_stat_year = year_match.group(1)
                            if league_match:
                                y_stat_league = league_match.group(1)

                        # Get statistic name
                        p = header.find('p')
                        if p:
                            p_text = p.get_text(strip=True)
                            stat_match = re.search(r".*\d{4}\s+(\w+\s+\w+)", p_text)
                            if stat_match:
                                y_stat_title = stat_match.group(1)

                    # Step 2: Banners — first row
                    if not first_row:
                        banners = tr.find_all('td', class_='banner')
                        if banners:
                            for banner in banners:
                                banner_text = banner.get_text(strip=True)
                                first_row.append(banner_text)

                    # Step 3: Data rows
                    datacol_blue = tr.find('td', class_='datacolBlue')
                    if datacol_blue:
                        row_name = datacol_blue.text.strip()

                        # Get *all* <td> elements in the row
                        tds = tr.find_all('td')

                        # Skip the first td (it's datacol_blue), and parse the rest
                        row_data = []
                        skip = True
                        for td in tds:
                            if skip:
                                if td == datacol_blue:
                                    skip = False
                                continue

                            text = td.get_text(strip=True)
                            row_data.append(text)

                        full_row = [row_name] + row_data

                        # Only append if it matches banner length
                        if len(full_row) == len(first_row):
                            rows.append(full_row)

                # Step 4: Assemble DataFrame
                if rows:
                    df = pd.DataFrame(rows, columns=first_row)  # Trim header if needed
                else:
                    df = pd.DataFrame()

                df['year'] = y_stat_year
                df['league'] = y_stat_league
                df['stat_title'] = y_stat_title

                return df

            try:
                # print(f"\n scrape_y_stat_table1 results:")
                y_stat_df_1 = scrape_stats_table(scrape_y_stat_table1)
                # print(y_stat_df_1)
                last_5_ys_yealy_stats_1_list.append(y_stat_df_1)

                # print(f"\n scrape_y_stat_table2 results:")
                y_stat_df_2 = scrape_stats_table(scrape_y_stat_table2)
                # print(y_stat_df_2)
                last_5_ys_yealy_stats_2_list.append(y_stat_df_2)

            except Exception as e:
                print(f"{e}") 
        
        # Combine scraping results from all year pages into one list per each teble scraped
        try:
            last_5_ys_yealy_stats_1_df = pd.concat(last_5_ys_yealy_stats_1_list, ignore_index=True)
            # print(last_5_ys_yealy_stats_1_df)
            # last_5_ys_yealy_stats_1_df.info()

            last_5_ys_yealy_stats_2_df = pd.concat(last_5_ys_yealy_stats_2_list, ignore_index=True)
            # print(last_5_ys_yealy_stats_2_df)
            # last_5_ys_yealy_stats_2_df.info()

        except Exception as e:
            print("ERROR: Combine scraping results from all year")
            print(f"{e}")

        # Concat dfs
        try:
            last_5_ys_yealy_stats = pd.concat([last_5_ys_yealy_stats_1_df,  last_5_ys_yealy_stats_2_df], ignore_index=True)

        except Exception as e:
            print(f"{e}")

        # Clean dfs
        try:
            # Step 1: Rename columns
            last_5_ys_yealy_stats.columns = ['statistic', 'player_name', 'team_name', 'no', 'top_25', 'year', 'league', 'stat_title']

            # Step 2: Convert values type
            # 2.1. year column to integer
            last_5_ys_yealy_stats['year'] = last_5_ys_yealy_stats['year'].astype(int)
            
            # 2.1. no column to float

            last_5_ys_yealy_stats['no'] = last_5_ys_yealy_stats['no'].replace("--", np.nan).astype(float)

            print(last_5_ys_yealy_stats)
            last_5_ys_yealy_stats.info()

        except Exception as e:
            print(f"{e}")

    except Exception as e:
            print(f"{e}")

    # ---------------------------------------------------------- #
    # 1.3. Normalize last_5_ys_yealy_stats 
    # ---------------------------------------------------------- #   

    """full db schema draft:
    - statistics and stat_titles step1:
    - df: statistics:
        col: statistics.statistic -> data form last_5_ys_yealy_stats.statistics
        cole: statistics.stat_title -> data from last_5_ys_yealy_stats.stat_title
        col: statistics.statistic_id pk -> last_5_ys_yealy_stats.statistic_id fk

                - statistics and stat_titles step2:
                - df: stat_titles:
                    col: stat_titles.stat_title -> data from statistics.stat_title
                    col: stat_titles.stat_title_id pk -> statistics.stat_title_id fk

                - df: statistics:
                    col: statistics.statistic (nothing canges) -> data
                    col: statistics.statistic_id pk (nothing canges) -> last_5_ys_yealy_stats.statistic_id fk
                    col: statistics.stat_title_id fk -> stat_title.stat_title_id pk 

    - players and teams step1:
    - df: players:
        col: players.player_name -> data from last_5_ys_yealy_stats.player_name
        col: players.team_name -> data from last_5_ys_yealy_stats.team_name
        col: players.player_id pk -> last_5_ys_yealy_stats.player_id fk 

            - players and teams step2:
                - df: teams:
                    col: teams.team_name -> data from players.team_name
                    col: teams.team_id pk -> players.team_id fk

                - df: players:
                    col: players.player_name (nothing canges) -> data from last_5_ys_yealy_stats.player_name
                    col: players.player_id pk -> players.player_id fk 
                    col: players.player_id fk -> teams.player_id pk
                                    
    - years:
        col: years.year -> data from last_5_ys_yealy_stats.year (is this needed)
        col: years.year_id pk -> last_5_ys_yealy_stats.year_id fk

    - leagues:
        col: leagues.league_name -> data from last_5_ys_yealy_stats.league
        col: leagues.league_id pk -> last_5_ys_yealy_stats.league_id fk

    - last_5_ys_yealy_stats:
        col: last_5_ys_yealy_stats.statistic_id fk -> statistics.statistic_id pk
        col: last_5_ys_yealy_stats.player_id (old: last_5_ys_yealy_stats.player_name) -> players.player_id pk
        col: last_5_ys_yealy_stats.team_id (old: last_5_ys_yealy_stats.team_name) -> players join teams on plaier_id, teams.team_id pk
        col: last_5_ys_yealy_stats.no (nothing changes) -> data
        col: last_5_ys_yealy_stats.top_25 (nothing_changes) -> data
        col: last_5_ys_yealy_stats.year_id fk (old: last_5_ys_yealy_stats.year) -> years.year_id pk
        col: last_5_ys_yealy_stats.league_id fk (old: last_5_ys_yealy_stats.league) -> leagues.league_id pk
        col: last_5_ys_yealy_stats.stat_title_id fk (old: last_5_ys_yealy_stats.stat_title) -> statistics join stat_titles on statistic_id, stat_titles.stat_title_id
    """

    # 1.3.0: normalization function:
    def create_lookup_df(
            df, 
            *cols, 
            id_col_name='id'):
        """
        Create a normalized lookup DataFrame with a primary key column.

        Args:
            df: Original DataFrame
            *cols: Column names to include in the lookup table
            id_col_name: Name of the ID column to be created

        Returns:
            A new DataFrame with a unique ID column and unique trimmed combinations of input columns.
        """
        try:
            for col in cols:
                df[col] = df[col].astype(str).str.strip()

            lookup_df = (
                df[list(cols)]
                .drop_duplicates()
                .sort_values(by=list(cols))
                .reset_index(drop=True)
                .reset_index()  # create ID column
                .rename(columns={"index": id_col_name})
            )
        except Exception as e:
            print(f"Error in create_lookup_df for columns {cols}: {e}")

        return lookup_df

    # 1.3.1: Step1: normalization 1:
    print(f"\n Step 1 normalization: \n")
    try:
        # statistics
        statistics = create_lookup_df(
            last_5_ys_yealy_stats, 
            'statistic', 'stat_title', 
            id_col_name='statistic_id')

        # print(f"\n statistics df: \n")
        # print(statistics)
        # statistics.info()

        # players
        players = create_lookup_df(
            last_5_ys_yealy_stats, 
            'player_name', 'team_name', 
            id_col_name='player_id')

        # print(f"\n players df: \n")
        # print(players)
        # players.info()

        # years
        years = create_lookup_df(
            last_5_ys_yealy_stats, 
            'year', 
            id_col_name='year_id')

        # print(f"\n years df: \n")
        # print(years)
        # years.info()

        # leagues
        leagues = create_lookup_df(
            last_5_ys_yealy_stats, 
            'league', 
            id_col_name='league_id')

        # print(f"\n leagues df: \n")
        # print(leagues)
        # leagues.info()

    except Exception as e:
            print(f"{e}")
            print("df creation error")

    # 1.3.2: Step 2: normalization 2:
    print(f"\n Step 2 normalization: \n")
    try:
        # stat_titles
        stat_titles = create_lookup_df(
            statistics, 
            'stat_title', 
            id_col_name='stat_title_id')

        # print(f"\n stat_titles df: \n")
        # print(stat_titles)
        # stat_titles.info()

        # teams
        teams = create_lookup_df(
            players, 
            'team_name', 
            id_col_name='team_id')

        # print(f"\n teams df: \n")
        # print(teams)
        # teams.info()

    except Exception as e:
            print(f"{e}")
            print("df creation error")

    # ---------------------------------------------------------- #
    # 1.4: switching text columns to ids: adding fk

    # 1.4.0: switching text columns to ids: merge id columnn to main df function:
    def add_simple_foreign_key(
            main_df, 
            lookup_df, 
            on_column, 
            fk_column):
        
        """ add_simplpe_foreign_key explinatio:
        Merge a lookup table into the main DataFrame to replace a text column with a foreign key.

        Args:
            main_df (pd.DataFrame): The main DataFrame containing a text column (e.g., 'stat_title').
            lookup_df (pd.DataFrame): The lookup DataFrame with 'on_column' and ID column (e.g., 'stat_title_id').
            on_column (str): The column name to join on (must exist in both DataFrames).
            fk_column (str): The name of the ID column in df_lookup to add to df_main.

        Returns:
            pd.DataFrame: The updated DataFrame with the foreign key column added.
        """
        try:
            main_df = main_df.merge(lookup_df[[on_column, fk_column]], on=on_column, how='left')
        except Exception as e:
            print(f"Error merging on {on_column}: {e}")

        return main_df

    def add_combined_foreign_key(
            main_df, 
            lookup_df, 
            on_columns, 
            fk_column):
        
        """ add_combined_foreign_key explinatio:
        Merge a lookup table into the main DataFrame to replace a text column with a foreign key.

        Args:
            main_df (pd.DataFrame): The main DataFrame containing a text column (e.g., 'stat_title').
            lookup_df (pd.DataFrame): The lookup DataFrame with 'on_columns' and ID column (e.g., 'stat_title_id').
            on_columns (str): The column names to join on (must exist in both DataFrames).
            fk_column (str): The name of the ID column in df_lookup to add to df_main.

        Returns:
            pd.DataFrame: The updated DataFrame with the foreign key column added.
        """

        try:
            main_df = main_df.merge(lookup_df[on_columns + [fk_column]], on=on_columns, how='left')
        except Exception as e:
                print(f"Error merging on {on_columns}: {e}")
        return main_df

    # 1.4.1: switching text columns to ids: adding fk
    print(f"\n Step 3 switching text columns to ids: adding fk:  \n")
    try:
        # statistics: stat_title_id
        statistics = add_simple_foreign_key(
            statistics, 
            stat_titles, 
            'stat_title', 
            'stat_title_id', )

        # print(f"\n statistics df with stat_title_id: \n")
        # print(statistics)
        # statistics.info()

        # players: team_id
        players = add_simple_foreign_key(
            players, 
            teams, 
            'team_name', 
            'team_id')
        
        # print(f"\n players df with team_id: \n")
        # print(players)
        # players.info()
        
        # last_5_ys_yealy_stats: statistic_id:
        last_5_ys_yealy_stats = add_combined_foreign_key(
            last_5_ys_yealy_stats, 
            statistics, 
            ['statistic', 'stat_title'],
            'statistic_id')

        # print(f"\n last_5_ys_yealy_stats df with statistic_id: \n")
        # print(last_5_ys_yealy_stats)
        # last_5_ys_yealy_stats.info()

        # last_5_ys_yealy_stats: player_id: 
        last_5_ys_yealy_stats = add_combined_foreign_key(
            last_5_ys_yealy_stats, 
            players, 
            ['player_name', 'team_name'],
            'player_id')

        # print(f"\n last_5_ys_yealy_stats df with statistic_id, player_id: \n")
        # print(last_5_ys_yealy_stats)
        # last_5_ys_yealy_stats.info()

        # last_5_ys_yealy_stats: year_id: 
        last_5_ys_yealy_stats = add_simple_foreign_key(
            last_5_ys_yealy_stats, 
            years, 
            'year',
            'year_id')

        # print(f"\n last_5_ys_yealy_stats df with statistic_id, player_id, year_id: \n")
        # print(last_5_ys_yealy_stats)
        # last_5_ys_yealy_stats.info()

        # last_5_ys_yealy_stats: league_id: 
        last_5_ys_yealy_stats = add_simple_foreign_key(
            last_5_ys_yealy_stats, 
            leagues, 
            'league',
            'league_id')

        # print(f"\n last_5_ys_yealy_stats df with statistic_id, player_id, year_id, league_id: \n")
        # print(last_5_ys_yealy_stats)
        # last_5_ys_yealy_stats.info()

    except Exception as e:
            print(f"{e}")

    # 1.4.2: switching text columns to ids: dropping text columnns

    def drop_columns(df, *cols):
        """
        Drop one or more columns from a DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame to modify.
            *cols (str): Column names to drop.

        Returns:
            pd.DataFrame: A copy of the DataFrame with specified columns dropped.
        """
        try:
            df = df.drop(columns=list(cols), errors='ignore')

        except TimeoutException:
            print("link not found")
            
        return df

    print(f"\n Step 3 switching text columns to ids: adding dropping text columnns:  \n")
    try:
        # statistics: drop stat_title
        statistics = drop_columns(statistics, 'stat_title')

        print(f"\n statistics df: stat_title dropped \n")
        print(statistics)
        statistics.info()

        # players: drop team_name
        players = drop_columns(players, 'team_name')

        print(f"\n players df: team_name dropped \n")
        print(players)
        players.info()

        # last_5_ys_yealy_stats: drop statistic, player_name, team_name, year, stat_title
        last_5_ys_yealy_stats = drop_columns(last_5_ys_yealy_stats, 'statistic', 'player_name', 'team_name', 'league', 'year', 'stat_title')

        print(f"\n last_5_ys_yealy_stats df: statistic, player_name, team_name, league, year, and stat_title dropped \n")
        print(last_5_ys_yealy_stats)
        last_5_ys_yealy_stats.info()

    except Exception as e:
        print(f"{e}")
finally:
    driver.quit()
