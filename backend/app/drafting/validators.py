"""
Indian Legal Validators & Formatters (PRD §6.4 & §6.6)
======================================================
Strict, deterministic validators and formatters for Indian legal instruments:
- CIN (21 chars)
- DIN (8 digits)
- PAN (10 chars)
- GSTIN (15 chars)
- Indian Currency & Words Formatter (Lakhs, Crores)
- Cross-field and past-date validators
"""

import re
from datetime import date, datetime
from typing import Dict, Any, List, Optional, Tuple

CIN_REGEX = re.compile(r"^([LU])([0-9]{5})([A-Z]{2})([0-9]{4})([A-Z]{3})([0-9]{6})$")
DIN_REGEX = re.compile(r"^\d{8}$")
PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")


def validate_cin(cin_str: str) -> Tuple[bool, Optional[str]]:
    """Validates 21-character Corporate Identification Number."""
    if not cin_str:
        return False, "CIN is required."
    clean = cin_str.strip().upper()
    if not CIN_REGEX.match(clean):
        return False, "Invalid CIN format. Expected 21 characters: Listing (L/U), 5-digit industry, 2-letter state, 4-digit year, 3-letter type, 6-digit number (e.g. U72200MH2013PTC248912)."
    return True, None


def validate_din(din_str: str) -> Tuple[bool, Optional[str]]:
    """Validates 8-digit Director Identification Number."""
    if not din_str:
        return False, "DIN is required."
    clean = din_str.strip()
    if not DIN_REGEX.match(clean):
        return False, "Invalid DIN format. Expected exactly 8 numeric digits (e.g. 01234567)."
    return True, None


def validate_pan(pan_str: str) -> Tuple[bool, Optional[str]]:
    """Validates 10-character Permanent Account Number."""
    if not pan_str:
        return False, "PAN is required."
    clean = pan_str.strip().upper()
    if not PAN_REGEX.match(clean):
        return False, "Invalid PAN format. Expected 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F)."
    return True, None


def validate_gstin(gstin_str: str) -> Tuple[bool, Optional[str]]:
    """Validates 15-character GSTIN."""
    if not gstin_str:
        return False, "GSTIN is required."
    clean = gstin_str.strip().upper()
    if not GSTIN_REGEX.match(clean):
        return False, "Invalid GSTIN format. Expected 15 characters (e.g. 27ABCDE1234F1Z5)."
    return True, None


def validate_date_not_future(date_val: Any) -> Tuple[bool, Optional[str]]:
    """Validates that a date is not in the future."""
    if not date_val:
        return True, None
    parsed = None
    if isinstance(date_val, (date, datetime)):
        parsed = date_val.date() if isinstance(date_val, datetime) else date_val
    elif isinstance(date_val, str):
        try:
            parsed = datetime.fromisoformat(date_val.split("T")[0]).date()
        except Exception:
            return False, f"Invalid date string format: {date_val}"

    if parsed and parsed > date.today():
        return False, f"Date ({parsed.isoformat()}) cannot be in the future."
    return True, None


def format_indian_currency(amount: float | int) -> str:
    """Formats a numeric amount into Indian numbering system (e.g. ₹ 12,50,000)."""
    try:
        val = int(round(amount))
    except Exception:
        return f"₹ {amount}"

    s = str(abs(val))
    if len(s) <= 3:
        res = s
    else:
        last3 = s[-3:]
        remaining = s[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        res = ",".join(groups) + "," + last3

    prefix = "₹ " if val >= 0 else "-₹ "
    return prefix + res


def number_to_indian_words(num: int | float) -> str:
    """Converts a number to Indian legal currency words (Crores, Lakhs, Thousands, Rupees)."""
    try:
        n = int(round(num))
    except Exception:
        return ""

    if n == 0:
        return "Rupees Zero Only"

    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
             "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
             "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def _two_digits(val: int) -> str:
        if val < 20:
            return units[val]
        else:
            t = tens[val // 10]
            u = units[val % 10]
            return f"{t} {u}".strip()

    def _three_digits(val: int) -> str:
        h = val // 100
        rem = val % 100
        res = ""
        if h > 0:
            res += f"{units[h]} Hundred"
        if rem > 0:
            if res:
                res += " and "
            res += _two_digits(rem)
        return res

    words = []
    crore = n // 10000000
    n %= 10000000
    lakh = n // 100000
    n %= 100000
    thousand = n // 1000
    n %= 1000
    hundred = n

    if crore > 0:
        words.append(f"{_two_digits(crore)} Crore")
    if lakh > 0:
        words.append(f"{_two_digits(lakh)} Lakh")
    if thousand > 0:
        words.append(f"{_two_digits(thousand)} Thousand")
    if hundred > 0:
        words.append(_three_digits(hundred))

    return "Rupees " + " ".join(words).strip() + " Only"


def format_legal_date(date_val: Any) -> str:
    """Formats date into formal Indian legal format (e.g. 15th August 2024 or 15 August 2024)."""
    if not date_val:
        return ""
    if isinstance(date_val, str):
        try:
            d = datetime.fromisoformat(date_val.split("T")[0]).date()
        except Exception:
            return str(date_val)
    elif isinstance(date_val, datetime):
        d = date_val.date()
    elif isinstance(date_val, date):
        d = date_val
    else:
        return str(date_val)

    day = d.day
    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    month_name = d.strftime("%B")
    return f"{day}{suffix} {month_name} {d.year}"

