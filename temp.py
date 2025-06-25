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

# warnings.simplefilter(action='ignore', category=ParserWarning)
# # ------------------------------------------------------------------
# # Standardize column names
# def std_col_names(df):
#     df.columns = df.columns.str.strip().str.lower().str.replace(".", "_").str.replace(" ", "_").str.replace("#", "no")
#     return df

# # Replace nonsence values with NaN
# def replace_nonsence(df):
#     df = df.replace(["To Be Determined", "--"], np.nan).copy()
#     return df

# # Drop nas
# def dropnas(df):
#     df = df.dropna().drop_duplicates().reset_index(drop=True)
#     return df

# # Convert a column to integer:
# def column_to_int(df, column_name):
#     df[column_name] = df[column_name].astype(int)
#     return df

# # Keep only digits
# def digits_only(df, column_name):
#     df[column_name] = df[column_name].astype(str).str.replace(r"\D", "", regex=True)
#     return df

# # Drop rows where a column has no digits
# def drop_non_digits(df, column_name):
#     mask_has_digits = df[column_name].astype(str).str.contains(r"\d")
#     df = df[mask_has_digits].reset_index(drop=True)
#     return df

# # Drop rows where one coli=unnm have specified value/values
# def drop_rows_w_value(df, column, value):
#     df = df[df[column] != value].reset_index(drop=True)
#     return df

# # Create separate dfs for future lookup table based on statistic column
# def create_lookup_df(df, column_name, new_column_name_1, new_column_name_2):
#     # Extract unique values
#     unique_vals = (
#         df[column_name]
#         .dropna()
#         .unique()
#     )
#     # Create lookup df
#     new_df = pd.DataFrame({
#         new_column_name_1: range(len(unique_vals)),
#         new_column_name_2: unique_vals
#     })
#     return new_df

# # Keep only rows where col starts with a letter
# def col_val_start_letter(df, columnn_name):
#     mask_starts_letter = df[columnn_name].astype(str).str.match(r"[A-Za-z]")
#     df = df[mask_starts_letter].reset_index(drop=True)
#     return df

# # Replace text column with fk
# def replace_txt_cloumn_with_fk(df1, df1_col1, df1_new_col, df2, df2_col1, df2_col2):
#     mask_not_digit = ~df1[df1_col1].str.match(r"^\d", na=False)
#     df_tmp = df1.loc[mask_not_digit]

#     # Now drop the rows where Statistic is NaN
#     df1 = (
#         df_tmp.dropna(subset=[df1_col1]).reset_index(drop=True)
#     )

#     # Keep only valid Statistic rows
#     #     • NOT starting with a digit
#     #     • NOT NaN
#     mask_valid = (
#         ~df1[df1_col1].str.match(r"^\d", na=False)
#     ) & (
#         df1[df1_col1].notna()
#     )

#     df1_col1 = (
#         df1_col1
#             .loc[mask_valid]
#             .reset_index(drop=True)
#     )

#     # Map Statistic → statistic_id
#     df_map = dict(zip(df2[df2_col1], df2[df2_col2]))

#     df1[df1_new_col] = (
#         df1[df1_col1]
#             .map(df_map)
#             .astype("int64")        # safe: no NaNs left after step 0
#     )

#     # Drop the text column
#     df1.drop(columns=[df1_col1], inplace=True)
#     return df1
# # ------------------------------------------------------------------

# Common scraping activity using selenium and BeautifulSoup
def scraping_page(url):
    try:
        # Load the web page
        driver.get(url)

        # Grab the surviving window handle (always the newest)
        driver.switch_to.window(driver.window_handles[-1])

        # Wait for the table to be loaded 
        div_container = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        # Get HTML 
        div_container_html = div_container.get_attribute('outerHTML')
        # print(table_html) 
    except TimeoutException:
        print("Timed-out waiting for the year list table.")

    # Parse scraped html using beautiful soup 
    try:
        soup = BeautifulSoup(div_container_html, 'html.parser')
        # print(soup)
        return soup

    except Exception as e:
            print(f"{e}") 
# ---------------------------------------------------------- #

# Scrape yearly statistics individual page
try:
    soup = scraping_page('https://www.baseball-almanac.com/yearly/yr2013a.shtml')
except Exception as e:
    print("ERROR: Scrape yearly statistics individual page")
    print(f"{e}")

# Find all tabls with class boxed
try:
    y_stat_tables = soup.find_all("table", class_="boxed")
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
    rows = []
    first_row = []
    y_stat_year = None
    y_stat_league = None
    y_stat_title = None

    trs = table.find_all('tr')

    for tr in trs:
        # Step 1: Header info (only once)
        header = tr.find('td', class_='header')
        if header and not y_stat_year:
            h2 = header.find('h2')
            if h2:
                text = h2.get_text(strip=True)
                year_match = re.search(r"^(\d{4})", text)
                league_match = re.search(r"^\d{4}\s+(\w+\s+\w+)", text)
                if year_match:
                    y_stat_year = year_match.group(1)
                if league_match:
                    y_stat_league = league_match.group(1)

            p = header.find('p')
            if p:
                stat_title_match = re.search(r"^(\w+\s+\w+)", p.get_text(strip=True))
                if stat_title_match:
                    y_stat_title = stat_title_match.group(1)

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
    df = pd.DataFrame(rows, columns=first_row[:len(rows[0])])  # Trim header if needed
    df['year'] = y_stat_year
    df['league'] = y_stat_league
    df['stat_title'] = y_stat_title

    return df

try:
    print(f"\n scrape_y_stat_table1 results:")
    y_stat_df_1 = scrape_stats_table(scrape_y_stat_table1)
    print(y_stat_df_1)

    print(f"\n scrape_y_stat_table2 results:")
    y_stat_df_2 = scrape_stats_table(scrape_y_stat_table2)
    print(y_stat_df_2)

except Exception as e:
    print("ERROR: Get tables titles")
    print(f"{e}") 

   

