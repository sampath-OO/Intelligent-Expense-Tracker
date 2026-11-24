import os
import re
from datetime import datetime
from ml_engine import categorize_transaction

MONTH_NAMES = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"

DATE_PATTERNS = [
    # Month Day, Year (e.g. Nov 21, 2026 or Nov 21 2026)
    (rf"^({MONTH_NAMES})[a-z]*\s+(\d{{1,2}}),?\s+(\d{{4}})$", ["%b %d, %Y", "%b %d %Y"]),
    # Day Month Year (e.g. 21 Nov 2026 or 21-Nov-2026 or 21 Nov, 2026)
    (rf"^(\d{{1,2}})[-\s]({MONTH_NAMES})[a-z]*,?[-\s](\d{{4}})$", ["%d %b %Y", "%d-%b-%Y", "%d %b, %Y"]),
    # YYYY-MM-DD or YYYY/MM/DD
    (r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$", ["%Y-%m-%d", "%Y/%m/%d"]),
    # DD/MM/YYYY or DD-MM-YYYY or MM/DD/YYYY
    (r"^\d{1,2}[/-]\d{1,2}[/-]\d{4}$", ["%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"]),
    # DD/MM/YY or DD-MM-YY
    (r"^\d{1,2}[/-]\d{1,2}[/-]\d{2}$", ["%d/%m/%y", "%d-%m-%y"]),
    # DD-MMM-YY
    (rf"^(\d{{1,2}})[-\s]({MONTH_NAMES})[a-z]*[-\s](\d{{2}})$", ["%d-%b-%y", "%d %b %y"])
]

INLINE_DATE_PATTERNS = [
    (rf"\b(({MONTH_NAMES})[a-z]*\s+\d{{1,2}},?\s+\d{{4}})\b", ["%b %d, %Y", "%b %d %Y"]),
    (rf"\b(\d{{1,2}}[-\s]({MONTH_NAMES})[a-z]*,?[-\s]\d{{4}})\b", ["%d %b %Y", "%d-%b-%Y", "%d %b, %Y"]),
    (r"\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b", ["%Y-%m-%d", "%Y/%m/%d"]),
    (r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b", ["%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"]),
    (r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2})\b", ["%d/%m/%y", "%d-%m-%y"])
]

DISCARD_LINE_PREFIXES = (
    "Transaction ID", "UTR No", "Paid by", "Credited to", "XXXX", "Page ",
    "Date", "Transaction Details", "Type", "Amount", "This is a system",
    "This is an automatically", "Disclaimer", "Customer(s)", "terms-conditions",
    "Transaction Statement", "For any queries", "contact us at", "Balance",
    "Statement Period", "Account Holder", "Branch", "Currency"
)

def parse_date_str(date_str, is_exact=True):
    cleaned = date_str.strip()
    patterns = DATE_PATTERNS if is_exact else INLINE_DATE_PATTERNS
    for pat, formats in patterns:
        m = re.match(pat, cleaned, re.IGNORECASE) if is_exact else re.search(pat, cleaned, re.IGNORECASE)
        if m:
            val = m.group(0) if is_exact else m.group(1)
            val = val.replace(".", "/").replace(",", " ")
            val = re.sub(r"\s+", " ", val).strip()
            for fmt in formats:
                try:
                    dt = datetime.strptime(val, fmt.replace(",", " "))
                    if dt.year > 2090:
                        dt = dt.replace(year=dt.year - 100)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
    return None

def clean_amount_str(val):
    if not val or val == "-":
        return 0.0
    val_str = str(val).replace(",", "").replace("₹", "").replace("$", "").replace("€", "").replace("£", "").strip()
    val_str = re.sub(r"[a-zA-Z]", "", val_str).strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def clean_description(desc):
    if not desc:
        return "Transaction"
    d = desc
    d = re.sub(r"https?://\S+", "", d)
    d = re.sub(r"This is a (?:system|automatically) generated statement.*", "", d, flags=re.IGNORECASE)
    d = re.sub(r"Customer\(s\) are requested.*", "", d, flags=re.IGNORECASE)
    d = re.sub(r"of any errors in the statement.*", "", d, flags=re.IGNORECASE)
    d = re.sub(r"terms-conditions/.*", "", d, flags=re.IGNORECASE)
    d = re.sub(r"Disclaimer.*", "", d, flags=re.IGNORECASE)
    d = re.sub(r"Do not fall prey.*", "", d, flags=re.IGNORECASE)
    d = re.sub(r"Transaction ID.*", "", d, flags=re.IGNORECASE)
    d = re.sub(r"UTR No.*", "", d, flags=re.IGNORECASE)
    d = re.sub(r"[\-\_\*\|\#\:]+$", "", d).strip()
    d = re.sub(r"\s+", " ", d).strip()
    return d if d else "Transaction"

def detect_statement_metadata(text):
    meta = {
        "provider": "Digital Statement",
        "account": "N/A",
        "period": "Current Cycle"
    }
    text_lower = text.lower()

    if "phonepe" in text_lower:
        meta["provider"] = "PhonePe UPI Statement"
    elif "google pay" in text_lower or "gpay" in text_lower:
        meta["provider"] = "Google Pay UPI Statement"
    elif "paytm" in text_lower:
        meta["provider"] = "Paytm Statement"
    elif "state bank of india" in text_lower or "sbi" in text_lower:
        meta["provider"] = "State Bank of India (SBI)"
    elif "hdfc" in text_lower:
        meta["provider"] = "HDFC Bank Statement"
    elif "icici" in text_lower:
        meta["provider"] = "ICICI Bank Statement"
    elif "axis bank" in text_lower:
        meta["provider"] = "Axis Bank Statement"
    elif "apex bank" in text_lower:
        meta["provider"] = "Apex Bank Statement"

    m_acc = re.search(r"(?:statement for|account no\.?|a/c no\.?|account number:?)\s*([0-9xX]{6,16})", text, re.IGNORECASE)
    if m_acc:
        meta["account"] = m_acc.group(1).strip()

    m_per = re.search(r"(\d{1,2}\s+[A-Za-z]{3},?\s+\d{4}\s*-\s*\d{1,2}\s+[A-Za-z]{3},?\s+\d{4})", text)
    if not m_per:
        m_per = re.search(r"Statement Period:?\s*([0-9A-Za-z\s,-]+(?:to|-)[0-9A-Za-z\s,-]+)", text, re.IGNORECASE)
    if m_per:
        meta["period"] = m_per.group(1).strip()

    return meta

def extract_from_pdf(file_path):
    """
    Extracts transactions from ANY bank or UPI statement PDF (PhonePe, GPay, Paytm, SBI, HDFC, ICICI, etc.)
    """
    if not os.path.exists(file_path):
        return {
            "success": False,
            "transactions": [],
            "is_scanned": False,
            "message": "File not found."
        }

    extracted_text = ""
    pages_text = []

    # 1. Read PDF text using pdfplumber or pypdf
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text() or ""
                pages_text.append(txt)
                extracted_text += "\n" + txt
    except Exception:
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                txt = page.extract_text() or ""
                pages_text.append(txt)
                extracted_text += "\n" + txt
        except Exception as e2:
            return {
                "success": False,
                "transactions": [],
                "is_scanned": False,
                "message": f"Could not read PDF file: {str(e2)}"
            }

    # 2. Check for scanned / empty PDF
    clean_all = re.sub(r"\s+", "", extracted_text)
    if len(clean_all) < 25:
        return {
            "success": False,
            "transactions": [],
            "is_scanned": True,
            "message": "This PDF appears to be a scanned image or contains no selectable digital text. OCR support is not included in the initial version. Please upload a digital bank statement with selectable text."
        }

    lines = [line.strip() for line in extracted_text.split("\n") if line.strip()]
    metadata = detect_statement_metadata(extracted_text)

    # -------------------------------------------------------------
    # Strategy A: PhonePe / UPI & Alternating Block Parser
    # -------------------------------------------------------------
    i = 0
    phonepe_txs = []
    while i < len(lines):
        line = lines[i]
        parsed_date = parse_date_str(line, is_exact=True)
        if parsed_date and i + 2 < len(lines):
            offset = 1
            if re.match(r"^\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?$", lines[i + 1]):
                offset = 2

            entry_type = None
            amount = 0.0
            debit_empty = False
            desc_parts = []
            skip = offset

            for k in range(i + offset, min(i + offset + 10, len(lines))):
                cand = lines[k]
                if parse_date_str(cand, is_exact=True):
                    break

                cand_upper = cand.upper()
                if cand_upper in ("CREDIT", "DEBIT", "CR", "DR"):
                    entry_type = "income" if cand_upper in ("CREDIT", "CR") else "expense"
                    skip = max(skip, k - i + 1)
                elif cand == "-":
                    debit_empty = True
                    skip = max(skip, k - i + 1)
                elif (cand.startswith("₹") or re.match(r"^[0-9,]+(?:\.[0-9]{1,2})?$", cand.replace("₹", "").strip())) and not cand.startswith("XXXX"):
                    amt_val = clean_amount_str(cand)
                    if amt_val > 0 and amount == 0:
                        amount = amt_val
                        if debit_empty and not entry_type:
                            entry_type = "income"
                        skip = max(skip, k - i + 1)
                elif not any(cand.startswith(x) for x in DISCARD_LINE_PREFIXES):
                    desc_parts.append(cand)
                    skip = max(skip, k - i + 1)

            if amount > 0:
                raw_desc = " ".join(desc_parts)
                final_desc = clean_description(raw_desc)
                
                # Determine transaction type
                if not entry_type:
                    desc_l = final_desc.lower()
                    if any(k in desc_l for k in ["salary", "received from", "upi received", "deposit", "credit", "refund"]):
                        final_type = "income"
                    else:
                        final_type = "expense"
                else:
                    final_type = entry_type

                category = categorize_transaction(final_desc, final_type)

                phonepe_txs.append({
                    "date": parsed_date,
                    "description": final_desc,
                    "amount": round(amount, 2),
                    "type": final_type,
                    "category": category
                })

            i += max(1, skip)
        else:
            i += 1

    if len(phonepe_txs) >= 3:
        return {
            "success": True,
            "transactions": phonepe_txs,
            "metadata": metadata,
            "is_scanned": False,
            "message": f"Successfully extracted {len(phonepe_txs)} transactions from {metadata['provider']}."
        }

    # -------------------------------------------------------------
    # Strategy B: Standard Tabular Statement Parser
    # -------------------------------------------------------------
    i = 0
    table_txs = []
    while i < len(lines):
        line = lines[i]
        parsed_date = parse_date_str(line, is_exact=True)
        if parsed_date and i + 1 < len(lines):
            desc = lines[i + 1]
            amounts = []
            skip = 2

            for j in range(i + 2, min(i + 8, len(lines))):
                next_l = lines[j]
                if parse_date_str(next_l, is_exact=True):
                    break
                is_amt = next_l == "-" or bool(re.match(r"^[0-9,]+(?:\.[0-9]{1,2})?$", next_l.replace("₹", "").replace("$", "").strip()))
                if is_amt:
                    amounts.append(next_l)
                    skip = j - i + 1
                elif not amounts and not any(next_l.startswith(x) for x in DISCARD_LINE_PREFIXES):
                    desc += " " + next_l
                    skip = j - i + 1

            if amounts:
                tx_type = "expense"
                amount = 0.0

                if len(amounts) >= 2:
                    debit_val = clean_amount_str(amounts[0])
                    credit_val = clean_amount_str(amounts[1])
                    if credit_val > 0 and debit_val == 0:
                        tx_type = "income"
                        amount = credit_val
                    elif debit_val > 0:
                        tx_type = "expense"
                        amount = debit_val
                    else:
                        amount = max(debit_val, credit_val)
                elif len(amounts) == 1:
                    amount = clean_amount_str(amounts[0])
                    desc_lower = desc.lower()
                    if any(k in desc_lower for k in ["salary", "credit", "deposit", "refund"]):
                        tx_type = "income"

                if amount > 0:
                    clean_desc = clean_description(desc)
                    category = categorize_transaction(clean_desc, tx_type)
                    table_txs.append({
                        "date": parsed_date,
                        "description": clean_desc,
                        "amount": round(amount, 2),
                        "type": tx_type,
                        "category": category
                    })

            i += max(1, skip)
        else:
            i += 1

    if table_txs:
        return {
            "success": True,
            "transactions": table_txs,
            "metadata": metadata,
            "is_scanned": False,
            "message": f"Successfully extracted {len(table_txs)} transactions from {metadata['provider']} tables."
        }

    # -------------------------------------------------------------
    # Strategy C: Single-line Free-form Parser
    # -------------------------------------------------------------
    single_line_txs = []
    for line in lines:
        if any(line.startswith(x) for x in DISCARD_LINE_PREFIXES):
            continue

        parsed_date = None
        date_raw = None
        for pat, formats in INLINE_DATE_PATTERNS:
            m = re.search(pat, line, re.IGNORECASE)
            if m:
                p_date = parse_date_str(m.group(1), is_exact=False)
                if p_date:
                    parsed_date = p_date
                    date_raw = m.group(1)
                    break

        if not parsed_date:
            continue

        amounts = re.findall(r"(?:₹|\$|€|£)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})|[0-9]+(?:\.[0-9]{1,2}))", line)
        if not amounts:
            continue

        float_amts = [clean_amount_str(a) for a in amounts if clean_amount_str(a) > 0]
        if not float_amts:
            continue

        tx_amount = float_amts[0]
        line_lower = line.lower()
        is_credit = bool(re.search(r"\b(cr|credit|deposit|salary|refund|interest|stipend|received)\b", line_lower))
        is_debit = bool(re.search(r"\b(dr|debit|withdrawal|paid|payment|upi|pos|atm|purchase)\b", line_lower))

        tx_type = "income" if (is_credit and not is_debit) else "expense"

        desc_clean = line.replace(date_raw, "")
        for a in amounts:
            desc_clean = desc_clean.replace(a, "")
        desc_clean = re.sub(r"\b(cr|dr|credit|debit|inr|usd|eur)\b", "", desc_clean, flags=re.IGNORECASE)
        desc_clean = re.sub(r"[\/,\|\:\-\*\#]+", " ", desc_clean)
        desc_clean = clean_description(desc_clean)

        category = categorize_transaction(desc_clean, tx_type)
        single_line_txs.append({
            "date": parsed_date,
            "description": desc_clean[:100],
            "amount": round(tx_amount, 2),
            "type": tx_type,
            "category": category
        })

    if single_line_txs:
        return {
            "success": True,
            "transactions": single_line_txs,
            "metadata": metadata,
            "is_scanned": False,
            "message": f"Successfully extracted {len(single_line_txs)} transactions."
        }

    return {
        "success": False,
        "transactions": [],
        "is_scanned": False,
        "message": "No structured transactions could be detected in this PDF. Please check the file format or enter transactions manually."
    }
