from urllib.parse import urlparse
from bs4 import BeautifulSoup, NavigableString
import re, csv, os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
page_url = "https://www.baseball-almanac.com/yearly/yr2024a.shtml"

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
# ------------------------------------------------------------------

driver.get(page_url)
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

        print("CSV filename would be:", filename)
        
        # Banner cells to headers 
        banner_cells = [td.get_text(strip=True) for td in table.find_all("td", class_="banner")]
        if not banner_cells:
            continue 

        # Add Year column at the front
        headers = ["Year"] + banner_cells

        # Datacol cells to data matrix
        data_cells = [td.get_text(strip=True) for td in table.find_all("td", class_ =lambda c: c and "datacol" in c)]
        width = len(banner_cells) # how many cols per row
        rows = [data_cells[i:i+width] for i in range(0, len(data_cells), width)]

        # Inject the year into each row (front or back must match headers)
        for r in rows:
            r.insert(0, year) # year first

        # Write / append to CSV 
        new_file = not Path(filename).exists()
        with open(filename, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(headers)
            w.writerows(rows)

        print(f"✓ {len(rows)} rows → {filename}")

except Exception as e:
    print("Top‑level error:", e)
finally:
    driver.quit()