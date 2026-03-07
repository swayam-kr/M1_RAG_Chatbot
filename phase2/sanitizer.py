import re

# Strict Regex Patterns based on Indian formats
PAN_REGEX = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')
# Aadhaar can be 12 contiguous digits or space-separated 4 block digits
AADHAAR_REGEX = re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b|\b\d{12}\b')
# Bank accounts in India typically range from 9 to 18 digits. Let's target the core 11-16 to avoid false positives on small numbers.
BANK_ACCOUNT_REGEX = re.compile(r'\b\d{11,18}\b')

# Additional edge cases could be handled here.

def sanitize_text(text: str) -> str:
    """Takes a raw string and returns it strictly stripped of identifiable sequences."""
    if not isinstance(text, str):
        return text
        
    text = PAN_REGEX.sub("[REDACTED_PAN]", text)
    text = AADHAAR_REGEX.sub("[REDACTED_AADHAAR]", text)
    text = BANK_ACCOUNT_REGEX.sub("[REDACTED_BANK_ACC]", text)
    
    return text

def sanitize_json(data):
    """
    Recursively iterate through dictionaries and lists.
    When a string is found, pass it through the Regex Privacy Filter.
    """
    if isinstance(data, dict):
        return {k: sanitize_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json(item) for item in data]
    elif isinstance(data, str):
        return sanitize_text(data)
    else:
        return data
