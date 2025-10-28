# NL2SQL-Agent Technical Architecture

This document explains, end to end, how the single-table NL→SQL agent works. It is written so that someone new to this repo (even with limited data-engineering background) can understand the moving parts, the flow between files, and how each component contributes to the final SQL that gets returned.

---
## 1. Big-Picture Summary (Layman View)

1. You describe what you want (e.g., “Show top spenders in the last month”).
2. The agent double-checks which tables/columns exist by asking Neo4j (a graph database storing our schema). This means the agent can’t hallucinate nonexistent columns.
3. Gemini (Vertex AI) reads the user request + schema and outputs a strict JSON recipe (an “Intermediate Representation” or IR) describing the SELECT, filters, grouping, etc.
4. A renderer converts that IR into deterministic DuckDB SQL.
5. DuckDB validates the SQL plan (no data is read, we only run `EXPLAIN`).
6. The CLI returns the SQL, the verifier status, and the IR as proof of what happened.

Think of the system as a cautious assistant: one part remembers the schema, one part plans the query, one part converts the plan into SQL, and one part double-checks it before handing it to you.

---
## 2. Code Layout: Who Does What

```
nl2sql-proto/
├── app.py                  # CLI entry point
├── agent_chain.py          # Orchestrates the whole flow
├── prompts/
│   └── planner_system.md   # Planning instructions for Gemini
├── schema_loader/
│   ├── schema.json         # Canonical schema definition
│   └── load_schema_to_neo4j.py # Loader script to populate Neo4j
├── sql/
│   ├── ir_models.py        # Pydantic models for IR JSON
│   └── renderer.py         # Deterministic IR→SQL logic
├── tools/
│   ├── neo4j_schema_tool.py# Fetch table + columns from Neo4j
│   └── sql_verifier.py     # DuckDB-based SQL verifier
├── data/
│   └── customers.csv       # Sample CSV (for reference/testing only)
├── requirements.txt        # Python dependencies
└── ARCHITECTURE.md         # This document
```

**Root-level `.env`** (ignored by git) stores credentials:
```
GOOGLE_CLOUD_PROJECT=only-yours
GOOGLE_CLOUD_LOCATION=us-central1
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASS=password
```
You should either export these in your shell or edit the `.env` so `agent_chain.py` can load them.

---
## 3. Data & Schema Governance

### 3.1 `schema_loader/schema.json`
Describes exactly one table for this prototype:
```json
{
  "dataset": "local_demo",
  "table": {
    "name": "customers",
    "fqdn": "local_demo.customers",
    "csv_path": "../data/customers.csv",
    "columns": [
      {"name": "id", "data_type": "INTEGER", "description": "Primary key"},
      {"name": "name", "data_type": "TEXT", "description": "Full name", "aliases": ["customer name"]},
      {"name": "email", "data_type": "TEXT", "description": "Email address"},
      {"name": "city", "data_type": "TEXT", "description": "City of residence", "aliases": ["location", "town"]},
      {"name": "created_at", "data_type": "TIMESTAMP", "description": "Account creation time", "aliases": ["signup time"]},
      {"name": "spend", "data_type": "DECIMAL(18,2)", "description": "Total spend in currency"}
    ]
  }
}
```

### 3.2 Loading into Neo4j (`schema_loader/load_schema_to_neo4j.py`)
```python
def load_schema(schema_path: str) -> None:
    with open(schema_path) as f:
        schema = json.load(f)
    dataset = schema["dataset"]
    table = schema["table"]
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        # create Dataset, Table, and Column nodes + relationships
```
This script:
- Creates/updates `Dataset`, `Table`, `Column` nodes.
- Stores `col.aliases` for hint matching.
- Runs idempotently thanks to `MERGE` (reruns update data in place).
- Default path is `schema_loader/schema.json` unless `SCHEMA_PATH` is set.

### 3.3 Graph Model in Neo4j
- `(:Dataset {name})`
- `(:Table {name, fqdn})`
- `(:Column {name, data_type, description, aliases, tableFqdn})`
- Relationships: `Dataset -[:HAS_TABLE]-> Table`, `Table -[:HAS_COLUMN]-> Column`

**Why?** Because Neo4j firmly stores schema metadata so the agent doesn’t rely on memory or hallucinate columns.

---
## 4. NL→SQL Flow (from `app.py`) 

### 4.1 CLI Entry (`app.py`)
```python
parser = argparse.ArgumentParser(...)
parser.add_argument("--q", required=True)
parser.add_argument("--format", choices=["text", "json"], default="text")
result = run_nl_to_sql(args.q)
```
- Accepts a natural-language query (`--q`).
- Optional `--format json` prints machine-friendly output.
- Default output prints SQL, verifier response, and IR.

