import json
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URL = "https://groww.in/mutual-funds/amc/groww-mutual-funds"

def parse_fund_size(size_str):
    # Extracts the numeric part of "₹169" or "₹169 Cr" for sorting
    matches = re.findall(r'[\d,]+(?:\.\d+)?', size_str)
    if matches:
        return float(matches[0].replace(',', ''))
    return 0.0

def scrape_amc_data():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")
        
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    data = {}

    # Extract Key Info
    key_info_section = soup.find("h2", string=lambda t: t and "Key information" in t)
    if key_info_section:
        table = key_info_section.find_next("table")
        if table:
            key_info = {}
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) == 2:
                    key = cols[0].text.strip()
                    val = cols[1].text.strip()
                    key_info[key] = val
            data["Key Information"] = key_info
            
            # Explicitly bubble up requested metrics
            data["AMC Age"] = key_info.get("AMC Age", "")
            data["AUM"] = key_info.get("Total AUM", "")
            data["No. Of Schemes"] = key_info.get("No. of schemes", "")

    # Extract 'How can you invest'
    invest_section = soup.find("h2", string=lambda t: t and "How can you invest" in t)
    if invest_section:
        content_div = invest_section.find_next("div")
        if content_div:
            data["How to Invest"] = content_div.text.strip()

    # Extract all Funds
    top_funds_section = soup.find("h2", string=lambda t: t and "List of" in t)
    funds = []
    if top_funds_section:
        table = top_funds_section.find_next("table")
        if table:
            headers = [th.text.strip() for th in table.find_all("th")]
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if cols:
                    fund_obj = {}
                    for i, col in enumerate(cols):
                        if i < len(headers):
                            # Try to extract the link if it's the Name column
                            if i == 0:
                                link = col.find('a')
                                if link and link.get('href'):
                                    fund_obj["URL"] = "https://groww.in" + link.get('href')
                            fund_obj[headers[i]] = col.text.strip()
                    funds.append(fund_obj)
    
    # Sort funds by AUM/Fund Size and pick top 5
    # The header is often "Fund Size (in Cr)" or similar.
    size_key = next((k for k in (funds[0].keys() if funds else []) if "Size" in k), "Fund Size (in Cr)")
    
    # Filter out funds without 'Fund Size' just in case
    funds_with_size = [f for f in funds if size_key in f and f[size_key]]
    
    # Sort descending
    funds_sorted = sorted(funds_with_size, key=lambda x: parse_fund_size(x[size_key]), reverse=True)
    top_5_funds = funds_sorted[:5]
    
    # Clean up the output to only what the user requested for the AMC overview page part
    clean_top_5 = []
    for f in top_5_funds:
        fund_name = next((f[k] for k in f.keys() if "Name" in k), "")
        perf_1y = next((f[k] for k in f.keys() if "1Y" in k), "")
        min_inv = "" # The AMC page table might not have Min Investment. We scrape what we can.
        f_size = f.get(size_key, "")
        
        clean_fund = {
            "Fund Name": fund_name,
            "1Y Returns": perf_1y,
            "AUM (Fund Size)": f_size,
            "URL": f.get("URL", "")
        }
        # Add all other parsed fields from the table for completeness
        clean_fund.update(f)
        clean_top_5.append(clean_fund)

    data["Top 5 Funds by AUM"] = clean_top_5

    with open("amc_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    scrape_amc_data()
    print("AMC data successfully written to amc_data.json")
