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
import re
import csv
import os
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urljoin
from urllib.parse import urlparse
from collections import defaultdict
from urllib.parse import urljoin
from pathlib import Path

# ------------------------------------------------------------------
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
# ------------------------------------------------------------------

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

# Load the web page
driver.get('https://www.baseball-almanac.com/yearmenu.shtml')

# Grab the surviving window handle (always the newest)
driver.switch_to.window(driver.window_handles[-1])


# 1.1. Get years and links from 'Year to Year' page
# Scrape html from years table using selenium
try:
    # Wait for the table to be loaded 
    table = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'table.boxed'))
    )

    # Get HTML 
    table_html = table.get_attribute('outerHTML')
    # print(table_html) 

except TimeoutException:
    print("Timed-out waiting for the year list table.")


# 1.2. Convert relative linnks sto absolute 
try:
    # Keep base url to join with extracted later
    base_url = 'https://www.baseball-almanac.com/'

    # Parse scraped html using beautiful soup 
    soup = BeautifulSoup(table_html, 'html.parser')
    # print(soup)

    # Regular expression that matches exactly four digits 
    year_pattern = re.compile(r"^\d{4}$")

    # Extract links from scraped HTML 
    year_links = [
        (link.get_text(strip=True), urljoin(base_url, link["href"]))
        for link in soup.find_all("a", href=True)
        if year_pattern.match(link.get_text(strip=True))
]
    # # Preview the result 
    # for year, url in year_links:
    #     print(year, ": ", url)

    # Get links for last 5 years only
    # Step 1: Convert to int → find max year
    years_int = [int(year) for year, _ in year_links]
    last_year = max(years_int)

    # Step 2: Build set of last 5 years
    last_5_years = set(range(last_year - 4, last_year + 1))

    # Step 3: Filter original list
    filtered_links = [
        (year, url)
        for year, url in year_links
        if int(year) in last_5_years
    ]

    # Step 4: Sort if desired (e.g., from oldest to newest)
    filtered_links.sort(key=lambda tup: int(tup[0]), reverse=True) # newest first

    header_done = set()

    for year, url in filtered_links:
        # # Preview
        # print(f"{year} → {url}")
       
        # Scrape each year
        driver.get(url)
        driver.switch_to.window(driver.window_handles[-1])

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.container"))
            )

            soup = BeautifulSoup(driver.page_source, "html.parser")

            for table in soup.find_all("table", class_="boxed"):
                header_td = table.find("td", class_="header")
                if not header_td:
                    continue

                filename = make_csv_name(driver.current_url, header_td)
                if not filename:
                    continue

                # print("CSV filename would be:", filename)
                
                # Banner cells to headers 
                banner_cells = extract_unique_banners(table)
                print(filename, banner_cells)
                if not banner_cells:
                    continue 

                # Add Year column at the front
                # headers = ["Year"] + banner_cells

                # Datacol cells to data matrix
                data_cells = [td.get_text(strip=True) for td in table.find_all("td", class_ =lambda c: c and "datacol" in c)]
                width = len(banner_cells) # how many cols per row
                rows = [data_cells[i:i+width] for i in range(0, len(data_cells), width)]

                # Inject the year into each row (front or back must match headers)
                for r in rows:
                    r.insert(0, year) # year first

                # Write / append to CSV 
                fp = Path(filename)

                need_header = filename not in header_done
                with fp.open("a", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    if need_header:
                        w.writerow(["Year"] + banner_cells)
                        header_done.add(filename) # don't write it again
                    w.writerows(rows)

                # print(f"✓ {len(rows)} rows → {filename}")

        except Exception as e:
            print("Top‑level error:", e)

except Exception as e:
        print(f"{e}") 

# Get team menu link
try:
    team_link_el = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Team by Team"))
    )

    team_url = team_link_el.get_attribute('href')
    print("Team by Team link:", team_url)
except TimeoutException:
    print("link not found")

finally:
    driver.quit()