### 4.2 Orchestrator (`agent_chain.py`)
**Responsibilities:** load `.env`, fetch schema, build prompt, call Gemini, parse IR, render SQL, verify SQL.

Key sections:
```python
load_dotenv(ENV_PATH)
...
api_key = os.environ.get("GOOGLE_CLOUD_API_KEY")
project = os.environ.get("GOOGLE_CLOUD_PROJECT")
if api_key and project:
    raise ValueError("... cannot both be set ...")
if project:
    vertex_client = genai.Client(vertexai=True, project=project, location=location)
else:
    vertex_client = genai.Client(vertexai=True, api_key=api_key)
```
This enforces mutual exclusivity between API key and project-based auth. Gemini requests run through your project (`only-yours`) with Application Default Credentials or, if you remove `project`, through an API key (though API key alone typically lacks Vertex permissions).

#### 4.2.1 Schema Retrieval Tool
```python
@tool("get_schema")
def get_schema_tool(_: str = "") -> str:
    return json.dumps(fetch_table_schema())
```
- `fetch_table_schema()` lives in `tools/neo4j_schema_tool.py`:
  ```python
  driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
  record = session.run("""
      MATCH (tb:Table)<-[:HAS_TABLE]-(:Dataset)
      OPTIONAL MATCH (tb)-[:HAS_COLUMN]->(c:Column)
      RETURN tb.fqdn, tb.name,
             collect(
                CASE WHEN c IS NULL THEN NULL ELSE
                     {name:c.name, data_type:c.data_type, description:c.description, aliases:coalesce(c.aliases, [])}
                END
             )
  """).single()
  columns = [col for col in record["cols"] if col is not None]
  ```
- Returns the first table’s name, FQDN, and columns with metadata.

#### 4.2.2 Prompt Construction
```python
SYSTEM_PROMPT = .../prompts/planner_system.md
SYSTEM_PROMPT_TEMPLATE = SystemMessagePromptTemplate.from_template(..., template_format="jinja2")
prompt = ChatPromptTemplate.from_messages([
    SYSTEM_PROMPT_TEMPLATE,
    MessagesPlaceholder("messages"),
])
```
- `planner_system.md` instructs Gemini to output strict JSON matching `sql/ir_models.py`.
- We use Jinja templates so curly braces in the prompt aren’t treated as Python `.format()` placeholders.

#### 4.2.3 Gemini Invocation Helpers
```python
def _lc_messages_to_vertex(messages: List[Any]) -> List[types.Content]:
    ...
    converted.append(types.Content(role=vertex_role, parts=[types.Part(text=text)]))

response = vertex_client.models.generate_content(...)
if not response.text:
    raise ValueError("Gemini returned empty response")
return response.text.strip()
```
- Transforms LangChain `SystemMessage`, `HumanMessage`, etc. into Vertex `types.Content` objects.
- Safety settings disable all blocking categories for demo purposes (turn them on in production).
- `_strip_markdown_fences` removes code fences because Gemini sometimes wraps JSON in ``` ```.

#### 4.2.4 IR Validation
```python
formatted_messages = prompt.format_messages(messages=messages)
response_text = llm.invoke(formatted_messages)
if not isinstance(response_text, str):
    raise ValueError("Planner returned non-string content")
clean_json = _strip_markdown_fences(response_text)
ir = IR.model_validate_json(clean_json)
```
- Uses Pydantic’s `IR` model (`sql/ir_models.py`) to ensure the JSON is well-formed and matches our schema (no extra fields, correct types).

#### 4.2.5 SQL Rendering
```python
sql = render_sql(ir)
```
- `sql/renderer.py` converts IR into deterministic DuckDB SQL:
  ```python
def render_sql(ir: IR) -> str:
    select_clause = ...
    where_clause = ...
    return f"SELECT {select_clause} FROM {quote_identifier(ir.table)}..."
  ```
- `quote_identifier` wraps bare identifiers in double quotes to prevent reserved-word conflicts.
- GROUP BY / ORDER BY quoting is careful—expressions like `COUNT(*)` are left as-is while plain column names get quoted.

