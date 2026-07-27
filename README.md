Skylark Drones — Business Intelligence Agent 🦅📈
An AI-powered, conversational business-intelligence agent designed to answer complex, founder-level questions in real-time. By leveraging Groq's LLM API with advanced tool-calling capabilities, this agent seamlessly queries monday.com boards via GraphQL, processes the data, and delivers natural-language insights complete with data-quality caveats.

The Streamlit-based conversational interface, allowing users to ask questions like, "How's our pipeline for the Mining sector?"

✨ Key Features
Conversational AI & Tool Calling: Uses Groq's fast LLMs to intelligently interpret user questions, determine the necessary data, and execute tool calls (query_deals, get_data_quality_report) autonomously.

Live GraphQL Integration: Connects directly to monday.com's API for real-time data retrieval—no stale dashboards.

Robust Data Normalization: Cleans raw API payloads into strongly-typed pandas DataFrames, parsing diverse date formats gracefully.

Transparent Data Quality: Automatically computes missingness reports. If a business answer is affected by incomplete data (e.g., missing deal values), the agent explicitly surfaces these caveats to the user.

🏗️ System Architecture
The project is modularized into three core components:

monday_client.py (API Layer): A lightweight, robust wrapper over the monday.com GraphQL API handling authentication, query pagination, and error management.

normalize.py (Data Pipeline): The data processing engine. It ingests raw monday.com column values, normalizes them into typed pandas DataFrames, and generates real-time data-quality/missingness metrics.

app.py (Application & Presentation): The Streamlit chat UI. It orchestrates the Groq LLM tool-calling loop, routing natural language queries to the appropriate backend functions and rendering the final contextualized response.

🚀 Getting Started
Prerequisites
Python 3.8+

A monday.com account with admin access (to generate an API token).

A Groq API Key.

1. Installation
Clone the repository and navigate into the project directory:

Bash
git clone https://github.com/yourusername/skylark-bi-agent.git
cd skylark-bi-agent
Create and activate a virtual environment:

Bash
# On macOS/Linux
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
Install the required dependencies:

Bash
pip install -r requirements.txt
2. Environment Configuration
Create a .env file in the root directory (you can use .env.example as a template) and add your credentials:

Code snippet
MONDAY_API_TOKEN=your_monday_personal_api_token
GROQ_API_KEY=your_groq_console_api_key
DEALS_BOARD_ID=your_deals_board_id
WORK_ORDERS_BOARD_ID=your_work_orders_board_id
(Note: You can find your monday.com API token under Admin → API).

3. monday.com Board Configuration
To ensure the agent reads your data correctly:

Import your source CSVs into monday.com to create two boards: Deals and Work Orders.

Ensure columns are set to appropriate types (Status, Date, Numbers).

Map Column IDs: monday.com auto-generates internal column IDs upon import. Run the test snippet provided in the setup notes to discover these IDs, then update the DEALS_COLUMN_MAP and the equivalent Work Orders map inside app.py.

4. Run the Application
Launch the Streamlit interface:

Bash
streamlit run app.py
🛡️ Data Handling Philosophies
To maintain analytical integrity, this agent adheres to strict data handling rules:

Null Handling: Missing deal values or financials are strictly treated as unknown rather than 0, preventing skewed totals and inaccurate averages.

Date Parsing: The system anticipates and parses multiple common date formats. Unparseable, corrupted date strings are safely converted to null to prevent application crashes.

Contextual Honesty: The agent is instructed to append data-quality warnings to its natural-language answers whenever the underlying data set is incomplete.
