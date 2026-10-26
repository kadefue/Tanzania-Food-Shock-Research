"""
NBS AASS (Tanzania National Bureau of Statistics) Data Dictionary Crawler
Catalog 52: https://microdata.nbs.go.tz/index.php/catalog/52/data-dictionary

Extracts:
- Data file / table names & descriptions
- Variable identifiers & labels
- First <h2> heading from Variable URL
- Value labels (codes and their meaning / categories)
- Question text, data type, format, and notes

Exports results to JSON, CSV, and Excel in 'nbs_aass_metadata/'.
"""

import os
import re
import time
import json
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

BASE_URL = "https://microdata.nbs.go.tz"
CATALOG_ID = "52"
DICT_START_URL = f"{BASE_URL}/index.php/catalog/{CATALOG_ID}/data-dictionary"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

session = requests.Session()
session.headers.update(HEADERS)


def get_soup(url, max_retries=3, delay=1.0):
    """Fetch URL with retries and return BeautifulSoup object."""
    if not url or not url.startswith("http"):
        return None

    for attempt in range(max_retries):
        try:
            resp = session.get(url, timeout=20)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "html.parser")
            elif resp.status_code == 404:
                return None
            time.sleep(delay * (attempt + 1))
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                print(f"[ERROR] Failed to fetch {url}: {e}")
                return None
            time.sleep(delay * (attempt + 1))
    return None


def get_data_file_links(start_url):
    """
    Find all dataset/file links under the Data Dictionary sidebar/list.
    """
    print(f"[*] Accessing main Data Dictionary page: {start_url}")
    soup = get_soup(start_url)
    if not soup:
        print("[!] Could not load main data dictionary page.")
        return []

    file_links = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full_url = urljoin(start_url, href)

        is_dict_link = (
            f"/catalog/{CATALOG_ID}/data-dictionary" in full_url
            or f"/catalog/{CATALOG_ID}/data_dictionary" in full_url
        )
        if is_dict_link and full_url not in seen_urls:
            title = a.get_text(strip=True)
            if full_url.rstrip("/") != start_url.rstrip("/"):
                seen_urls.add(full_url)
                file_links.append({"name": title, "url": full_url})

    if not file_links:
        file_links.append({"name": "Default Data File", "url": start_url})

    print(f"[+] Found {len(file_links)} data file link(s).")
    return file_links


def parse_variable_detail(var_url):
    """
    Visit individual variable page to extract:
    - First <h2> tag text
    - Comprehensive metadata, definitions, questions, and category value codes
    """
    soup = get_soup(var_url)
    if not soup:
        return {}

    # 1. Extract first <h2> text
    first_h2_tag = soup.find("h2")
    h2_text = first_h2_tag.get_text(strip=True) if first_h2_tag else ""

    details = {
        "h2_header": h2_text,
        "variable_url": var_url,
        "question": "",
        "data_type": "",
        "format": "",
        "definition": "",
        "categories": [],  # List of {"code": ..., "label": ..., "frequency": ...}
    }

    # 2. Extract table of categories/value labels if present
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if any(h in headers for h in ["value", "category", "label", "cases", "code"]):
            rows = table.find_all("tr")
            for tr in rows[1:]:
                cols = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cols) >= 2:
                    code = cols[0]
                    label = cols[1]
                    freq = cols[2] if len(cols) > 2 else ""
                    details["categories"].append({
                        "code": code,
                        "label": label,
                        "frequency": freq,
                    })

    # 3. Extract field definitions (Questions, Notes, Concept)
    for row in soup.find_all(["tr", "div", "dl"]):
        text = row.get_text(" ", strip=True)
        if "Literal question" in text or "Question:" in text:
            details["question"] = text.replace("Literal question", "").replace("Question:", "").strip()
        elif "Type:" in text or "Data type" in text:
            details["data_type"] = text.replace("Type:", "").replace("Data type", "").strip()
        elif "Format:" in text:
            details["format"] = text.replace("Format:", "").strip()
        elif "Definition:" in text or "Description:" in text:
            details["definition"] = text.replace("Definition:", "").replace("Description:", "").strip()

    return details