#### 4.2.6 SQL Verification (`tools/sql_verifier.py`)
```python
def verify_sql(sql: str, table: str, columns: List[Dict]) -> Dict:
    con = duckdb.connect(database=":memory:")
    con.execute(f'CREATE TABLE "{table}" ({cols_def});')
    try:
        con.execute("EXPLAIN " + sql)
        return {"ok": True, ...}
    except Exception as e:
        return {"ok": False, "message": str(e)}
```
- `DUCK_TYPES` maps known data types (INTEGER, TEXT, DECIMAL, etc.). Unrecognized types default to TEXT.
- If the SQL references a nonexistent column or uses unsupported syntax (e.g., `DATE('now', '-30 days')`), DuckDB raises an error and we bubble it up to the CLI.

### 4.3 CLI Output (`app.py`)
Default (text) mode prints:
```
=== Generated SQL ===
<sql>

=== Verifier ===
{"ok": ..., "message": ...}

=== IR ===
{ JSON IR dump }
```
With `--format json`, it prints:
```json
{
  "sql": "...",
  "verifier": {"ok": true, ...},
  "ir": { ... }
}
```

---
## 5. Control Flow: File-by-File

Below is the request lifecycle with references to key functions/methods:

1. `app.py:main()` → `run_nl_to_sql(query)` from `agent_chain.py`
2. `agent_chain.py:run_nl_to_sql`
   - `get_schema_tool.run("")` → `tools/neo4j_schema_tool.fetch_table_schema`
     - Ensures the agent only sees real columns.
   - Build prompt messages (user query + schema snapshot).
   - `prompt.format_messages(...)` → returns system + user messages.
   - `llm.invoke(...)` → `_invoke_gemini` → Vertex AI Gemini.
     - Uses `_lc_messages_to_vertex` to convert message objects to Vertex content.
   - `_strip_markdown_fences(response_text)` → ensures clean JSON.
   - `IR.model_validate_json(clean_json)` → pydantic validation.
   - `render_sql(ir)` → `sql/renderer.py` (deterministic SQL string).
   - `verify_sql(sql, table, columns)` → `tools/sql_verifier.py` (DuckDB `EXPLAIN`).
3. CLI prints everything or returns as JSON.

If any stage fails (missing schema, malformed IR, SQL syntax issues, DuckDB errors), we raise/return informative errors instead of proceeding with an invalid plan.

---
## 6. Configuration & Environment Setup

