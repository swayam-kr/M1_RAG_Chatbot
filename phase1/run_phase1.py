import json
import time
from playwright.sync_api import sync_playwright
from extract_scheme import extract_scheme_data
from scraper import scrape_amc_data

def run_phase1():
    print("Step 1: Scraping AMC Overview and fetching Top 5 Funds...")
    scrape_amc_data()
    
    with open("amc_data.json", "r", encoding="utf-8") as f:
        amc_data = json.load(f)
        
    top_funds = amc_data.get("Top 5 Funds by AUM", [])
    if not top_funds:
        print("No top funds found in amc_data.json!")
        return

    all_schemes = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for fund in top_funds:
            url = fund.get("URL")
            name = fund.get("Fund Name")
            if not url:
                print(f"Skipping {name} - No URL provided")
                continue
                
            print(f"Step 2: Fetching HTML for {name} ({url})...")
            try:
                page.goto(url, wait_until="networkidle")
                time.sleep(1) # Extra buffer for JS hydration
                html = page.content()
                
                print(f"Step 3: Extracting scheme details for {name}...")
                scheme_data = extract_scheme_data(html)
                all_schemes.append(scheme_data)
                
            except Exception as e:
                print(f"Error processing {name}: {e}")
                
        browser.close()
        
    print(f"Successfully processed {len(all_schemes)} schemes.")
    
    with open("all_schemes_data.json", "w", encoding="utf-8") as f:
        json.dump(all_schemes, f, indent=2, ensure_ascii=False)
        
    print("Done! Phase 1 pipeline completed. See 'all_schemes_data.json' and 'amc_data.json'.")

if __name__ == "__main__":
    run_phase1()
