"""Unit tests for the Vertex-backed SuperBot agent."""

from __future__ import annotations

from typing import List

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from super_bot_agent import (
    NODE_NAME,
    SuperBotConfigError,
    VertexConfig,
    build_super_bot_graph,
)
from super_bot_agent.graph import create_super_bot_node


class StubChatModel:
    """Minimal stub implementing an invoke method for tests."""

    def __init__(self, responses: List[str]):
        self._responses = responses
        self._calls = 0

    def invoke(self, messages):  # noqa: D401 - LangChain-like interface
        """Return the next canned response wrapped as an AIMessage."""

        response = self._responses[self._calls % len(self._responses)]
        self._calls += 1
        return AIMessage(content=response)


def test_super_bot_node_appends_assistant_turn():
    node = create_super_bot_node(StubChatModel(["hello"]))
    initial_state = {"messages": [HumanMessage(content="Hi there")]}  # type: ignore[arg-type]

    result = node(initial_state)

    assert "messages" in result
    assert len(result["messages"]) == 1
    assert result["messages"][0].content == "hello"


def test_graph_invoke_accumulates_messages():
    stub_llm = StubChatModel(["first", "second"])
    graph = build_super_bot_graph(stub_llm)

    turn_one = graph.invoke({"messages": [HumanMessage(content="Hi")]})
    assert [msg.type for msg in turn_one["messages"]] == ["human", "ai"]

    follow_up_messages = turn_one["messages"] + [HumanMessage(content="And now?")]
    turn_two = graph.invoke({"messages": follow_up_messages})

    assert [msg.type for msg in turn_two["messages"]][-2:] == ["human", "ai"]
    assert turn_two["messages"][-1].content == "second"


def test_graph_wiring_contains_single_node():
    graph = build_super_bot_graph(StubChatModel(["ok"]))
    compiled = graph.get_graph()
    user_nodes = {node for node in compiled.nodes if not node.startswith("__")}
    assert user_nodes == {NODE_NAME}
    edges = set(compiled.edges)
    assert ("__start__", NODE_NAME) in edges
    assert (NODE_NAME, "__end__") in edges


def test_vertex_config_requires_project(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    monkeypatch.setenv("GCP_LOCATION", "us-central1")

    with pytest.raises(SuperBotConfigError):
        VertexConfig.from_env()


def test_vertex_config_requires_location(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GCP_PROJECT_ID", "project-123")
    monkeypatch.delenv("GCP_LOCATION", raising=False)

    with pytest.raises(SuperBotConfigError):
        VertexConfig.from_env()

