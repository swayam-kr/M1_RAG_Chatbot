import json
from sanitizer import sanitize_json, sanitize_text

def test_sanitizer_flat_text():
    text = "My PAN is ABCDE1234F. Do not share it. My Aadhaar is 1234 5678 9012 and bank is 123456789012345."
    clean = sanitize_text(text)
    
    assert "[REDACTED_PAN]" in clean, "PAN was not redacted."
    assert "ABCDE1234F" not in clean, "Original PAN leaked."
    
    assert "[REDACTED_AADHAAR]" in clean, "Aadhaar was not redacted."
    assert "1234 5678 9012" not in clean, "Original Aadhaar leaked."
    
    assert "[REDACTED_BANK_ACC]" in clean, "Bank Account was not redacted."
    assert "123456789012345" not in clean, "Original Bank Account leaked."

def test_sanitizer_nested_json():
    mock_payload = {
        "Key Information": {
            "CEO": "Varun Gupta (PAN: ABCDE1234F)",
            "Contact": ["Phone 12345", "Aadhaar: 123456789012"]
        },
        "Nested Arrays": [
            [{"secret": "Bank: 9876543210987"}],
            "No secret here",
            "PAN: QWERT9876Y"
        ]
    }
    
    clean_json = sanitize_json(mock_payload)
    
    # Assert nested dicts
    assert "ABCDE1234F" not in clean_json["Key Information"]["CEO"]
    assert "[REDACTED_PAN]" in clean_json["Key Information"]["CEO"]
    
    assert "123456789012" not in clean_json["Key Information"]["Contact"][1]
    assert "[REDACTED_AADHAAR]" in clean_json["Key Information"]["Contact"][1]
    
    # Assert multidimensional nested arrays
    assert "9876543210987" not in clean_json["Nested Arrays"][0][0]["secret"]
    assert "[REDACTED_BANK_ACC]" in clean_json["Nested Arrays"][0][0]["secret"]
    
    assert "QWERT9876Y" not in clean_json["Nested Arrays"][2]
    assert "[REDACTED_PAN]" in clean_json["Nested Arrays"][2]
    
    print("All privacy tests passed securely!")

if __name__ == "__main__":
    test_sanitizer_flat_text()
    test_sanitizer_nested_json()