1. **Install dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r nl2sql-proto/requirements.txt
   ```
2. **Ensure `.env` exists at repo root**
   ```bash
   cat .env
   # Fill in actual values
   GOOGLE_CLOUD_PROJECT=only-yours
   GOOGLE_CLOUD_LOCATION=us-central1
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASS=password
   ```
3. **Authenticate gcloud** (for Vertex AI)
   ```bash
   gcloud init
   gcloud auth application-default login
   gcloud services enable aiplatform.googleapis.com --project=only-yours
   ```
4. **Run loader** (populate Neo4j)
   ```bash
   python nl2sql-proto/schema_loader/load_schema_to_neo4j.py
   ```
5. **Run queries**
   ```bash
   python nl2sql-proto/app.py --q "Count customers by city"
   python nl2sql-proto/app.py --q "Show total spend per city for the last 30 days, top 5"
   ```

---
## 7. Error Modes & Safety Nets

| Stage | Example Failure | Handling |
|-------|-----------------|----------|
| Neo4j fetch | No table nodes found | Raises `ValueError("No table schema found")` |
| Gemini output | Non-JSON or missing fields | `_strip_markdown_fences` + `IR.model_validate_json` raises descriptive error |
| SQL rendering | (none – deterministic) | N/A |
| DuckDB verify | Syntax error (e.g., wrong date function) | Returns `{"ok": false, "message": ...}` |
| Credentials | Missing `.env` / ADC | `FileNotFoundError` or Vertex `PERMISSION_DENIED`; instructions in docs |

DuckDB verification deliberately doesn’t execute data. It enforces schema correctness (columns/types) and catches unsupported syntax early.

---
## 8. Extensibility Notes

1. **Multi-table joins**: Extend `schema.json` and Neo4j to include join metadata, update `IR` models to support `joins`, expand prompt instructions.
2. **Aliases / Business Terms**: Already partially supported via `aliases`. You can add nodes in Neo4j linking business terms to columns.
3. **Different LLM**: Swap `_invoke_gemini` for any other LLM client returning JSON. Just ensure `_strip_markdown_fences` still applies or adjust accordingly.
4. **Unit tests**: Add tests for `renderer.render_sql` and `tools.sql_verifier.verify_sql` to catch regressions.
5. **UI / API**: Wrap `run_nl_to_sql` inside FastAPI endpoints (a natural next step given `fastapi` is already in `requirements.txt`).

---
## 9. Quick Reference Table (Files → Functions)

| File | Key Function/Class | Purpose |
|------|--------------------|---------|
| `app.py` | `main()` | Parse CLI args, call agent, print output |
| `agent_chain.py` | `run_nl_to_sql()` | Orchestrate schema fetch → Gemini → IR → SQL → verify |
|  | `_invoke_gemini()` | Call Vertex AI with structured messages |
|  | `_strip_markdown_fences()` | Clean JSON emitted by Gemini |
|  | `get_schema_tool()` | LangChain tool to fetch schema from Neo4j |
| `prompts/planner_system.md` | (string) | System prompt for planner enforcing JSON IR |
| `schema_loader/schema.json` | (json) | Schema definition (dataset, table, columns) |
| `schema_loader/load_schema_to_neo4j.py` | `load_schema()` | Insert schema metadata into Neo4j |
| `tools/neo4j_schema_tool.py` | `fetch_table_schema()` | Return table/columns from Neo4j |
| `tools/sql_verifier.py` | `verify_sql()` | DuckDB in-memory `EXPLAIN` validation |
| `sql/ir_models.py` | `IR` (Pydantic model) | Defines allowed IR structure |
| `sql/renderer.py` | `render_sql()` | Deterministically render IR to DuckDB SQL |

---
## 10. Worked Example (End-to-End)

User runs:
```bash
python nl2sql-proto/app.py --q "Show total spend per city for the last 30 days, top 5"
```
Flow:
1. `app.py` → `run_nl_to_sql(query)`
2. `get_schema_tool.run("")` → JSON of `customers` table
3. `prompt.format_messages(...)` builds messages:
   - System: rules from `planner_system.md`
   - User: `{"natural_language_query": ..., "schema": ...}`
4. `_invoke_gemini()` → Gemini returns IR JSON (sometimes wrapped in ``` ``` so `_strip_markdown_fences` cleans it)
5. `IR.model_validate_json` validates it against Pydantic model (fails fast on hallucinated fields)
6. `render_sql(ir)` outputs SQL like:
   ```sql
   SELECT city AS "city", SUM(spend) AS "total_spend"
   FROM "customers"
   WHERE created_at >= CURRENT_DATE - INTERVAL 30 DAY
   GROUP BY "city"
   ORDER BY SUM(spend) DESC
   LIMIT 5;
   ```
7. `verify_sql` creates a DuckDB table with the schema and runs `EXPLAIN <SQL>`
8. CLI prints SQL, verifier JSON, IR JSON

If the SQL had used SQLite syntax (`DATE('now', '-30 days')`), `verify_sql` would return:
```json
{"ok": false, "message": "Parser Error: Wrong number of arguments provided to DATE function"}
```
This tells the user and us that Gemini’s suggestion needs a tweak (and we can adjust the prompt or post-process filters to fix it).

---
## 11. Troubleshooting Checklist

| Symptom | Fix |
|---------|-----|
| `Missing .env file...` | Create `.env` at repo root with credentials |
| `PERMISSION_DENIED` from Vertex | Run `gcloud auth application-default login`, ensure billing + Vertex AI API enabled |
| `Schema contains no columns` | Run loader script, check Neo4j credentials |
| `ValidationError: Invalid JSON` | Inspect Gemini’s output; adjust prompt or call `_strip_markdown_fences` |
| DuckDB errors about columns/types | Check that schema.json and Neo4j metadata match the actual table |

---
## 12. Suggested Enhancements

1. **Prompt tuning**: Add examples for date logic (e.g., `created_at >= CURRENT_DATE - INTERVAL 30 DAY`) so Gemini always uses DuckDB-friendly syntax.
2. **Better error UX**: Surface DuckDB errors alongside suggested fixes or fallback to safer defaults.
3. **Caching**: Cache Neo4j schema responses to avoid repeated database hits.
4. **Multi-table support**: Expand IR to handle joins (`joins: [...]`) and load join metadata into Neo4j.
5. **Testing**: Add pytest cases for IR validation, SQL rendering, and DuckDB verification with known fixtures.

---
## 13. TL;DR

- `app.py` drives everything.
- `agent_chain.py` choreographs schema fetch → LLM → IR → SQL → verification.
- Neo4j is the schema source of truth.
- Gemini plans queries using a strict JSON schema enforced by Pydantic.
- SQL is rendered deterministically and verified by DuckDB without touching real data.
- The CLI surfaces results + verification status, so users know whether the SQL is safe to run.

Keep this document handy as the living reference for how the NL→SQL agent is wired today. Update sections as you add tables, extend IR capabilities, or swap LLM providers.
