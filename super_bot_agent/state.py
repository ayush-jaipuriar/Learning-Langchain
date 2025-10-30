"""Conversation state schema for the SuperBot LangGraph agent."""

from typing import Annotated, List, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class State(TypedDict):
    """Graph state: append-only message list managed by LangGraph reducers."""

    messages: Annotated[List[BaseMessage], add_messages]


__all__ = ["State"]

