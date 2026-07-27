import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from monday_client import get_board_items
from normalize import (
    items_to_dataframe,
    normalize_deals,
    normalize_work_orders,
    status_breakdown,
    auto_map_columns,
    fuzzy_match,
    missingness_report,
)

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN") or st.secrets.get("MONDAY_API_TOKEN", "")
DEALS_BOARD_ID = os.getenv("DEALS_BOARD_ID") or st.secrets.get("DEALS_BOARD_ID", "")
WORK_ORDERS_BOARD_ID = os.getenv("WORK_ORDERS_BOARD_ID") or st.secrets.get("WORK_ORDERS_BOARD_ID", "")
GROQ_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")

client = Groq(api_key=GROQ_KEY)
MODEL_NAME = "llama-3.3-70b-versatile"

st.set_page_config(page_title="Skylark BI Agent", layout="wide")
st.title("Skylark Drones — Business Intelligence Agent")

DEALS_COLUMN_MAP = {
    "deal_name": "item_name",
    "owner_code": "text_mm5n5ttg",
    "client_code": "text_mm5n352c",
    "status": "color_mm5nqne7",
    "close_date": "date_mm5nj77k",
    "closure_probability": "color_mm5nk2be",
    "deal_value": "numeric_mm5nbq08",
    "tentative_close_date": "date_mm5n76tt",
    "deal_stage": "color_mm5nnvzt",
    "product_deal": "text_mm5ne48n",
    "sector": "text_mm5nzvjc",
    "created_date": "date_mm5nnma5",
}

# Keywords used to auto-detect Work Orders columns by their TITLE (not their ID),
# so no manual column-ID lookup is needed. First column whose title contains any
# keyword wins. If your board uses different wording, add more keywords here.
WORK_ORDERS_KEYWORD_MAP = {
    "execution_status": ["execution status", "status"],
    "sector": ["sector"],
    "order_date": ["date"],
    "order_value": ["value", "amount", "cost"],
    "billing_status": ["billing"],
}


@st.cache_data(ttl=300)
def load_data():
    deals_raw = get_board_items(DEALS_BOARD_ID, MONDAY_TOKEN)
    errors = []
    if not deals_raw["success"]:
        errors.append(f"Deals board fetch failed: {deals_raw['errors']}")

    deals_df = items_to_dataframe(deals_raw.get("items", []))
    deals_clean = normalize_deals(deals_df, DEALS_COLUMN_MAP) if not deals_df.empty else pd.DataFrame()
    deals_quality = missingness_report(deals_clean) if not deals_clean.empty else {}

    work_orders_raw = get_board_items(WORK_ORDERS_BOARD_ID, MONDAY_TOKEN)
    if not work_orders_raw["success"]:
        errors.append(f"Work Orders board fetch failed: {work_orders_raw['errors']}")

    wo_column_map = auto_map_columns(work_orders_raw.get("columns", []), WORK_ORDERS_KEYWORD_MAP)
    wo_column_map["order_name"] = "item_name"
    missing_fields = [f for f in WORK_ORDERS_KEYWORD_MAP if f not in wo_column_map]
    if missing_fields:
        errors.append(
            f"Could not auto-detect these Work Orders columns by title: {missing_fields}. "
            f"Add matching keywords to WORK_ORDERS_KEYWORD_MAP in app.py, or rename the "
            f"columns on your board to include one of the expected keywords."
        )

    wo_df = items_to_dataframe(work_orders_raw.get("items", []))
    wo_clean = normalize_work_orders(wo_df, wo_column_map) if not wo_df.empty else pd.DataFrame()
    wo_quality = missingness_report(wo_clean) if not wo_clean.empty else {}

    return {
        "deals_raw_df": deals_df,
        "deals_clean_df": deals_clean,
        "deals_quality": deals_quality,
        "work_orders_clean_df": wo_clean,
        "work_orders_quality": wo_quality,
        "errors": errors,
    }