def crawl_data_file(file_info):
    """
    Crawl a data file page, extract all variables and their links.
    """
    file_name = file_info["name"]
    file_url = file_info["url"]
    soup = get_soup(file_url)
    if not soup:
        return []

    variables = []
    seen_vars = set()

    # Look for variable tables or links to variable descriptions
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full_url = urljoin(file_url, href)

        if f"/catalog/{CATALOG_ID}/variable" in full_url and full_url not in seen_vars:
            seen_vars.add(full_url)
            var_name = a.get_text(strip=True)

            var_label = ""
            tr = a.find_parent("tr")
            if tr:
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) > 1:
                    var_label = cells[1] if cells[0] == var_name else cells[0]

            variables.append({
                "file_name": file_name,
                "file_url": file_url,
                "variable_name": var_name,
                "variable_label": var_label,
                "variable_url": full_url,
            })

    # Fallback to summary table if individual links not structured with /variable/
    if not variables:
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) >= 2:
                name = tds[0].get_text(strip=True)
                label = tds[1].get_text(strip=True)
                if name and not name.lower().startswith("name"):
                    variables.append({
                        "file_name": file_name,
                        "file_url": file_url,
                        "variable_name": name,
                        "variable_label": label,
                        "variable_url": file_url,
                    })

    return variables


def main():
    print("=" * 60)
    print("  NBS Microdata Catalog 52 Data Dictionary Crawler")
    print("=" * 60)

    # 1. Collect all data files listed under Dictionary
    file_links = get_data_file_links(DICT_START_URL)
    if not file_links:
        print("[!] No dictionary links discovered. Exiting.")
        return

    all_variables = []

    # 2. Iterate each data file and find its variables
    print("\n[*] Extracting variables for each data file...")
    for file_info in tqdm(file_links, desc="Files"):
        vars_in_file = crawl_data_file(file_info)
        all_variables.extend(vars_in_file)
        time.sleep(0.3)

    print(f"[+] Total variables discovered: {len(all_variables)}")

    # 3. For each variable, open its detailed link to extract <h2> and metadata
    print("\n[*] Crawling detailed variable definitions, <h2> headers, and value codes...")
    detailed_data = []

    # Cache details by URL to avoid re-fetching duplicate variable links
    details_cache = {}

    for v in tqdm(all_variables, desc="Variables"):
        var_url = v.get("variable_url", "")
        if var_url and "/variable/" in var_url:
            if var_url not in details_cache:
                details_cache[var_url] = parse_variable_detail(var_url)
                time.sleep(0.2)
            var_detail = details_cache[var_url]
        else:
            var_detail = {}

        combined = {
            "File Name": v.get("file_name", ""),
            "Variable Name": v.get("variable_name", ""),
            "H2 Header": var_detail.get("h2_header", ""),
            "Variable Label": v.get("variable_label", ""),
            "Question": var_detail.get("question", ""),
            "Definition": var_detail.get("definition", ""),
            "Data Type": var_detail.get("data_type", ""),
            "Format": var_detail.get("format", ""),
            "Value Codes & Labels": "; ".join(
                f"{c['code']} = {c['label']}"
                for c in var_detail.get("categories", [])
            ),
            "Raw Categories": var_detail.get("categories", []),
            "File URL": v.get("file_url", ""),
            "Variable URL": v.get("variable_url", ""),
        }
        detailed_data.append(combined)

    # 4. Save results to JSON, CSV, and Excel
    output_dir = "nbs_aass_metadata"
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, "data_dictionary_catalog_52.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(detailed_data, f, indent=2, ensure_ascii=False)
    print(f"\n[✓] Saved complete JSON to: {json_path}")

    # Prepare DataFrame for Excel/CSV export
    df_rows = []
    for item in detailed_data:
        row = dict(item)
        if "Raw Categories" in row:
            del row["Raw Categories"]
        df_rows.append(row)

    df = pd.DataFrame(df_rows)

    preferred_order = [
        "File Name",
        "Variable Name",
        "H2 Header",
        "Variable Label",
        "Question",
        "Definition",
        "Data Type",
        "Format",
        "Value Codes & Labels",
        "File URL",
        "Variable URL",
    ]
    cols = [c for c in preferred_order if c in df.columns] + [
        c for c in df.columns if c not in preferred_order
    ]
    df = df[cols]

    csv_path = os.path.join(output_dir, "data_dictionary_catalog_52.csv")
    excel_path = os.path.join(output_dir, "data_dictionary_catalog_52.xlsx")

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_excel(excel_path, index=False)

    print(f"[✓] Saved CSV to: {csv_path}")
    print(f"[✓] Saved Excel to: {excel_path}")
    print("\nCrawling completed successfully!")


if __name__ == "__main__":
    main()