# NL2SQL Prototype Architecture Guide

## 1. What This Prototype Does
- Translates a user question written in everyday language into a DuckDB-compatible SQL query.
- Guarantees the query only references real tables/columns by consulting Neo4j for the official schema.
- Performs a dry-run verification against DuckDB to ensure the SQL parses and plans, without touching real data.
- Uses Google Vertex AI (Gemini 2.0 Flash) for planning so you can run without OpenAI credits.

Think of it as a friendly assistant with three talents: it remembers your table layout (via Neo4j), it plans a query carefully (via LangChain + an LLM), and it double-checks its work (via DuckDB).

## 2. Key Building Blocks

| Layer | Role | Where to look |
| --- | --- | --- |
| Data Sample | CSV used only for schema and future testing | `data/customers.csv` |
| Schema Definition | Canonical description of columns/types and aliases | `schema_loader/schema.json` |
| Loader Script | Pushes schema metadata into Neo4j | `schema_loader/load_schema_to_neo4j.py` |
| Neo4j Tool | Fetches table + column info for the agent | `tools/neo4j_schema_tool.py` |
| SQL Verifier | Creates empty DuckDB table and runs `EXPLAIN` | `tools/sql_verifier.py` |
| IR Models | Strict Pydantic models describing the query plan | `sql/ir_models.py` |
| SQL Renderer | Converts IR objects into final SQL strings | `sql/renderer.py` |
| Planner Prompt | Instructions that force the LLM to stay on-spec | `prompts/planner_system.md` |
| Planner Runtime | Gemini invocation helpers + message conversion | `agent_chain.py` |
| CLI Entry | User-facing entry point with text/JSON output | `app.py` |

## 3. How the Flow Works (Story Mode)
1. **Load schema once** – We run the loader script to populate Neo4j with the dataset, table, columns, data types, and nice-to-have aliases. Neo4j becomes the single source of truth.
2. **User asks a question** – For example, “Who are the top five spenders this month?”
3. **Agent grabs the schema** – Through the `get_schema` tool, the agent reads Neo4j and receives a JSON snippet listing only the allowed columns.
4. **LLM drafts an IR** – The Language Model must output JSON in the shape defined by `sql/ir_models.py`. This IR lists projections, filters, grouping, etc.
5. **Renderer builds SQL** – The IR is fed to `renderer.py`, which deterministically prints DuckDB SQL, quoting identifiers safely.
6. **DuckDB verifies** – `sql_verifier.py` spins up an in-memory DuckDB, creates an empty table with the correct columns/types, and runs `EXPLAIN` on the SQL. No data is read or modified.
7. **Result is returned** – The CLI prints the SQL, the verifier status, and the IR for transparency.

## 4. Why This Design Is Beginner-Friendly
- **Single table**: avoids join complexity while showcasing the pattern.
- **IR with Pydantic**: gives clear validation errors if the model returns bad JSON.
- **DuckDB verification**: quick feedback loop; you know immediately if a query is syntactically sound.
- **Neo4j as truth source**: easy mental model—whatever is in Neo4j is what the agent can see.

## 5. Configuration & Environment
- Environment variables live in `.env` (copy from `.env.example` if added):
  - `OPENAI_API_KEY`
  - `NEO4J_URI` (defaults to `bolt://localhost:7687`)
  - `NEO4J_USER` / `NEO4J_PASS`
- Dependencies listed in `requirements.txt`. A virtual environment keeps things tidy.
- DuckDB is bundled as a Python package; no separate server needed.

## 6. Schema Lifecycle
1. **Define** – Edit `schema_loader/schema.json` to describe datasets, tables, and columns.
2. **Load** – Run `python schema_loader/load_schema_to_neo4j.py` (after activating the venv). The script uses Cypher `MERGE` to insert or update nodes.
3. **Query** – When the agent runs, it pulls the latest schema; any change in Neo4j is reflected instantly.

Neo4j graph model basics:
- Nodes: `Dataset`, `Table`, `Column`.
- Relationships: `Dataset` -[:HAS_TABLE]-> `Table`; `Table` -[:HAS_COLUMN]-> `Column`.
- Columns optionally store alias lists to help the LLM relate user words to schema terms.

## 7. Agent Planning Details
- LangChain `ChatPromptTemplate` uses the markdown prompt (`planner_system.md`) as the system message.
- We convert formatted LangChain messages into Vertex AI `types.Content` objects so Gemini receives structured roles + text.
- The prompt enforces “JSON only” output—if Gemini slips, `IR.model_validate_json` raises an error.
- `agent_chain.py` guards against missing columns and non-string responses to keep failures obvious.

## 8. SQL Rendering & Verification
- `sql/renderer.py` quotes identifiers with double quotes to follow DuckDB conventions.
- Group-by and order-by clauses are sanity-checked to avoid accidental quoting of expressions.
- `sql_verifier.py` builds `CREATE TABLE` statements from the schema and runs `EXPLAIN <SQL>` to confirm the plan.
- If verification fails, the error message from DuckDB is bubbled up so users see what went wrong.

## 9. Step-by-Step Setup & Testing (Beginner Friendly)
1. **Install Python 3.11+** (3.13 used here).
2. **Create a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r nl2sql-proto/requirements.txt
   ```
3. **Set environment variables** (temporary shell vars or a `.env` file):
   ```bash
   export GOOGLE_CLOUD_API_KEY="your-google-key"
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_USER="neo4j"
   export NEO4J_PASS="password"
   ```
4. **Ensure Neo4j is running** (Desktop app or server). Default creds match the loader defaults.
5. **Load the schema**:
   ```bash
   python nl2sql-proto/schema_loader/load_schema_to_neo4j.py
   ```
   You should see “Schema loaded into Neo4j ✅”. In Neo4j Browser, run `MATCH (n) RETURN n` to confirm nodes.
6. **Run a sample question**:
   ```bash
   python nl2sql-proto/app.py --q "Show total spend per city for the last 30 days, top 5"
   ```
   - The CLI prints SQL, verifier status, and the IR JSON.
   - To integrate with other tools, add `--format json` for machine-readable output.
7. **Try more queries** from the test matrix in the PRD:
   - “List all columns”
   - “Customers in Hyderabad”
   - “Count customers by city”
   Watch how the IR changes and how the SQL verifier responds.

## 10. Troubleshooting Tips
- **Missing schema**: Loader not run or Neo4j credentials wrong; the agent will raise `Schema contains no columns`.
- **Validation errors**: If the LLM returns malformed JSON, the script will fail fast—re-run after checking logs.
- **Gemini quota/auth errors**: Ensure `GOOGLE_CLOUD_API_KEY` is set and the Vertex project has access to `gemini-2.0-flash-001`.
- **DuckDB errors**: The verifier message usually pinpoints unknown columns or syntax issues.
- **Environment errors**: Ensure the virtual environment is activated before running scripts.

## 11. Future Enhancements
- Add automated tests for renderer + verifier edge cases.
- Extend schema model to multiple tables and join relationships.
- Introduce vector similarity or BusinessTerm nodes in Neo4j for richer NL understanding.
- Swap models by pointing the Gemini client at a different Vertex AI deployment.

Keep this guide nearby when onboarding new contributors—they can understand the “why” and “how” without diving into every line of code.
