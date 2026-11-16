"""Exercise the MCP tools through the server's call_tool interface, as an agent would."""

import asyncio
import json

import pytest


@pytest.fixture
def mcp_module(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'mcp.db'}")
    monkeypatch.setenv("NUTRITION_USER_EMAIL", "agent@example.com")
    import importlib

    import mcp_server

    module = importlib.reload(mcp_server)
    with module.flask_app.app_context():
        from app import services

        services.register_user("agent@example.com", "password123")
    return module


def call(module, name, args):
    result = asyncio.run(module.mcp.call_tool(name, args))
    assert not result.is_error, result.content
    structured = result.structured_content
    if structured is not None:
        # Non-object return types are wrapped as {"result": ...}.
        return structured["result"] if set(structured) == {"result"} else structured
    return json.loads(result.content[0].text)


def test_tools_are_registered(mcp_module):
    tools = asyncio.run(mcp_module.mcp.list_tools())
    tools = getattr(tools, "tools", tools)
    names = {t.name for t in tools}
    assert {"search_foods", "log_meal", "add_custom_food", "get_meals", "daily_nutrition_summary"} <= names


def test_agent_logs_meal_by_name_and_reads_summary(mcp_module):
    foods = call(mcp_module, "search_foods", {"query": "banana"})
    assert foods and foods[0]["name"] == "Banana"

    meal = call(
        mcp_module,
        "log_meal",
        {"meal_type": "snack", "date": "2026-02-01", "items": [{"food_name": "banana", "servings": 2}]},
    )
    assert meal["totals"]["calories"] == 210

    summary = call(mcp_module, "daily_nutrition_summary", {"date": "2026-02-01"})
    assert summary["consumed"]["calories"] == 210
    assert summary["by_meal_type"]["snack"] == 210
