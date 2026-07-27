import pandas as pd
from datetime import datetime
from difflib import get_close_matches

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]

SECTOR_MAP = {
    "mining": "Mining", "powerline": "Powerline", "renewables": "Renewables",
    "railways": "Railways", "construction": "Construction", "dsp": "DSP",
    "tender": "Tender", "security and surveillance": "Security and Surveillance",
    "others": "Others",
}


def parse_date(value):
    if not value or str(value).strip() == "":
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except ValueError:
            continue
    return None


def parse_number(value):
    if value is None:
        return None
    s = str(value).replace(",", "").replace("₹", "").replace("$", "").strip()
    if s == "" or s.lower() == "none":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def clean_category(value, mapping=None):
    if not value or str(value).strip() == "":
        return None
    s = str(value).strip().lower()
    if mapping and s in mapping:
        return mapping[s]
    return str(value).strip()


def split_multi_value(value):
    if not value or str(value).strip() == "":
        return []
    return [v.strip() for v in str(value).split("+") if v.strip()]


def items_to_dataframe(items: list) -> pd.DataFrame:
    rows = []
    for item in items:
        row = {"item_name": item["name"], "item_id": item["id"]}
        for cv in item["column_values"]:
            row[cv["id"]] = cv["text"]
        rows.append(row)
    return pd.DataFrame(rows)


def normalize_deals(df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
    out = pd.DataFrame()
    out["deal_name"] = df.get(column_map.get("deal_name", ""), None)
    out["owner_code"] = df.get(column_map.get("owner_code", ""), None)
    out["client_code"] = df.get(column_map.get("client_code", ""), None)
    out["status"] = df.get(column_map.get("status", ""), None)
    if column_map.get("close_date") in df.columns:
        out["close_date"] = df[column_map["close_date"]].apply(parse_date)
    if column_map.get("tentative_close_date") in df.columns:
        out["tentative_close_date"] = df[column_map["tentative_close_date"]].apply(parse_date)
    if column_map.get("created_date") in df.columns:
        out["created_date"] = df[column_map["created_date"]].apply(parse_date)
    if column_map.get("deal_value") in df.columns:
        out["deal_value"] = df[column_map["deal_value"]].apply(parse_number)
    out["closure_probability"] = df.get(column_map.get("closure_probability", ""), None)
    out["deal_stage"] = df.get(column_map.get("deal_stage", ""), None)
    out["product_deal_raw"] = df.get(column_map.get("product_deal", ""), None)
    if "product_deal_raw" in out.columns:
        out["product_deal_list"] = out["product_deal_raw"].apply(split_multi_value)
    if column_map.get("sector") in df.columns:
        out["sector"] = df[column_map["sector"]].apply(lambda v: clean_category(v, SECTOR_MAP))
    return out


def fuzzy_match(value: str, choices: list, cutoff: float = 0.6):
    """
    Correct typos by matching `value` against a list of known-good `choices`
    (e.g. actual sector names present in the data), case-insensitively.
    Returns the matching choice in its original casing, or None if nothing
    is close enough.
    """
    if not value:
        return None
    clean_choices = [c for c in choices if c]
    if not clean_choices:
        return None
    lower_to_original = {}
    for c in clean_choices:
        lower_to_original.setdefault(c.lower(), c)

    value_lower = value.strip().lower()

    # Exact match first (fast path, no correction needed).
    if value_lower in lower_to_original:
        return lower_to_original[value_lower]

    matches = get_close_matches(value_lower, list(lower_to_original.keys()), n=1, cutoff=cutoff)
    if matches:
        return lower_to_original[matches[0]]
    return None


def auto_map_columns(columns: list, keyword_map: dict) -> dict:
    """
    Build a {field_name: column_id} map by matching monday.com column titles
    against keywords, instead of requiring hand-typed column IDs.

    columns: list of {"id": ..., "title": ..., "type": ...} from the board.
    keyword_map: {field_name: [keyword1, keyword2, ...]} — first column whose
                 title contains any keyword (case-insensitive) wins.
    """
    result = {}
    used_ids = set()
    for field_name, keywords in keyword_map.items():
        match = None
        for col in columns:
            title = (col.get("title") or "").lower()
            if col["id"] in used_ids:
                continue
            if any(kw in title for kw in keywords):
                match = col["id"]
                break
        if match:
            result[field_name] = match
            used_ids.add(match)
    return result


def normalize_work_orders(df: pd.DataFrame, column_map: dict) -> pd.DataFrame:
    out = pd.DataFrame()
    out["order_name"] = df.get(column_map.get("order_name", ""), None)
    out["execution_status"] = df.get(column_map.get("execution_status", ""), None)
    if column_map.get("sector") in df.columns:
        out["sector"] = df[column_map["sector"]].apply(lambda v: clean_category(v, SECTOR_MAP))
    if column_map.get("order_date") in df.columns:
        out["order_date"] = df[column_map["order_date"]].apply(parse_date)
    if column_map.get("order_value") in df.columns:
        out["order_value"] = df[column_map["order_value"]].apply(parse_number)
    if column_map.get("billing_status") in df.columns:
        out["billing_status"] = df[column_map["billing_status"]]
    return out


def status_breakdown(df: pd.DataFrame, status_col: str) -> dict:
    """Count + percentage breakdown of a status column, with blanks tracked separately."""
    if df.empty or status_col not in df.columns:
        return {"total": 0, "breakdown": []}
    total = len(df)
    working = df[status_col].fillna("(Blank/unknown)")
    working = working.replace("", "(Blank/unknown)")
    counts = working.value_counts()
    breakdown = [
        {"status": status, "count": int(count), "pct": round(count / total * 100, 1)}
        for status, count in counts.items()
    ]
    return {"total": total, "breakdown": breakdown}


def missingness_report(df: pd.DataFrame) -> dict:
    report = {}
    caveats = []
    total = len(df)
    for col in df.columns:
        missing = df[col].isna().sum()
        pct = round((missing / total) * 100, 1) if total else 0
        report[col] = pct
        if pct > 15:
            caveats.append(f"{pct}% of rows are missing '{col}' — related figures should be treated as a lower bound.")
    return {"per_column_pct_missing": report, "caveats": caveats}