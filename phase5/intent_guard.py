import re
from typing import Optional

# ── Investment advice / preference intent ─────────────────────────────────
ADVICE_KEYWORDS = [
    "should i invest", "is it good", "advice", "recommend", "best fund",
    "top fund", "compare", "better than", " vs ", "calculate",
    "how much will i get", "cagr calculation", "return if i invest",
    "which fund should", "is it worth", "good for me", "suit me",
    "my portfolio", "my risk", "my goal", "i want to invest",
    "i am looking to invest", "can i invest", "should i buy", "should i sell"
]

# ── PII detection (detect before sanitizer redacts them) ──────────────────
PII_PATTERNS = [
    re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'),                    # PAN
    re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b|\b\d{12}\b'),            # Aadhaar
    re.compile(r'\b\d{11,18}\b'),                                    # Bank account
    re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),  # Email
    re.compile(r'\b(\+91|91)?[6-9]\d{9}\b'),                        # Indian mobile
]

_ADVICE_PATTERNS = [
    re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
    for kw in ADVICE_KEYWORDS
]

# ── Canned responses ──────────────────────────────────────────────────────
HARDCODED_REFUSAL = (
    "I'm a factual FAQ assistant — I can't give financial advice, compare funds, "
    "or factor in personal investment goals. Please ask a specific factual question "
    "about a Groww Mutual Fund (e.g. expense ratio, NAV, exit load, fund manager)."
)

PII_REFUSAL = (
    "Your privacy matters to us. I've detected sensitive personal information "
    "(such as a PAN, Aadhaar, bank account, phone number, or email) in your message. "
    "I'm unable to process requests that include personal data. "
    "Please rephrase your question without any personal identifiers."
)

def _contains_pii(query: str) -> bool:
    for pattern in PII_PATTERNS:
        if pattern.search(query):
            return True
    return False

def _is_advice_intent(query: str) -> bool:
    for pattern in _ADVICE_PATTERNS:
        if pattern.search(query):
            return True
    return False

def guard_query(query: str) -> Optional[str]:
    """
    Returns a refusal string if the query is prohibited, None otherwise.
    PII check takes priority over advice check.
    """
    # PII check runs on the RAW (un-redacted) query
    if _contains_pii(query):
        return PII_REFUSAL
    if _is_advice_intent(query):
        return HARDCODED_REFUSAL
    return None

# Backwards compat alias
def is_prohibited_intent(query: str) -> bool:
    return guard_query(query) is not None
