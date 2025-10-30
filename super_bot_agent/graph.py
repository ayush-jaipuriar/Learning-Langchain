"""LangGraph wiring for the single-node SuperBot Vertex agent."""

from __future__ import annotations

import logging
import time
from typing import Callable, Dict, List, Sequence

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import END, START, StateGraph

from .provider import build_vertex_chat_model
from .state import State

logger = logging.getLogger(__name__)

NODE_NAME = "super_bot"


def _message_text(message: BaseMessage) -> str:
    """Best-effort extraction of text content from a LangChain message."""

    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, Sequence):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                part = item.get("text")
                if isinstance(part, str):
                    parts.append(part)
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return str(content)


def _ensure_ai_message(message: BaseMessage | str) -> AIMessage:
    if isinstance(message, AIMessage):
        return message
    if isinstance(message, BaseMessage):
        return AIMessage(
            content=_message_text(message),
            additional_kwargs=getattr(message, "additional_kwargs", {}),
            response_metadata=getattr(message, "response_metadata", {}),
        )
    if isinstance(message, str):
        return AIMessage(content=message)
    return AIMessage(content=str(message))


def create_super_bot_node(llm: BaseChatModel) -> Callable[[State], Dict[str, List[BaseMessage]]]:
    """Create the callable executed by the SuperBot node."""

    def super_bot(state: State) -> Dict[str, List[BaseMessage]]:
        messages = state.get("messages", [])
        if not messages:
            raise ValueError(
                "SuperBot requires at least one message (the latest human turn) in state."
            )

        prompt_chars = sum(len(_message_text(msg)) for msg in messages)

        start_time = time.perf_counter()
        response = llm.invoke(messages)
        latency_ms = (time.perf_counter() - start_time) * 1000

        ai_message = _ensure_ai_message(response)
        response_chars = len(_message_text(ai_message))

        latest_human = next((msg for msg in reversed(messages) if msg.type == "human"), None)

        logger.info(
            "SuperBot turn complete",
            extra={
                "superbot_node": NODE_NAME,
                "vertex_model": getattr(getattr(llm, "config", {}), "model_name", None)
                or getattr(llm, "model_name", "unknown"),
                "prompt_chars": prompt_chars,
                "response_chars": response_chars,
                "latency_ms": round(latency_ms, 2),
                "latest_human_preview": (_message_text(latest_human)[:200] if latest_human else None),
            },
        )

        return {"messages": [ai_message]}

    return super_bot


def build_super_bot_graph(llm: BaseChatModel | None = None):
    """Compile the LangGraph workflow with the single SuperBot node."""

    llm_instance = llm or build_vertex_chat_model()

    workflow = StateGraph(State)
    workflow.add_node(NODE_NAME, create_super_bot_node(llm_instance))
    workflow.add_edge(START, NODE_NAME)
    workflow.add_edge(NODE_NAME, END)

    return workflow.compile()


__all__ = ["NODE_NAME", "build_super_bot_graph", "create_super_bot_node"]

