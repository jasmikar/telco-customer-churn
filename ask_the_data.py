"""
ask_the_data.py

A small AI-assisted analytics tool: I ask a question in plain language,
a local LLM (via Ollama) translates it into a SQL query against my BigQuery
dataset, the script runs the query, and the same LLM summarizes the result
in plain language.

I built this as a portfolio project to demonstrate a practical LLM-assisted
analytics workflow: natural language -> SQL -> execution -> validated,
human-readable insight. I use a fully local, free model (Llama 3.1 via
Ollama) rather than a paid API, so the project can be run end-to-end by
anyone without an API key.

SETUP:
1. Install Ollama from ollama.com (free, no account required)
2. Run in a terminal: ollama pull llama3.1
   (downloads the model, ~4-5 GB, takes a few minutes)
3. pip install ollama google-cloud-bigquery --break-system-packages
4. Set the GOOGLE_APPLICATION_CREDENTIALS environment variable to the path
   of your downloaded BigQuery service account key (a .json file)
5. Fill in PROJECT_ID, DATASET and TABLE below with your own values
6. Make sure Ollama is running in the background (open the app, or run
   "ollama serve" in a separate terminal) before running this script

DATA: IBM Telco Customer Churn dataset (public, via Kaggle)
https://www.kaggle.com/datasets/blastchar/telco-customer-churn
"""

import os
import ollama
from google.cloud import bigquery

# ---------- FILL IN YOUR OWN VALUES HERE ----------
PROJECT_ID = "telco-customer-churn-508416"   # my BigQuery project ID
DATASET = "churn_data"                        # my dataset name
TABLE = "customers"                           # my table name
MODEL = "llama3.1"                            # the model downloaded via ollama pull
KEY_FILE = "telco-customer-churn-508416-949403481e19.json"  # my service account key filename
# ---------------------------------------------------

# Point the Google Cloud SDK at my key file. The filename itself isn't
# sensitive -- the file's contents are, which is why it's listed in
# .gitignore and never gets committed to the repo.
os.environ.setdefault(
    "GOOGLE_APPLICATION_CREDENTIALS",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), KEY_FILE),
)

# Table schema description, so the model knows what it can query.
# These are the exact column types BigQuery auto-detected from the CSV
# (note that several Yes/No columns were detected as BOOLEAN, not STRING).
SCHEMA_DESCRIPTION = """
The table {project}.{dataset}.{table} contains one row per customer of a
fictional telecom/streaming company. Columns:

- customerID (STRING): unique customer id
- gender (STRING): Male / Female
- SeniorCitizen (INTEGER): 0 or 1
- Partner (BOOLEAN): true / false
- Dependents (BOOLEAN): true / false
- tenure (INTEGER): number of months as a customer
- PhoneService (BOOLEAN): true / false
- MultipleLines (STRING): Yes / No / No phone service
- InternetService (STRING): DSL / Fiber optic / No
- OnlineSecurity (STRING): Yes / No / No internet service
- OnlineBackup (STRING): Yes / No / No internet service
- DeviceProtection (STRING): Yes / No / No internet service
- TechSupport (STRING): Yes / No / No internet service
- StreamingTV (STRING): Yes / No / No internet service
- StreamingMovies (STRING): Yes / No / No internet service
- Contract (STRING): Month-to-month / One year / Two year
- PaperlessBilling (BOOLEAN): true / false
- PaymentMethod (STRING): e.g. Electronic check, Mailed check, Bank transfer, Credit card
- MonthlyCharges (FLOAT): monthly charge amount
- TotalCharges (STRING): total charges to date (may need SAFE_CAST to FLOAT64)
- Churn (BOOLEAN): true / false -- true means the customer has left

IMPORTANT: since Partner, Dependents, PhoneService, PaperlessBilling and
Churn are BOOLEAN columns, write WHERE Churn = true (not WHERE Churn = 'Yes').
""".format(project=PROJECT_ID, dataset=DATASET, table=TABLE)

bq_client = bigquery.Client(project=PROJECT_ID)


def question_to_sql(question: str) -> str:
    """Ask the local LLM to write a BigQuery Standard SQL query for a plain-language question."""
    prompt = f"""You are a data analyst who writes BigQuery Standard SQL.

{SCHEMA_DESCRIPTION}

Write ONE SQL query that answers the following question. Reply with ONLY
the SQL code -- no explanation, no markdown code fences, no extra text.

Question: {question}
"""
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    sql = response["message"]["content"].strip()
    # Smaller models often add markdown code fences or extra text despite
    # the instruction above -- strip that out as a safety net.
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql


def run_query(sql: str):
    """Run the SQL query against BigQuery and return the result as a list of rows."""
    query_job = bq_client.query(sql)
    rows = list(query_job.result())
    return rows


def summarize_result(question: str, sql: str, rows) -> str:
    """Ask the local LLM to summarize the query result in plain language."""
    rows_as_text = "\n".join(str(dict(row)) for row in rows[:50])  # cap at 50 rows
    prompt = f"""Original question: {question}

The SQL query that was run:
{sql}

The result (up to 50 rows shown):
{rows_as_text}

Summarize the answer to the question in 2-4 sentences, in plain language,
for a non-technical colleague. Reference concrete numbers from the result.
"""
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()


def main():
    print(f"Using local model: {MODEL} (via Ollama)")
    print("Ask a question about the customer data (type 'quit' to exit).\n")
    while True:
        question = input("Your question: ").strip()
        if question.lower() in ("quit", "exit", ""):
            break

        try:
            sql = question_to_sql(question)
            print(f"\n--- Generated SQL ---\n{sql}\n")

            rows = run_query(sql)
            print(f"--- Result: {len(rows)} rows ---")

            summary = summarize_result(question, sql, rows)
            print(f"\n--- Answer ---\n{summary}\n")

        except Exception as e:
            print(f"\nSomething went wrong: {e}\n")
            error_text = str(e).lower()
            if "badrequest" in error_text or "syntax" in error_text or "invalid" in error_text:
                # Smaller local models make more SQL mistakes than larger hosted
                # models -- this is a known trade-off I document in the README
                # as part of validating AI-assisted analysis, per good practice.
                print("Tip: this looks like a SQL error -- smaller models make more")
                print("of these than large hosted models. Check that the generated")
                print("SQL actually matches your column names, and consider logging")
                print("cases like this in your README -- it shows you understand")
                print("the model's limitations.\n")
            elif "connection" in error_text or "connect" in error_text:
                print("Tip: this looks like Ollama isn't running. Start it with")
                print("'ollama serve' in a separate terminal, then try again.\n")
            elif "credentials" in error_text or "permission" in error_text or "auth" in error_text:
                print("Tip: this looks like a Google Cloud authentication issue.")
                print("Check that KEY_FILE points to a valid service account key")
                print("and that the service account has BigQuery access.\n")
            else:
                print("Tip: check that Ollama is running and your BigQuery")
                print("credentials and table names are set up correctly.\n")


if __name__ == "__main__":
    main()
