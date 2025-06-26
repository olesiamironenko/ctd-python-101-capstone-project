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

header_done = set()
# ---------------------------------------------------------- #


# ---------------------------------------------------------- #
# Helper functions
# ---------------------------------------------------------- #
def get_team(td, base_url):
    """
    Return (team_title, absolute_link) for the <a> whose title
    contains the word 'roster'. If none, return empty strings.
    """
    for a in td.find_all("a", href=True):
        title = a.get("title", "")
        if re.search(r"roster", title, re.I):
            clean = re.sub(r"\b\d{4}\b", "", title, flags=re.I)   # drop year
            clean = re.sub(r"\broster\b", "", clean, flags=re.I)       # drop 'roster'
            team_name = re.sub(r"\s{2,}", " ", clean).strip()

            return team_name, urljoin(base_url, a["href"])
    return "", ""
# ---------------------------------------------------------- #


# ---------------------------------------------------------- #
# Web Scraping
# ---------------------------------------------------------- #

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
            print(f"\n ERROR in: Common scraping page activity: reutrning soup")
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
                banners = tr.find_all('td', class_='banner')
                if banners:
                    first_row = ['Name'] + [b.text.strip() for b in banners]

                # Step 3: Data rows
                datacol_blue = tr.find('td', class_='datacolBlue')
                datacol_boxes = tr.find_all('td', class_='datacolBox')
                if datacol_blue and datacol_boxes:
                    row_name = datacol_blue.text.strip()
                    row_data = [box.text.strip() for box in datacol_boxes]
                    full_row = [row_name] + row_data
                    rows.append(full_row)

            # Step 4: Assemble DataFrame
            if rows:
                df = pd.DataFrame(rows, columns=first_row[:len(rows[0])])  # Trim header if needed
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
        print(last_5_ys_yealy_stats_1_df)
        last_5_ys_yealy_stats_1_df.info()

        last_5_ys_yealy_stats_2_df = pd.concat(last_5_ys_yealy_stats_2_list, ignore_index=True)
        print(last_5_ys_yealy_stats_2_df)
        last_5_ys_yealy_stats_2_df.info()

        

    except Exception as e:
        print("ERROR: Get tables titles")
        print(f"{e}")

    # Clean dfs
    try:
        # Step 1: Rename columns
        last_5_ys_yealy_stats_1_df.columns = ['team_name', 'statistics', 'player_name', 'year', 'league', 'stat_title']
        last_5_ys_yealy_stats_2_df.columns = ['team_name', 'statistics', 'player_name', 'year', 'league', 'stat_title']

        # Step 2: Convert year column to integer
        last_5_ys_yealy_stats_1_df['year'] = last_5_ys_yealy_stats_1_df['year'].astype(int)
        last_5_ys_yealy_stats_2_df['year'] = last_5_ys_yealy_stats_2_df['year'].astype(int)

    except Exception as e:
        print("ERROR: Get tables titles")
        print(f"{e}")

    # Concat cleaned dfs
    try:
        last_5_ys_yealy_stats = pd.concat([last_5_ys_yealy_stats_1_df,  last_5_ys_yealy_stats_2_df], ignore_index=True)

        print(last_5_ys_yealy_stats)
        last_5_ys_yealy_stats.info()

    except Exception as e:
        print("ERROR: Get tables titles")
        print(f"{e}")

except Exception as e:
        print("ERROR: Get tables titles")
        print(f"{e}")

# Write 5 years stats into CSVs
try:   
    last_5_ys_yealy_stats.to_csv('./csv/last_5_ys_yealy_stats.csv', sep=',', index=False)

except Exception as e:
    print("ERROR: Get tables titles")
    print(f"{e}") 


# except Exception as e:
#         print(f"{e}") 

# # 2.1. Get team and players info
# # Get team menu link
# try:
#     teams_link_el = WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.LINK_TEXT, "Team by Team"))
#     )

#     teams_url = teams_link_el.get_attribute('href')
#     # print("Team by Team link:", teams_url)
# except TimeoutException:
#     print("link not found")

# try:
#     url = teams_url

#     # Get last handle
#     driver.get(url)
#     driver.switch_to.window(driver.window_handles[-1])

#     # Wait for table to load
#     team_info = WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.CSS_SELECTOR, 'table.boxed'))
#     )

#     # Get HTML 
#     team_info_html = team_info.get_attribute('outerHTML')
#     # print(team_info_table_html)

#     soup = BeautifulSoup(team_info_html, 'html.parser')
#     # print(soup)

#     team_table = soup.find("table")
    
