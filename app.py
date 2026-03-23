import re
import time
import zipfile
from io import BytesIO
from collections import Counter

import pandas as pd
import pdfplumber
import streamlit as st
import streamlit.components.v1 as components


# =========================
# Access Settings
# =========================
ENABLE_EXPIRY = False  # True = locked, False = open

st.set_page_config(page_title="Webtool", layout="wide")

if ENABLE_EXPIRY:
    st.markdown(
        """
        <div style="
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 80vh;
            text-align: center;
        ">
            <h1 style="color: #e74c3c; font-size: 48px;">
                ⛔ Access Stopped!
            </h1>
            <p style="font-size: 20px; color: #555;">
                This application is currently unavailable.
            </p>
            <p style="font-size: 16px; color: #888;">
                Please contact the developer (JBI).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


# =========================
# JB Wake-up Intro
# =========================
sleep_html = """
<!DOCTYPE html>
<html>
<head>
<style>
    body {
        margin: 0;
        background: #eef3f9;
        font-family: Arial, sans-serif;
    }

    .wrap {
        height: 72vh;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .scene {
        text-align: center;
        color: #333;
    }

    .sleep {
        font-size: 38px;
        color: #6b7c93;
        margin-bottom: 16px;
        animation: floatzzz 1.6s ease-in-out infinite;
    }

    .bed {
        position: relative;
        width: 280px;
        height: 150px;
        margin: 0 auto 20px auto;
    }

    .mattress {
        position: absolute;
        bottom: 10px;
        left: 12px;
        width: 255px;
        height: 95px;
        background: #d9e6f2;
        border-radius: 18px;
        border: 3px solid #b8cde0;
    }

    .pillow {
        position: absolute;
        left: 28px;
        top: 28px;
        width: 58px;
        height: 36px;
        background: #ffffff;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }

    .blanket {
        position: absolute;
        bottom: 18px;
        left: 82px;
        width: 135px;
        height: 52px;
        background: #8bb7f0;
        border-radius: 24px;
        animation: blanket-breathe 1.8s ease-in-out infinite;
    }

    .jb-head {
        position: absolute;
        left: 62px;
        top: 38px;
        width: 34px;
        height: 34px;
        background: #f2c9a5;
        border-radius: 50%;
        border: 2px solid #d9a97e;
        z-index: 2;
    }

    .jb-hair {
        position: absolute;
        left: 64px;
        top: 33px;
        width: 34px;
        height: 16px;
        background: #2b2b2b;
        border-radius: 16px 16px 8px 8px;
        z-index: 3;
    }

    .title {
        font-size: 28px;
        font-weight: 700;
        color: #1f4e79;
        margin-top: 10px;
    }

    .sub {
        font-size: 16px;
        color: #666;
        margin-top: 6px;
    }

    .app-box {
        margin: 18px auto 0 auto;
        display: inline-block;
        padding: 12px 20px;
        background: #e8f4ea;
        color: #1d6b3b;
        border: 1px solid #b9dfc1;
        border-radius: 12px;
        font-weight: 600;
        animation: pulse 1.4s ease-in-out infinite;
    }

    @keyframes blanket-breathe {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-4px); }
    }

    @keyframes floatzzz {
        0%, 100% { transform: translateY(0px); opacity: 0.7; }
        50% { transform: translateY(-8px); opacity: 1; }
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); box-shadow: 0 0 0 rgba(29,107,59,0.0); }
        50% { transform: scale(1.04); box-shadow: 0 0 18px rgba(29,107,59,0.15); }
    }
</style>
</head>
<body>
    <div class="wrap">
        <div class="scene">
            <div class="sleep">😴 Zzz... Zzz...</div>

            <div class="bed">
                <div class="mattress"></div>
                <div class="pillow"></div>
                <div class="jb-head"></div>
                <div class="jb-hair"></div>
                <div class="blanket"></div>
            </div>

            <div class="title">JBI is sleeping...</div>
            <div class="sub">JBI is waking to start the PO Generator.</div>
            <div class="app-box">Initializing Purchase Order Extractor...</div>
        </div>
    </div>
