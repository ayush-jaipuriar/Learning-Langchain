"""Command-line interface for the Vertex-powered SuperBot agent."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Iterable, Mapping

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from . import (
    SuperBotConfigError,
    SuperBotProviderError,
    build_super_bot_graph,
    build_vertex_chat_model,
)


logger = logging.getLogger(__name__)


def _resolve_log_level(env_value: str | None) -> int:
    levels: Mapping[str, int] = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }
    return levels.get((env_value or "INFO").upper(), logging.INFO)


def _configure_logging(env_level: str | None) -> None:
    logging.basicConfig(
        level=_resolve_log_level(env_level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )


def _stream_updates(graph, payload, stream_mode: str) -> None:
    print(f"\n--- Streaming (mode={stream_mode}) ---")
    for idx, event in enumerate(graph.stream(payload, stream_mode=stream_mode), start=1):
        print(f"Event {idx}: {event}")


def _stream_values(graph, payload) -> None:
    print("\n--- Streaming (mode=values) ---")
    for idx, snapshot in enumerate(graph.stream(payload, stream_mode="values"), start=1):
        node_state = snapshot.get("super_bot", {})
        print(f"Snapshot {idx}:")
        messages = node_state.get("messages", [])
        for message in messages:
            print(f"  [{message.type}] {_safe_message_content(message)}")


def _safe_message_content(message) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        fragments = []
        for part in content:
            if isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str):
                    fragments.append(text)
            elif isinstance(part, str):
                fragments.append(part)
        return "".join(fragments)
    return str(content)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interact with the Vertex-backed SuperBot agent.")
    parser.add_argument(
        "--prompt",
        default="Hello SuperBot!",
        help="Text passed as the human turn to the agent.",
    )
    parser.add_argument(
        "--mode",
        choices=["invoke", "stream"],
        default="invoke",
        help="Whether to run a one-shot invoke or demonstrate streaming.",
    )
    parser.add_argument(
        "--stream-mode",
        choices=["updates", "values"],
        default="updates",
        help="Stream mode to use when --mode=stream.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Optional path to a dotenv file containing Vertex configuration.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    env_path = Path(args.env_file)
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    _configure_logging(os.getenv("SUPERBOT_LOG_LEVEL"))

    try:
        # Build the underlying LLM early so configuration issues surface fast.
        llm = build_vertex_chat_model()
        graph = build_super_bot_graph(llm)
    except SuperBotConfigError as exc:
        logger.error("Configuration error: %s", exc)
        return 2
    except SuperBotProviderError as exc:
        logger.error("Vertex provider initialization failed: %s", exc)
        return 3

    payload = {"messages": [HumanMessage(content=args.prompt)]}

    if args.mode == "invoke":
        result = graph.invoke(payload)
        print("\n--- Invoke Result ---")
        for message in result["messages"]:
            print(f"[{message.type}] {_safe_message_content(message)}")
        return 0

    if args.stream_mode == "updates":
        _stream_updates(graph, payload, stream_mode="updates")
    else:
        _stream_values(graph, payload)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

