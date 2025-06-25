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
def get_prefix(page_url: str) -> str:
    path = urlparse(page_url).path                # '/yearly/yr2024a.shtml'
    pre_dot = path[-7] if len(path) >= 7 else ""  # char right before '.shtml'
    return "al_" if pre_dot == "a" else "nl_" if pre_dot == "n" else ""

def clean_table_name(header_td) -> str:
    """Return the plain text fragment between the two <a> links."""
    p_tag = header_td.find("p")
    if not p_tag:
        raise ValueError("No <p> tag inside header")

    text_parts = []
    for node in p_tag.contents:
        if isinstance(node, NavigableString):
            for part in map(str.strip, node.strip("←→ ").split("|")):
                # drop "2023", "2024", etc. at the *start* of the fragment
                part = re.sub(r"^\d{4}\s*", "", part)   # ← NEW line
                if part:                                # keep only non‑empty strings
                    text_parts.append(part)

    # choose the longest non‑empty fragment
    return max(text_parts, key=len) if text_parts else ""

def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")

def make_csv_name(page_url: str, header_td) -> str:
    core   = slugify(clean_table_name(header_td))
    prefix = get_prefix(page_url)
    return f"{prefix}{core}.csv" if core else ""

def extract_unique_banners(table):
    """Return a deduplicated, ordered list of column names
       from the FIRST <tr> that contains <td class="banner"> cells."""
    for tr in table.find_all("tr"): # walk rows top‑down
        cells = [td.get_text(strip=True) 
            for td in tr.find_all("td", class_="banner")]
        if cells: # found the first banner row
            # de‑dupelicate but keep order
            seen = set()
            unique = [c for c in cells if not (c in seen or seen.add(c))]
            return unique
    return []   

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
try:
    def link_list(header):
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
                    ""
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

# Derive year links from year table - function call
# Create link lists and merge them
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
    print(last_year)

    # Step 2: Build set of last 5 years
    last_5_years = set(range(last_year - 4, last_year + 1))
    print(last_5_years)

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
# 1.2. Scrape each year page
# ---------------------------------------------------------- #       
try:
    for year_link in last_5_years_links:
        year = year_link['year']
        league_name = year_link['league_name']
        year_href = year_link['year_href']

        print(f"Scraping {year} - {league_name} from {year_href}")

        y_l_soup = scraping_page(year_href)

        # # Find table with the td.header p contains "hiting"
        # for table in yl_soup.find_all("table", class_="boxed"):
        #     header_td = table.find("td", class_="header")
        #     if not header_td:
        #         continue

#                 filename = make_csv_name(driver.current_url, header_td)
#                 if not filename:
#                     continue

#                 # print("CSV filename would be:", filename)
            
#                 # Banner cells to headers 
#                 banner_cells = extract_unique_banners(table)
#                 # print(filename, banner_cells)
#                 if not banner_cells:
#                     continue 

#                 # Add Year column at the front
#                 # headers = ["Year"] + banner_cells

#                 # Datacol cells to data matrix
#                 data_cells = [td.get_text(strip=True) for td in table.find_all("td", class_ =lambda c: c and "datacol" in c)]
#                 width = len(banner_cells) # how many cols per row
#                 rows = [data_cells[i:i+width] for i in range(0, len(data_cells), width)]

#                 # Inject the year into each row (front or back must match headers)
#                 for r in rows:
#                     r.insert(0, year) # year first

#                 # Write / append to CSV 
#                 fp = Path(filename)

#                 need_header = filename not in header_done
#                 with fp.open("a", newline="", encoding="utf-8") as f:
#                     w = csv.writer(f)
#                     if need_header:
#                         w.writerow(["Year"] + banner_cells)
#                         header_done.add(filename) # don't write it again
#                     w.writerows(rows)

#                 # print(f"✓ {len(rows)} rows → {filename}")

# except Exception as e:
#     print("Top‑level error:", e)

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
