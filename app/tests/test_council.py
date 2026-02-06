import asyncio

import httpx

from app.core.branching import ConversationTree
from app.core.council import aggregate_rankings, parse_ranking
from app.core.models.providers import AsyncProviderClient
from app.core.types import ConversationNode, LLMResult, Stage2Review


def test_parse_ranking_strict():
    text = """analysis\nFINAL RANKING:\n1. Response C\n2. Response A\n3. Response B"""
    assert parse_ranking(text) == ["C", "A", "B"]


def test_aggregate_rankings_avg():
    labels = {
        "A": LLMResult("gpt", "m1", "x", None, 10),
        "B": LLMResult("groq", "m2", "y", None, 10),
    }
    reviews = [
        Stage2Review("gpt", "m1", "", ["A", "B"]),
        Stage2Review("groq", "m2", "", ["B", "A"]),
    ]
    agg = aggregate_rankings(reviews, labels)
    assert set(agg.aggregate_order) == {"A", "B"}
    assert agg.label_to_model["A"] == "gpt/m1"


def test_tree_ops():
    tree = ConversationTree()
    n1 = ConversationNode.new("user", "q1")
    tree.add_node(n1)
    n2 = ConversationNode.new("assistant", "a1", n1.id)
    tree.add_node(n2)
    tree.set_active(n1.id)
    n3 = ConversationNode.new("user", "q2", n1.id)
    tree.add_node(n3)
    lineage = tree.lineage(n3.id)
    assert [n.content for n in lineage] == ["q1", "q2"]


def test_chat_returns_config_error_without_api_key():
    client = AsyncProviderClient("gpt", "https://api.openai.com/v1", None)
    result = asyncio.run(client.chat("gpt-4o-mini", [{"role": "user", "content": "ping"}], 1))
    assert result.error == "api key is not configured"
    assert result.latency_ms == 0


def test_safe_json_returns_raw_when_non_json_response():
    request = httpx.Request("POST", "https://example.com")
    response = httpx.Response(401, request=request, text="Unauthorized")
    parsed = AsyncProviderClient._safe_json(response)
    assert parsed == {"raw": "Unauthorized"}
