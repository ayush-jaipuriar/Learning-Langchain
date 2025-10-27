# Iteration Log

## 2025-10-22 – Project Overview Analysis
- **Summary:** Reviewed repository structure and key scripts to prepare a high-level documentation of the LangChain learning project.
- **Files referenced:** `README.md`, `app.py`, `data_ingestion.py`, `text_splitting.py`, `demo_text_splitting.py`, `demo_openai_embeddings.py`, `openai_faiss_pipeline.py`, `demo_json_splitting.py`, `web_rag_pipeline.py`, `vertex_rag_pipeline.py`, contents of `food_delivery_agent/`, and supporting markdown files in the root directory.
- **Changes made:** No code modifications performed; analysis only.
- **Next steps:**
  - Build out the food delivery LangGraph agent by defining nodes, tools, and graph wiring.
  - Add automated tests or notebooks demonstrating each pipeline end-to-end.
  - Document environment setup nuances for OpenAI vs Vertex AI usage.

## 2025-10-26 – NL2SQL Prototype Scaffold
- **Summary:** Implemented the first working slice of the NL2SQL prototype, including schema ingestion, agent chain wiring, SQL rendering, and verifier integration per the PRD.
- **Files added/updated:**
  - `nl2sql-proto/data/customers.csv` – sample dataset for DuckDB schema validation.
  - `nl2sql-proto/schema_loader/schema.json` & `load_schema_to_neo4j.py` – schema definition and Neo4j loader.
  - `nl2sql-proto/tools/neo4j_schema_tool.py`, `sql_verifier.py` – schema retrieval and DuckDB SQL verification tools.
  - `nl2sql-proto/sql/ir_models.py`, `renderer.py` – Pydantic IR models and deterministic SQL renderer.
  - `nl2sql-proto/prompts/planner_system.md` – planner system instructions consumed at runtime.
  - `nl2sql-proto/agent_chain.py`, `app.py` – LangChain agent orchestration and CLI entry point with JSON/text output modes.
  - `nl2sql-proto/requirements.txt` – dependency manifest.
- **Theory & reasoning highlights:** Applied graph-backed schema governance for tool-grounded planning, enforced IR strictness with Pydantic, and ensured SQL safety via DuckDB EXPLAIN-only validation. Loader consolidates schema canonicalization in Neo4j, while the agent ensures runtime schema retrieval to mitigate hallucinations.
- **Next steps:**
  - Add automated tests for IR rendering and SQL verifier edge cases.
  - Extend agent with join-aware IR once multi-table schema is ingested.
  - Replace inline prompt string reads with cached loader or environment-specific overrides.

## 2025-10-26 – Vertex AI Planner Migration
- **Summary:** Swapped the NL→SQL agent from OpenAI to Google Vertex AI (Gemini) to avoid expired OpenAI credits and wired in a reusable Gemini invocation helper.
- **Files added/updated:**
  - `nl2sql-proto/agent_chain.py` – replaced LangChain `ChatOpenAI` with a direct Gemini client, added message conversion helpers and `.env` bootstrapping for `GOOGLE_CLOUD_API_KEY`.
  - `nl2sql-proto/requirements.txt` – added `google-genai` dependency.
- **Theory & reasoning highlights:** Gemini is called via the `google-genai` Vertex interface enabling on-demand model swaps without LangChain wrappers; templated system prompt now flows through runnable conversion; `.env` scaffolding teaches users to inject Google credentials safely.
- **Next steps:**
  - Add tests/mocks to validate Gemini response parsing without live API calls.
  - Update other scripts to share the same environment loader if Vertex usage becomes standard.
  - Consider a configuration flag to toggle between providers.