</body>
</html>
"""

wake_html = """
<!DOCTYPE html>
<html>
<head>
<style>
    body {
        margin: 0;
        background: #eef3f9;
        font-family: Arial, sans-serif;
    }

    .wrap {
        height: 72vh;
        display: flex;
        justify-content: center;
        align-items: center;
        text-align: center;
    }

    .emoji {
        font-size: 70px;
        margin-bottom: 10px;
        animation: bounce 1s ease-in-out infinite;
    }

    .title {
        font-size: 32px;
        font-weight: 700;
        color: #1f4e79;
        margin-bottom: 10px;
    }

    .sub {
        font-size: 18px;
        color: #555;
    }

    @keyframes bounce {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
</style>
</head>
<body>
    <div class="wrap">
        <div>
            <div class="emoji">😳</div>
            <div class="title">JBI woke up!</div>
            <div class="sub">Powering PO Generator...</div>
        </div>
    </div>
</body>
</html>
"""

intro_placeholder = st.empty()

with intro_placeholder.container():
    components.html(sleep_html, height=700)

time.sleep(2.2)

with intro_placeholder.container():
    components.html(wake_html, height=420)

time.sleep(1.2)
intro_placeholder.empty()


st.title("Purchase Order Extractor")


# =========================
# Helpers
# =========================
def clean_space(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def extract_po_from_filename(name: str) -> str:
    m = re.search(r"\bPOR\d{6,12}\b", (name or "").upper())
    return m.group(0) if m else ""


def normalize_po(po: str) -> str:
    m = re.search(r"\bPOR\d{6,12}\b", (po or "").upper())
    return m.group(0) if m else ""


def is_number(token: str) -> bool:
    return bool(re.fullmatch(r"\d+(\.\d+)?", token or ""))


def is_money(token: str) -> bool:
    t = (token or "").replace(",", "")
    return bool(re.fullmatch(r"\d+(\.\d{1,8})?", t))


def to_float(token: str) -> float:
    return float((token or "0").replace(",", ""))


def fix_uom(uom: str) -> str:
    u = (uom or "").upper().strip()
    return re.sub(r"\d+$", "", u)


def keep_best_nonblank(existing: str, new: str) -> str:
    existing = clean_space(existing)
    new = clean_space(new)
    if not new:
        return existing
    if not existing:
        return new
    return new if len(new) > len(existing) else existing


# =========================
# Description cleaning (context-aware)
# =========================
PACK_WORD_RE = re.compile(
    r"(bottle|btl|btls?|case|pack|packs|pcs?|pc|sachet|box|carton|tray|can|jar|pouch|tub)",
    flags=re.I,
)
UNIT_RE = re.compile(r"^(kg|g|gram|grams|ml|l|ltr|liter|liters)$", flags=re.I)


def is_size_token(tok: str) -> bool:
    # 250ml, 1L, 500g, 1.5L
    t = (tok or "").upper()
    return bool(re.fullmatch(r"\d+(\.\d+)?(ML|L|G|KG)\b", t))


def clean_desc_line(line: str) -> str:
    line = clean_space(line)
    if not line:
        return ""

    # whole-line single letter junk
    if re.fullmatch(r"[A-Z]", line):
        return ""

    # trailing single-letter junk at end only
    line = re.sub(r"\s+\b[A-Z]\b$", "", line)

    # optional OCR-ish fix
    line = re.sub(r"\b1L\s+8\b", "1L x", line, flags=re.I)

    return clean_space(line)


def clean_description_tokens(desc_tokens: list[str]) -> str:
    """
    Remove stray 'No.' column numbers from DESCRIPTION only, without breaking:
      - 2 kg, 12 kg
      - 1L x 12
      - 12 bottle/case
      - 0% / 0 % (percentage)
    """
    kept = []
    for i, t in enumerate(desc_tokens):
        prev = desc_tokens[i - 1] if i > 0 else ""
        nxt = desc_tokens[i + 1] if i + 1 < len(desc_tokens) else ""

        t_low = t.lower()
        prev_low = prev.lower()
        nxt_low = nxt.lower()

        # keep multiplier tokens
        if t_low in {"x", "×"}:
            kept.append(t)
            continue

        # standalone integer token
        if re.fullmatch(r"\d{1,3}", t):
            # KEEP percent split like "0 %"
            if nxt and (nxt == "%" or nxt.startswith("%")):
                kept.append(t)
                continue

            # KEEP measurement: "12 kg"
            if nxt and UNIT_RE.match(nxt):
                kept.append(t)
                continue

            # KEEP packaging ONLY if next token STARTS with a word-pack token
            # (so "12 bottle/case" is kept, but "4 1.5Lx12bottle/case" removes 4)
            if nxt and PACK_WORD_RE.search(nxt) and not re.match(r"^\d", nxt):
                kept.append(t)
                continue

            # KEEP multiplier pattern: "x 12" or "12 x"
            if prev_low in {"x", "×"} or nxt_low in {"x", "×"}:
                kept.append(t)
                continue

            # KEEP if prev is size and next is word-pack: "1L 12 bottle"
            if prev and is_size_token(prev) and nxt and PACK_WORD_RE.search(nxt) and not re.match(r"^\d", nxt):
                kept.append(t)
                continue

            # Otherwise: likely "No." artifact -> drop
            continue

        kept.append(t)

    return clean_space(" ".join(kept))


def is_pack_line(line: str) -> bool:
    """
    True when the line looks like a packaging descriptor line like:
      - bottle/case
      - sachet/box
      - pcs/case
    """
    if not line:
        return False
    if re.match(r"^\d", line):
        return False
    return bool(PACK_WORD_RE.search(line))


# =========================
# PDF text extraction (BYTES-safe)
# =========================
def extract_lines_from_pdf_bytes(pdf_bytes: bytes) -> list[str]:
    lines = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for ln in text.splitlines():
                ln = clean_space(ln)
                if ln:
                    lines.append(ln)
    return lines


# =========================
# Header parsing
# =========================
DATE_PATTERN = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}"


def parse_ship_to_first(lines: list[str]) -> str:
    header_re = re.compile(r"Ship-?\s*to\s*Address", flags=re.I)
    stop_re = re.compile(
        r"(Acknowledgement|THIS DOCUMENT IS NOT VALID|VAT Amount|Series Range|Date Issued|VAT Invoice|Total PHP|Invoice Discount)",
        flags=re.I,
    )

    for i, line in enumerate(lines):
        line = clean_space(line)
        if not line:
            continue

        if header_re.search(line):
            m = re.search(r"Ship-?\s*to\s*Address\s*:?\s*(.+)$", line, flags=re.I)
            if m:
                candidate = clean_space(m.group(1))
                if candidate and not stop_re.search(candidate):
                    return candidate

            j = i + 1
            while j < len(lines):
                nxt = clean_space(lines[j])
                if not nxt:
                    j += 1
                    continue
                if stop_re.search(nxt):
                    return ""
                if re.match(r"^(Unit\b|Address\b|City\b|Province\b|Barangay\b)", nxt, flags=re.I):
                    j += 1
                    continue
                return nxt

    return ""


def extract_order_no_best_effort(lines: list[str]) -> str:
    for i, ln in enumerate(lines):
        if re.search(r"\bOrder\s*No\b", ln, flags=re.I):
            for j in range(i, min(i + 20, len(lines))):
                m = re.search(r"\b(POR\d{6,12})\b", lines[j], flags=re.I)
                if m:
                    return m.group(1).upper()

    hits = []
    for ln in lines:
        if re.search(r"Series\s*Range", ln, flags=re.I):
            continue
        hits.extend(re.findall(r"\bPOR\d{6,12}\b", ln, flags=re.I))

    hits = [h.upper() for h in hits]
    if not hits:
        return ""
    return Counter(hits).most_common(1)[0][0]


def parse_header(lines: list[str]) -> dict:
    text = "\n".join(lines)
    header = {"Order No": "", "Document Date": "", "Delivery Date": "", "Ship To": ""}

    header["Order No"] = extract_order_no_best_effort(lines)

    m = re.search(r"Document Date\s+(" + DATE_PATTERN + r")", text)
    if m:
        header["Document Date"] = clean_space(m.group(1))

    m = re.search(r"Delivery Date\s+(" + DATE_PATTERN + r")", text)
    if m:
        header["Delivery Date"] = clean_space(m.group(1))

    header["Ship To"] = parse_ship_to_first(lines)
    return header


# =========================
# Item parsing
# =========================
STOP_SECTION_RE = re.compile(
    r"(VAT Amount Specification|VAT Invoice|12%\s*VAT|Total PHP|Total\s+\d|Invoice Discount|Acknowledgement Certificate|THIS DOCUMENT IS NOT VALID|Ship-?\s*to\s*Address)",
    flags=re.I,
)
ITEM_START_RE = re.compile(r"^(A\d{7,}|NF\d+)\b", flags=re.I)


def parse_items(lines: list[str]) -> list[dict]:
    items = []
    i = 0

    while i < len(lines):
        line = clean_space(lines[i])

        if not line or STOP_SECTION_RE.search(line):
            i += 1
            continue

        if not ITEM_START_RE.match(line):
            i += 1
            continue

        tokens = line.split()
        code = tokens[0]

        # skip tiny digits right after item code (No. column leak)
        start_desc_idx = 1
        if len(tokens) > 1 and re.fullmatch(r"\d{1,3}", tokens[1]):
            start_desc_idx = 2

        # qty index = first numeric token after desc start
        qty_index = None
        for idx in range(start_desc_idx, len(tokens)):
            if is_number(tokens[idx]):
                qty_index = idx
                break

        if qty_index is None or qty_index + 2 >= len(tokens):
            i += 1
            continue

        qty = float(tokens[qty_index])
        uom = fix_uom(tokens[qty_index + 1])

        if not is_money(tokens[qty_index + 2]):
            i += 1
            continue
        unit_cost = to_float(tokens[qty_index + 2])

        amount = None
        for tok in reversed(tokens):
            if is_money(tok):
                amount = to_float(tok)
                break

        # description tokens before qty
        desc_tokens = tokens[start_desc_idx:qty_index]
        desc_first = clean_desc_line(clean_description_tokens(desc_tokens))

        desc_parts = []
        if desc_first:
            desc_parts.append(desc_first)

        i += 1

        # continuation lines
        while i < len(lines):
            nxt = clean_space(lines[i])

            if not nxt:
                i += 1
                continue
            if STOP_SECTION_RE.search(nxt):
                break
            if ITEM_START_RE.match(nxt):
                break

            # merge trailing number with next packaging line
            m_trailing_num = re.search(r"(?:^|\s)(\d{1,3})$", nxt)
            nxt2 = clean_space(lines[i + 1]) if (i + 1 < len(lines)) else ""
            if m_trailing_num and nxt2 and is_pack_line(nxt2):
                combined = f"{nxt} {nxt2}"
                combined = clean_desc_line(combined)
                if combined:
                    combined = clean_description_tokens(combined.split())
                    if combined:
                        desc_parts.append(combined)
                i += 2
                continue

            # numeric-only line handling (pack-size vs item-no)
            if re.fullmatch(r"\d{1,3}", nxt):
                # Keep ONLY when next line starts with a WORD-packaging line
                if nxt2 and is_pack_line(nxt2):
                    desc_parts.append(nxt)
                    i += 1
                    continue

                i += 1
                continue

            cleaned = clean_desc_line(nxt)
            if cleaned:
                cleaned = clean_description_tokens(cleaned.split())
                if cleaned:
                    desc_parts.append(cleaned)

            i += 1

        full_desc = clean_space(" ".join(desc_parts))
        full_desc = re.split(
            r"(12%\s*VAT|VAT Invoice|VAT Amount|Total PHP|VAT Amount Specification|Acknowledgement)",
            full_desc,
            flags=re.I,
        )[0].strip()

        items.append(
            {
                "Item Code": code,
                "Full Description": full_desc,
                "Quantity": qty,
                "Unit of Measure": uom,
                "Direct Unit Cost": unit_cost,
                "Amount": amount,
            }
        )

    return items


# =========================
# Main
# =========================
uploaded_files = st.file_uploader(
    "Upload TBG Purchase Order PDF(s)",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_files:
    uploads = [{"name": f.name, "bytes": f.getvalue()} for f in uploaded_files]

    per_pdf = []
    best_header_by_po = {}
    orphan_ship_files = []

    # PASS 1
    for up in uploads:
        lines = extract_lines_from_pdf_bytes(up["bytes"])
        header = parse_header(lines)
        items = parse_items(lines)

        po_raw = clean_space(header.get("Order No", "")) or extract_po_from_filename(up["name"])
        po_key = normalize_po(po_raw)
        ship = clean_space(header.get("Ship To", ""))

        per_pdf.append(
            {
                "name": up["name"],
                "po_raw": po_raw,
                "po_key": po_key,
                "header": header,
                "items": items,
            }
        )

        if not po_key:
            if ship:
                orphan_ship_files.append({"name": up["name"], "ship_to": ship})
            continue

        prev = best_header_by_po.get(
            po_key,
            {"Order No": po_raw, "Document Date": "", "Delivery Date": "", "Ship To": ""},
        )
        prev["Ship To"] = keep_best_nonblank(prev.get("Ship To", ""), ship)

        if clean_space(header.get("Document Date", "")) and not prev["Document Date"]:
            prev["Document Date"] = header["Document Date"]
        if clean_space(header.get("Delivery Date", "")) and not prev["Delivery Date"]:
            prev["Delivery Date"] = header["Delivery Date"]

        if not clean_space(prev.get("Order No", "")) and po_raw:
            prev["Order No"] = po_raw

        best_header_by_po[po_key] = prev

    # SAFE orphan attach (optional)
    pos_missing_ship = [k for k, v in best_header_by_po.items() if not clean_space(v.get("Ship To", ""))]
    if len(orphan_ship_files) == 1 and len(pos_missing_ship) == 1:
        target_po = pos_missing_ship[0]
        best_header_by_po[target_po]["Ship To"] = keep_best_nonblank(
            best_header_by_po[target_po].get("Ship To", ""),
            orphan_ship_files[0]["ship_to"],
        )

    ship_map = {k: clean_space(v.get("Ship To", "")) for k, v in best_header_by_po.items()}

    # PASS 2
    all_rows = []
    for rec in per_pdf:
        po_key = rec["po_key"]
        best = best_header_by_po.get(po_key, rec["header"])

        for it in rec["items"]:
            all_rows.append(
                {
                    "Source PDF": rec["name"],
                    "Order No": best.get("Order No", rec["po_raw"]),
                    "Document Date": best.get("Document Date", ""),
                    "Delivery Date": best.get("Delivery Date", ""),
                    "Ship To": ship_map.get(po_key, ""),
                    **it,
                }
            )

    if not all_rows:
        st.error("No item rows detected across the uploaded PDFs.")
        st.stop()

    df = pd.DataFrame(all_rows)

    st.success(f"Processed {len(uploaded_files)} PDF(s) • {len(df)} rows extracted")
    st.dataframe(df, use_container_width=True)

    # Combined Excel
    combined_out = BytesIO()
    df.to_excel(combined_out, index=False)
    combined_out.seek(0)

    st.download_button(
        "Download Combined Excel",
        data=combined_out,
        file_name="PO_Combined.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # ZIP (combined + per PDF)
    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("PO_Combined.xlsx", combined_out.getvalue())

        for pdf_name in df["Source PDF"].unique():
            sub = df[df["Source PDF"] == pdf_name].copy()
            out = BytesIO()
            sub.to_excel(out, index=False)
            out.seek(0)
            safe_name = re.sub(r"[^\w\-\.]+", "_", pdf_name.replace(".pdf", ""))
            zf.writestr(f"{safe_name}.xlsx", out.getvalue())

    zip_buf.seek(0)
    st.download_button(
        "Download ZIP (Combined + Per PDF)",
        data=zip_buf,
        file_name="PO_Excel_Files.zip",
        mime="application/zip",
    )

st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        color: #555;
        text-align: center;
        padding: 6px;
        font-size: 12px;
        border-top: 1px solid #e6e6e6;
    }
    </style>

    <div class="footer">
        TBG PO PDF to Excel Converter • Version 2.7.0 • Developed by JBI
    </div>
    """,
    unsafe_allow_html=True,
)