def query_deals_tool(sector: str = None, stage: str = None, status: str = None):
    df = st.session_state.data["deals_clean_df"]
    if df.empty:
        return {"error": "No deals data loaded."}
    filtered = df.copy()
    corrections = []

    if sector:
        known_sectors = df["sector"].dropna().unique().tolist() if "sector" in df.columns else []
        matched = fuzzy_match(sector, known_sectors)
        if matched:
            if matched.lower() != sector.strip().lower():
                corrections.append(f"Interpreted sector '{sector}' as '{matched}'.")
            filtered = filtered[filtered["sector"].str.lower() == matched.lower()]
        else:
            return {
                "error": f"No sector matching '{sector}' found.",
                "available_sectors": sorted(known_sectors),
            }

    if stage:
        known_stages = df["deal_stage"].dropna().unique().tolist() if "deal_stage" in df.columns else []
        matched = fuzzy_match(stage, known_stages, cutoff=0.5)
        if matched:
            if matched.lower() != stage.strip().lower():
                corrections.append(f"Interpreted stage '{stage}' as '{matched}'.")
            filtered = filtered[filtered["deal_stage"].str.contains(matched, case=False, na=False)]
        else:
            filtered = filtered[filtered["deal_stage"].str.contains(stage, case=False, na=False)]

    if status:
        known_statuses = df["status"].dropna().unique().tolist() if "status" in df.columns else []
        matched = fuzzy_match(status, known_statuses)
        if matched:
            if matched.lower() != status.strip().lower():
                corrections.append(f"Interpreted status '{status}' as '{matched}'.")
            filtered = filtered[filtered["status"].str.lower() == matched.lower()]
        else:
            return {
                "error": f"No status matching '{status}' found.",
                "available_statuses": sorted(known_statuses),
            }

    summary_cols = ["deal_name", "status", "sector", "deal_stage", "deal_value"]
    available_cols = [c for c in summary_cols if c in filtered.columns]

    return {
        "row_count": len(filtered),
        "total_value": float(filtered["deal_value"].sum(skipna=True)) if "deal_value" in filtered else 0,
        "missing_value_count": int(filtered["deal_value"].isna().sum()) if "deal_value" in filtered else 0,
        "sample_rows": filtered[available_cols].head(5).to_dict(orient="records"),
        "corrections_made": corrections,
    }


def get_data_quality_tool():
    return st.session_state.data["deals_quality"]


def query_work_orders_tool(sector: str = None):
    df = st.session_state.data["work_orders_clean_df"]
    if df.empty:
        return {"error": "No work orders data loaded."}
    filtered = df.copy()
    corrections = []

    if sector:
        known_sectors = df["sector"].dropna().unique().tolist() if "sector" in df.columns else []
        matched = fuzzy_match(sector, known_sectors)
        if matched:
            if matched.lower() != sector.strip().lower():
                corrections.append(f"Interpreted sector '{sector}' as '{matched}'.")
            filtered = filtered[filtered["sector"].str.lower() == matched.lower()]
        else:
            return {
                "error": f"No sector matching '{sector}' found.",
                "available_sectors": sorted(known_sectors),
            }

    result = status_breakdown(filtered, "execution_status")
    result["sector_filter"] = sector or "All sectors"
    result["corrections_made"] = corrections
    result["data_quality"] = st.session_state.data["work_orders_quality"]
    return result


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_deals",
            "description": "Query the Deals board with optional filters. Returns row count, total pipeline value, missing-value count, and a few sample rows.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sector": {"type": "string", "description": "Filter by sector, e.g. Mining, Renewables"},
                    "stage": {"type": "string", "description": "Filter by deal stage substring, e.g. 'Negotiations'"},
                    "status": {"type": "string", "description": "Filter by status: Open, On Hold, Dead"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_data_quality_report",
            "description": "Return the missing-data report and caveats for the Deals board.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_work_orders",
            "description": (
                "Get the execution-status breakdown for Work Orders, optionally filtered by sector. "
                "Returns total count examined and, for each execution status value, the count and "
                "percentage of the total. Use this for any question about work order status, progress, "
                "or completion rate, e.g. 'What's the status of our mining sector work orders?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sector": {"type": "string", "description": "Filter by sector, e.g. Mining, Renewables"},
                },
            },
        },
    },
]

