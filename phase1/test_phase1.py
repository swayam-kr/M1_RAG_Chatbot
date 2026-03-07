import json
import os

def test_amc_data_exists_and_valid():
    assert os.path.exists("amc_data.json"), "amc_data.json not found."
    with open("amc_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert "Key Information" in data, "Key Information missing from AMC Data."
    assert "Top 5 Funds by AUM" in data, "Top 5 Funds by AUM missing from AMC Data."
    
    # Assert top 5 funds exist and are 5 in length
    top_funds = data["Top 5 Funds by AUM"]
    assert len(top_funds) == 5, f"Expected 5 top funds, found {len(top_funds)}."
    
    for fund in top_funds:
        assert "Fund Name" in fund, "Fund Name is missing in one of the funds."
        assert "URL" in fund, "URL is missing in one of the funds."
        assert "AUM (Fund Size)" in fund, "AUM (Fund Size) is missing."

def test_all_schemes_data_exists_and_valid():
    assert os.path.exists("all_schemes_data.json"), "all_schemes_data.json not found."
    with open("all_schemes_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert isinstance(data, list), "all_schemes_data.json should be a list of schemes."
    assert len(data) == 5, f"Expected 5 schemes, found {len(data)}."
    
    for scheme in data:
        assert "Scheme Name" in scheme and scheme["Scheme Name"], "Scheme Name missing or empty."
        
        # Test required Phase 1 output schemas
        assert "Fund Managers" in scheme, "Fund Managers missing from schema."
        assert isinstance(scheme["Fund Managers"], list), "Fund Managers must be a list."
        if len(scheme["Fund Managers"]) > 0:
            fm = scheme["Fund Managers"][0]
            assert "Name" in fm, "Fund Manager Name missing."
            assert "Experience" in fm, "Fund Manager Experience missing."
            assert "Education" in fm, "Fund Manager Education missing."
            
        assert "Tax Implications" in scheme, "Tax Implications missing."
        assert not any("Exit Load" in k for k in scheme["Tax Implications"].keys()), "Exit Load should not be in Tax Implications."
        
        # We initialized Sector Allocations dynamically
        assert "Sector Allocation" in scheme, "Sector Allocation missing."
        assert isinstance(scheme["Sector Allocation"], list), "Sector Allocation must be a list."
        
        # Equity Debt Cash Split explicitly expected
        assert "Equity / Debt / Cash Split" in scheme, "Asset split missing."
        split = scheme["Equity / Debt / Cash Split"]
        assert "Equity" in split, "Equity split part missing."
        assert "Debt" in split, "Debt split part missing."
        assert "Cash" in split, "Cash split part missing."
        
        assert "%" in split["Equity"] and "%" in split["Debt"] and "%" in split["Cash"], "Splits must be formatted as percentages."
        
        print(f"Verified schema for: {scheme.get('Scheme Name')}")
