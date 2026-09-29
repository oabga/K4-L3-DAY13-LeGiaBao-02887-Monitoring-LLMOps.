from __future__ import annotations

import hashlib
import re

PII_PATTERNS: dict[str, tuple[str, str]] = {
    "email": (r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]"),
    "phone_vn": (r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)", "[REDACTED_PHONE_VN]"),
    "cccd": (r"\b\d{12}\b", "[REDACTED_ID]"),
    "credit_card": (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "[REDACTED_CARD]"),
}


def scrub_text(text: str) -> str:
    safe = text
    for name, (pattern, replacement) in PII_PATTERNS.items():
        safe = re.sub(pattern, replacement, safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
