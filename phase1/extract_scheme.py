import json
from bs4 import BeautifulSoup
import re

def extract_scheme_data(html):
    soup = BeautifulSoup(html, "html.parser")
    data = {}

    # 1. Scheme Name
    # As requested by the user, we ensure 'Scheme Name' avoids hallucinations by capturing it perfectly.
    # We will try both the h1 and the __NEXT_DATA__ fallback for maximum accuracy.
    script = soup.find("script", id="__NEXT_DATA__")
    next_data = {}
    if script:
        try:
            next_data = json.loads(script.string)
        except:
            pass
            
    mf_data = next_data.get("props", {}).get("pageProps", {}).get("mfServerSideData", {})
    scheme_name = mf_data.get("scheme_name", "")
    
    if not scheme_name:
        name_el = soup.find("h1", class_=lambda c: c and "header_schemeName" in c)
        scheme_name = name_el.text.strip() if name_el else ""
    
    data["Scheme Name"] = scheme_name

    # 2. Pills (Category, Subcategory, Risk)
    pills_container = soup.find("div", class_=lambda c: c and "pills_container" in c)
    if pills_container:
        pills = pills_container.find_all("div", class_=lambda c: c and "pill12Pill" in c)
        data["Tags"] = [p.text.strip() for p in pills]
    
    # 3. Fund Details (NAV, Min SIP, Expense Ratio)
    # Removing Fund size and Exit Load as they are already in the AMC overview data per user request
    details_container = soup.find("div", class_=lambda c: c and "fundDetails_fundDetailsContainer" in c)
    if details_container:
        blocks = details_container.find_all("div", class_=lambda c: c and "fundDetails_gap4" in c, recursive=False)
        for block in blocks:
            label_el = block.find("div", class_=lambda c: c and "contentTertiary" in c)
            val_el = block.find("div", class_=lambda c: c and "contentPrimary" in c)
            if label_el and val_el:
                label = label_el.text.strip().replace(":", "")
                val = val_el.text.strip()
                if "Fund size" in label:
                    continue # Skip Fund Size
                if "Expense ratio" in label:
                    label = "Expense ratio"
                data[label] = val

    # 4. Returns (1Y, 3Y, 5Y)
    returns = {}
    return_rows = soup.find_all("tr", class_=lambda c: c and "returnCalculator_tableRow" in c)
    for row in return_rows:
        cols = row.find_all("td")
        if len(cols) >= 5:
            period = cols[0].text.strip()
            ret_val = cols[4].text.strip()
            returns[period] = ret_val
    data["Returns"] = returns

    # 5. Top 5 Holdings
    holdings = []
    holdings_rows = soup.find_all("tr", class_=lambda c: c and "holdings_row" in c)
    for row in holdings_rows[:5]:
        cols = row.find_all("td")
        if len(cols) >= 4:
            h_name = cols[0].text.strip()
            h_sector = cols[1].text.strip()
            h_asset = cols[3].text.strip()
            holdings.append({
                "Name": h_name,
                "Sector": h_sector,
                "Allocation": h_asset
            })
    data["Top Holdings"] = holdings

    # 6. Fund Managers
    managers = []
    fm_section = soup.find("h3", string=lambda t: t and "Fund management" in t)
    if fm_section:
        manager_cards = fm_section.find_parent("div").find_all("div", class_=lambda c: c and "fundManagement_cardText" in c)
        for card in manager_cards:
            name_div = card.find("div", class_=lambda c: c and "fundManagement_personName" in c)
            if name_div:
                managers.append(name_div.text.strip())
    data["Fund Managers"] = managers

    # 7. Tax Implications (Excluding Exit Load explicitly as requested)
    tax_info = {}
    tax_sections = soup.find_all("div", class_=lambda c: c and "exitLoadStampDutyTax_section" in c)
    for section in tax_sections:
        heading = section.find("h4")
        content = section.find("div", class_="bodyBase contentSecondary")
        if heading and content:
            head_text = heading.text.strip()
            if "Exit load" not in head_text: 
                tax_info[head_text] = content.text.strip()
    data["Tax Implications"] = tax_info

    # 8. Advanced Ratios, Sector Allocation, Splits and Detailed Fund Managers (From __NEXT_DATA__)
    script = soup.find("script", id="__NEXT_DATA__")
    
    # Initialize basic values
    data["Sector Allocation"] = []
    data["Equity / Debt / Cash Split"] = {"Equity": "0.00%", "Debt": "0.00%", "Cash": "0.00%"}
    
    if script:
        try:
            next_data = json.loads(script.string)
            mf_data = next_data.get("props", {}).get("pageProps", {}).get("mfServerSideData", {})
            
            # --- Sector Allocation ---
            holdings_all = mf_data.get("holdings", [])
            sector_alloc = {}
            for h in holdings_all:
                sector = h.get("sector_name")
                alloc = h.get("corpus_per", 0)
                if sector: # Might be None for exact Equity/Debt classifications
                    sector_alloc[sector] = sector_alloc.get(sector, 0) + alloc
                    
            sector_alloc_sorted = sorted(sector_alloc.items(), key=lambda x: x[1], reverse=True)
            data["Sector Allocation"] = [{"Sector": s, "Allocation": f"{v:.2f}%"} for s, v in sector_alloc_sorted]

            # --- Equity / Debt / Cash Split ---
            equity_pct, debt_pct, cash_pct = 0.0, 0.0, 0.0
            
            for h in holdings_all:
                inst = h.get("instrument_name", "").lower()
                nature = h.get("nature_name", "").lower()
                alloc = h.get("corpus_per", 0)
                
                if "equity" in inst or "eq" in nature:
                    equity_pct += alloc
                elif "debt" in inst or "debt" in nature:
                    debt_pct += alloc
                else:
                    cash_pct += alloc
            
            # The holdings list might be partial or just Top N. The remaining balance to 100% is always Cash Equivalent.
            # But the UI dynamically shows sum of all holdings. Groww calculates the cash remainder explicitly.
            total_invested = equity_pct + debt_pct + cash_pct
            if total_invested < 100:
                cash_pct += (100.0 - total_invested)
                
            data["Equity / Debt / Cash Split"] = {
                "Equity": f"{equity_pct:.2f}%",
                "Debt": f"{debt_pct:.2f}%",
                "Cash": f"{cash_pct:.2f}%"
            }

            # --- Detailed Fund Managers ---
            # Replace the simple array with detailed array
            detailed_managers = []
            fm_details = mf_data.get("fund_manager_details", [])
            for fm in fm_details:
                detailed_managers.append({
                    "Name": fm.get("person_name", ""),
                    "Education": fm.get("education", ""),
                    "Experience": fm.get("experience", "")
                })
            
            if detailed_managers:
                data["Fund Managers"] = detailed_managers
                
        except Exception as e:
            pass

    return data

if __name__ == "__main__":
    with open("scheme_dump_pretty.html", "r", encoding="utf-8") as f:
        html = f.read()
    data = extract_scheme_data(html)
    with open("scheme_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Scheme data extracted to scheme_data.json")

