<div align="center">

# 🛸 Skylark BI Agent

### Ask your business a question. Get a founder-ready answer.

_A conversational BI analyst that queries **live** monday.com boards — no CSV exports, no stale dashboards._

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-F55036?logo=groq&logoColor=white)](https://console.groq.com/)
[![monday.com](https://img.shields.io/badge/monday.com-GraphQL%20API-FF3D57?logo=monday.com&logoColor=white)](https://developer.monday.com/)
[![Status](https://img.shields.io/badge/status-prototype-yellow)]()

</div>

---

### 💬 What it does

> *"How's our pipeline looking for the Mining sector?"*
> *"What's the status of our Renewables work orders?"*
> *"Give me a leadership update on deal flow this quarter."*

Ask it like you'd ask an analyst. It pulls straight from monday.com,
cleans the messy real-world data on the way in, and answers with
numbers, context, and the caveats that matter — not just a raw table.

<div align="center">
<img src="./screenshot.png" alt="Skylark BI Agent chat interface" width="720">

<sub>The deployed agent — dark UI, live refresh, conversational input</sub>
</div>

---

## 📚 Contents

- [Why this exists](#-why-this-exists)
- [How it's built](#%EF%B8%8F-how-its-built)
- [Setup](#-setup)
- [monday.com configuration](#-mondaycom-configuration)
- [Known data-quality handling](#-known-data-quality-handling)
- [Files](#-files)

## 🎯 Why this exists

Founders don't want to open monday.com, filter three boards, and do
mental math. They want to ask a question in plain English and get a
straight answer — with the messiness of real data (missing values,
inconsistent formats, ambiguous phrasing) already handled for them.
This agent is built to be that layer.

## 🏛️ How it's built

| Layer | File | Job |
|---|---|---|
| 💬 **Chat UI** | `app.py` | Streamlit interface; Groq (Llama 3.3 70B) tool-calling loop interprets questions, calls the right tool, and writes the final answer |
| 📡 **API client** | `monday_client.py` | Thin GraphQL wrapper over monday.com — auth, pagination, error handling |
| 🧹 **Cleaning** | `normalize.py` | Turns raw monday.com column values into typed pandas DataFrames; runs missingness/data-quality checks |

**Three tools, on demand:**

| Tool | What it answers |
|---|---|
| `query_deals` | Pipeline value, row counts, and samples — filterable by sector, stage, or status |
| `query_work_orders` | Execution-status breakdown by sector — counts and percentages |
| `get_data_quality_report` | The missing-data caveats behind any of the above |

The system prompt requires every answer to include a headline number,
the supporting breakdown, relevant context, data-quality caveats, and
one concrete takeaway — not a bare figure with no interpretation.
Ambiguous questions ("this quarter," with no year) get a clarifying
question instead of a silent guess.

## ⚙️ Setup

### 1️⃣ Clone & environment

```bash
git clone https://github.com/Adityaa0611/Skylark-bi-agent.git
cd Skylark-bi-agent
python -m venv venv
# Windows:      venv\Scripts\activate
# Mac / Linux:  source venv/bin/activate
pip install -r requirements.txt
```

> Pinned to **Python 3.12** (`runtime.txt`) — newer Python builds have
> hit dependency issues with this stack.

### 2️⃣ Configure secrets

Create a `.env` file (see `.env.example`):

| Variable | Where to get it |
|---|---|
| 🔑 `MONDAY_API_TOKEN` | monday.com → **Admin** → **API** |
| 🔑 `GROQ_API_KEY` | [console.groq.com](https://console.groq.com/) *(free)* |
| 🔢 `DEALS_BOARD_ID` | Your Deals board's ID |
| 🔢 `WORK_ORDERS_BOARD_ID` | Your Work Orders board's ID |

### 3️⃣ Run it

```bash
streamlit run app.py
```

## 🧩 monday.com configuration

Import the provided CSVs as two boards, **Deals** and **Work Orders**,
using Status/Date/Numbers column types as described in the assignment.

- **Deals** columns are matched by monday.com's auto-generated column
  IDs (`DEALS_COLUMN_MAP` in `app.py`) — these are board-specific, so
  if you rebuild the board, re-discover the IDs and update the map.
- **Work Orders** columns are matched by **title keywords** instead
  (`WORK_ORDERS_KEYWORD_MAP`), so no manual column-ID lookup is needed
  there — the agent finds the right column by scanning titles for
  words like "status," "sector," or "value."

## 🧹 Known data-quality handling

| Issue | Handling |
|---|---|
| Missing deal values | Treated as **unknown**, not zero — excluded from totals rather than counted as `$0` |
| Inconsistent date formats | Parsed across multiple common formats; anything unparseable becomes `null`, not a crash |
| Incomplete data affecting an answer | Surfaced as a caveat alongside the answer, every time it's relevant |

## 📁 Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit chat UI, Groq tool-calling loop, system prompt |
| `monday_client.py` | Read-only monday.com GraphQL client |
| `normalize.py` | Column cleaning, typing, and data-quality reporting |
| `requirements.txt` | Pinned dependencies |
| `runtime.txt` | Python version pin (3.12) |

📄 Full assumptions, trade-offs, and the "leadership updates"
interpretation are in [`DECISION_LOG.md`](./DECISION_LOG.md).

---

<div align="center">

Built for the Skylark Drones full-stack assignment · read-only, live monday.com integration · zero-cost LLM tier

</div>
