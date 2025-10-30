# SuperBot – Vertex LangGraph Architecture

## Overview
SuperBot is a single-node LangGraph chatbot backed exclusively by Google Vertex AI. It exists as a teaching implementation that highlights reducer-managed state, provider abstraction, invoke vs. streaming execution, and configuration hygiene for cloud-hosted LLMs. All logic lives under `super_bot_agent/` and reuses the same building blocks for the CLI, notebook, and tests.

## State & Reducer
- **Schema:** `super_bot_agent/state.py` defines a `TypedDict` with `messages: Annotated[List[BaseMessage], add_messages]`.
- **Semantics:** `add_messages` guarantees append-only behavior so both human and assistant turns survive every run. LangGraph merges the node output (`{"messages": [AIMessage]}`) back into state.
- **Why it matters:** Reducer wiring makes the notebook demonstrations of `stream_mode="values"` more illustrative because snapshots show message accumulation rather than replacement.

## Provider Abstraction
- **Module:** `super_bot_agent/provider.py`
- **Validation:** `VertexConfig.from_env()` pulls `GCP_PROJECT_ID`, `GCP_LOCATION`, `VERTEX_MODEL`, `VERTEX_TEMPERATURE`, and `VERTEX_MAX_OUTPUT_TOKENS`, raising descriptive `SuperBotConfigError` exceptions if anything is missing or malformed.
- **Instantiation:** `build_vertex_chat_model()` wraps `langchain-google-vertexai.ChatVertexAI`, logging project/model metadata while surfacing initialization failures as `SuperBotProviderError`.
- **Auth Model:** Relies on Google Application Default Credentials (ADC). The environment template (`configs/superbot.env.example`) documents the required keys and reminders to run `gcloud auth application-default login`.

## Graph Wiring
- **Module:** `super_bot_agent/graph.py`
- **Node:** `create_super_bot_node(llm)` reads the full conversational history, invokes the supplied `ChatVertexAI`, logs prompt/response character counts, and returns only the assistant turn for reducer merging.
- **Workflow:** `build_super_bot_graph()` compiles a `StateGraph` with `START → super_bot → END`, keeping the node injectable for tests or alternative providers.
- **Instrumentation:** Latency (ms) and short human-message previews are emitted at `INFO` level for observability without storing sensitive content.

## Execution Surfaces
- **CLI:** `super_bot_agent/cli.py` exposes `invoke` and `stream` modes with optional `--stream-mode={updates,values}` and `--env-file` flags. It autodetects `SUPERBOT_LOG_LEVEL` and returns friendly exit codes for configuration vs. provider errors.
- **Script Entry Point:** `super_bot.py` simply proxies to the CLI so `python super_bot.py --mode stream` works out of the box.
- **Notebook:** `notebooks/chatbot.ipynb` walks learners through env loading, state inspection, graph compilation, topology visualization, invoke execution, and both streaming modes.

## Testing Strategy
- **Location:** `tests/super_bot/test_super_bot.py`
- **Coverage:** Ensures the node appends assistant turns, the graph accumulates messages across invocations, the wiring only includes the single `super_bot` node, and `VertexConfig` enforces project/location requirements via `pytest` and lightweight stubs.
- **Approach:** Uses a deterministic `StubChatModel` to avoid real Vertex calls while exercising the same API surface as the production graph.

## Configuration Quickstart
1. Copy `configs/superbot.env.example` to `.env` and fill in project details.
2. Run `gcloud auth application-default login` if ADC is not set up.
3. Install dependencies with `pip install -r requirements.txt`.
4. Execute `python super_bot.py --prompt "Hello"` to run a single invoke turn.
5. Switch streaming modes via `--mode stream --stream-mode values` to observe reducer snapshots.

## Future Enhancements
- Introduce a provider registry to support fallbacks without changing graph code.
- Layer in telemetry exporters (e.g., LangSmith traces) to persist the logged metadata externally.
- Experiment with multi-node compositions (planner, tool nodes) once the single-node example is mastered.