#     # Extract league names from banner row
#     banner_names = extract_unique_banners(team_table)
#     if len(banner_names) < 2:
#         raise ValueError("Need at least two banner columns")
#     league1, league2 = banner_names[:2]
#     prefix1 = "al" if "american" in league1.lower() else "nl"
#     prefix2 = "al" if "american" in league2.lower() else "nl"
#     # print(banner_names)

#     # Extract rows and links
#     rows = [] # final CSV rows
#     roster_links = [] # [(team_name, abs_link), …]
#     seen_links = set() # dedupe roster links
#     seen_banners = set() # dedupe banner rows
#     stop = False # flag to halt after duplicate banner


#     for tr in team_table.find_all("tr"):
#         if stop:
#             break

#         # Get banner row
#         banner_tds = tr.find_all("td", class_="banner")
#         if banner_tds:
#             for td in banner_tds:
#                 text = td.get_text(strip=True)
#                 if text in seen_banners: # first duplicate -> set flag
#                     stop = True
#                     break
#                 seen_banners.add(text)
#             continue # skip data parsing on banner rows

#         # Get data row
#         datacols = tr.find_all("td", class_=lambda c: c and "datacol" in c)
#         if len(datacols) < 2:
#             continue

#         team1_title, team1_link = get_team(datacols[0], base_url)
#         team2_title, team2_link = get_team(datacols[1], base_url)
        
#         # Collect rows
#         rows.append([team1_title, team1_link, team2_title, team2_link])

#         # Collect unique roster links
#         for title, link in ((team1_title, team1_link), (team2_title, team2_link)):
#             if link and link not in seen_links:
#                 roster_links.append((title, link))
#                 seen_links.add(link)

#     # print(f"Collected {len(rows)} rows")
#     # print(f"Collected {len(roster_links)} unique roster links")

#     # Write/append CSV
#     filename = f"{prefix1}_{prefix2}_teams.csv"
#     csv_path = Path(filename)
#     need_header = not csv_path.exists()

#     with csv_path.open("a", newline="", encoding="utf-8") as f:
#         w = csv.writer(f)
#         if need_header:
#             w.writerow([
#                 f"{prefix1}_team_title", f"{prefix1}_team_link",
#                 f"{prefix2}_team_title", f"{prefix2}_team_link"
#             ])
#         w.writerows(rows)

#     # print(f"Wrote {len(rows)} rows to {filename}")

#     # Scrape teams pages
#     for team_name, roster_url in roster_links: # 1 roster page
#         driver.get(roster_url)

#         # Loop through nav-tabs
#         while True:
#             try:
#                 # Wait for the table then active tab
#                 WebDriverWait(driver, 10).until(
#                     EC.presence_of_element_located((By.CSS_SELECTOR, "table.boxed"))
#                 )
#                 nav_el = driver.find_element(By.CSS_SELECTOR, ".navtabactive")
#                 tab_label = nav_el.text.strip()
#             except NoSuchElementException:
#                 # There is no navbar on the page
#                 print("No active navtab on", driver.current_url, "→ finished this roster")
#                 break # leave the inner while-loop and go to next roster page

#             # Parse current table
#             soup  = BeautifulSoup(driver.page_source, "html.parser")
#             table = soup.find("table", class_="boxed")
#             rows  = []
#             for tr in table.find_all("tr"):
#                 td_cells = tr.select('td.banner, td[class*="datacol"]')
#                 if not td_cells:
#                     continue
#                 row = [td.get_text(strip=True) for td in td_cells if isinstance(td, Tag)]
#                 if row:
#                     row.insert(0, team_name) # inject team name
#                     rows.append(row)

#             if rows:
#                 csv_name = re.sub(r"[^a-z0-9]+", "_", tab_label.lower()).strip("_") + ".csv"
#                 with Path(csv_name).open("a", newline="", encoding="utf-8") as f:
#                     csv.writer(f).writerows(rows)
#                 print(f"for {team_name} {len(rows)} rows added to {csv_name}")

#             # Click next inactive tab, if any
#             try:
#                 next_tab = nav_el.find_element(
#                     By.XPATH,
#                     'following-sibling::div[contains(@class,"navtabinactive")][1]/a'
#                 )
#                 next_tab.click()
                
#                 # Wait for the old tab to disappear
#                 WebDriverWait(driver, 10).until(EC.staleness_of(nav_el))

#                 # Wait for the new active tab to appear and become active
#                 WebDriverWait(driver, 10).until(
#                     EC.presence_of_element_located((By.CSS_SELECTOR, ".navtabactive"))
#                 )
#             except Exception:
#                 break # no more tabs → next roster page

except TimeoutException:
    print("link not found")

finally:
    driver.quit()