AVAILABLE_FUNCTIONS = {
    "query_deals": query_deals_tool,
    "get_data_quality_report": get_data_quality_tool,
    "query_work_orders": query_work_orders_tool,
}

SYSTEM_PROMPT = """You are a business intelligence analyst for Skylark Drones.
Answer founder-level questions about pipeline, revenue, and sectoral performance using the query_deals and
get_data_quality_report tools. Always mention relevant data quality caveats (missing values, small sample sizes)
when they affect your answer. If a question is ambiguous (e.g. "this quarter"), ask a clarifying question before
computing an answer.

For every answer, provide a thorough, well-structured response (roughly 150-300 words unless the question is
trivially simple) that includes:
1. A direct headline answer to the question.
2. The supporting numbers/breakdown behind that answer (e.g. by sector, stage, or time period).
3. Any relevant trend, comparison, or context that helps a founder interpret the numbers.
4. Data quality caveats, if applicable.
5. One concrete, actionable takeaway or recommendation.

Do not just give a single number or one-line answer — always explain the "why" and "so what" behind the data.

When a question asks about the STATUS, BREAKDOWN, or DISTRIBUTION of a set of items (e.g. "what's the status of
X work orders", "how are our deals distributed by stage"), call the relevant tool (query_work_orders or
query_deals) and format your answer EXACTLY like this:

1. A one-line header describing what the table shows (e.g. "Mining-sector work orders (as of the latest data pull)").
2. A markdown table with columns for the category (e.g. Execution Status), the count (# orders), and the
   percentage of the filtered total. Use the exact numbers returned by the tool — never estimate or round
   percentages yourself.
3. Immediately below the table: "Total <items> examined: <N>."
4. A "Take-aways" section with 3-5 bullet points interpreting the numbers (what's dominant, what's small,
   what it implies for the business).
5. A "Data-quality note" sentence stating how reliable this specific field is, referencing the data_quality/
   missingness figures from the tool output when relevant.

Only use this table format for breakdown/status/distribution questions. For single-number or comparison
questions (e.g. "what's our total mining pipeline value"), answer in prose with the structure described above.

If a tool result includes "corrections_made" (e.g. a misspelled sector/status/stage was auto-corrected to a
real value), briefly note the correction in one short sentence at the very start of your answer, e.g.
"(Assuming you meant 'Mining' — here's that breakdown:)" — then proceed normally. If a tool result includes
"error" with an "available_sectors" or "available_statuses" list and no close match was found, tell the user
their filter didn't match anything and list the valid options instead of guessing."""


def trim_history(messages, keep_last=6):
    system_msgs = [m for m in messages if m["role"] == "system"]
    other_msgs = [m for m in messages if m["role"] != "system"]
    return system_msgs + other_msgs[-keep_last:]


if "data" not in st.session_state:
    with st.spinner("Loading data from monday.com..."):
        st.session_state.data = load_data()

if st.session_state.data["errors"]:
    for e in st.session_state.data["errors"]:
        st.warning(e)

if st.button("Refresh data from monday.com"):
    st.cache_data.clear()
    st.session_state.data = load_data()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

for msg in st.session_state.messages:
    if msg["role"] in ("user", "assistant") and msg.get("content"):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

user_input = st.chat_input("Ask a business question, e.g. 'How's our pipeline for the Mining sector?'")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=trim_history(st.session_state.messages),
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=1024,
            )
            msg = response.choices[0].message

            while msg.tool_calls:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in msg.tool_calls
                    ],
                })
                for tc in msg.tool_calls:
                    fn = AVAILABLE_FUNCTIONS.get(tc.function.name)
                    raw_args = tc.function.arguments
                    args = json.loads(raw_args) if raw_args and raw_args.strip() not in ("", "null") else {}
                    if args is None:
                        args = {}
                    result = fn(**args) if fn else {"error": "unknown tool"}
                    st.session_state.messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, default=str),
                    })

                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=trim_history(st.session_state.messages),
                    tools=TOOLS,
                    tool_choice="auto",
                    max_tokens=1024,
                )
                msg = response.choices[0].message

            final_text = msg.content or ""
            st.write(final_text)
            st.session_state.messages.append({"role": "assistant", "content": final_text})