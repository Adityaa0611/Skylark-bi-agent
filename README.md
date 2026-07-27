```
   _____ _____   ____  _         .+.::+   .::+#####+
  / ____|  __ \ / __ \| |       .::::+.::: BI AGENT
 | (___ | |__) | |  | | |       :.:+###.:::::.
  \___ \|  _  /| |  | | |        .:++###+::.
  ____) | | \ \| |__| | |____    ..:+++::.
 |_____/|_|  \_\\____/|______|     ...
```

**Skylark Drones asks its data questions. This answers them — live, from monday.com, in plain English.**

---

### the pitch, in one exchange

```
you   > How's our pipeline looking for the Mining sector?

agent > Mining pipeline: ₹4.2Cr across 11 open deals, concentrated in
        Negotiation and Proposal stages (7 of 11). One data-quality
        note: 2 deals are missing a closure probability, so this
        total may be conservative. Take-away: Mining is your
        second-largest open sector after Renewables — worth a
        check-in on the two unscored deals before quarter close.
```

No dashboard. No filter menu. No stale export. Just a question and
an answer that actually reasons about the data behind it.

---

### the screenshot, because you should see it before you read about it

<img src="./screenshot.png" alt="Skylark BI Agent — live chat interface" width="700">

---

### under the hood

Three files. That's the whole engine.

```
app.py             — Streamlit chat + Groq (Llama 3.3 70B) tool-calling loop
monday_client.py    — GraphQL wrapper: auth, pagination, nothing fancier
normalize.py        — turns monday.com's raw text cells into real,
                       typed, checked pandas data
```

The model doesn't get raw access to your boards. It gets **three
tools**, and it has to ask for what it needs, like anyone would:

```
query_deals(sector?, stage?, status?)
    → row count, pipeline value, sample rows

query_work_orders(sector?)
    → execution-status breakdown, counts + percentages

get_data_quality_report()
    → what's missing, and how much
```

The system prompt won't let it hand back a bare number either — every
answer needs the headline, the breakdown behind it, relevant context,
any data-quality caveat, and one actual takeaway. If a question is
vague ("this quarter" — which year?), it asks instead of guessing.

---

### getting it running

<details>
<summary><strong>1. clone + install</strong></summary>

```bash
git clone https://github.com/Adityaa0611/Skylark-bi-agent.git
cd Skylark-bi-agent
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Python is pinned to **3.12** in `runtime.txt` — newer builds have hit
dependency friction with this stack.
</details>

<details>
<summary><strong>2. secrets — drop these into a `.env`</strong></summary>

```
MONDAY_API_TOKEN       # monday.com → Admin → API
GROQ_API_KEY           # console.groq.com — free
DEALS_BOARD_ID         # your Deals board's numeric ID
WORK_ORDERS_BOARD_ID   # your Work Orders board's numeric ID
```
</details>

<details>
<summary><strong>3. run it</strong></summary>

```bash
streamlit run app.py
```
</details>

---

### wiring up monday.com itself

Import the assignment CSVs as two boards: **Deals** and **Work
Orders**, with Status/Date/Numbers column types.

Two different matching strategies are used on purpose:

- **Deals** → matched by monday.com's auto-generated column IDs
  (`DEALS_COLUMN_MAP` in `app.py`). Rebuild the board, and you'll need
  to re-discover and update those IDs — they're board-specific.
- **Work Orders** → matched by scanning **column titles** for
  keywords like *"status"*, *"sector"*, *"value"*
  (`WORK_ORDERS_KEYWORD_MAP`). No manual ID lookup required.

---

### what happens when the data is a mess (it is)

| the mess | what the agent does about it |
|---|---|
| a deal's value is blank | counted as **unknown**, never as ₹0 — kept out of totals entirely |
| dates in five different formats | parsed across the common ones; anything unreadable becomes `null`, not a crash |
| an answer would be wrong without context | the caveat rides along with the answer, every time |

---

### the rest of the paper trail

Assumptions, trade-offs, and how *"leadership updates"* got
interpreted all live in [`DECISION_LOG.md`](./DECISION_LOG.md) — worth
a read before you judge any of the above.

<br>

<div align="center">
<sub>Skylark Drones full-stack assignment · read-only monday.com integration · runs on free-tier everything</sub>
</div>
