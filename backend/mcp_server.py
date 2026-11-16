"""MCP server exposing the tracker's database to LLM agents.

Tools act on behalf of one user, chosen with the NUTRITION_USER_EMAIL environment variable,
so an agent can log meals and query nutrition data just like the web app.

    NUTRITION_USER_EMAIL=you@example.com python mcp_server.py
"""

import os

from mcp.server.mcpserver import MCPServer
from sqlalchemy import select

from app import create_app, services
from app.extensions import db
from app.models import User

flask_app = create_app()
mcp = MCPServer(
    name="nutrition-tracker",
    instructions=(
        "Tools for a personal nutrition and fitness log. Search foods before logging so you use "
        "catalog names. Dates are YYYY-MM-DD and default to today."
    ),
)


def _current_user_id():
    email = os.environ.get("NUTRITION_USER_EMAIL", "").strip().lower()
    if not email:
        raise RuntimeError("Set NUTRITION_USER_EMAIL to the account the agent should act for.")
    user_id = db.session.scalar(select(User.id).where(User.email == email))
    if user_id is None:
        raise RuntimeError(f"No user with email {email!r}. Register in the web app first.")
    return user_id


@mcp.tool()
def search_foods(query: str, limit: int = 10) -> list[dict]:
    """Search the food catalog (plus the user's custom foods) by name. Returns per-serving nutrition."""
    with flask_app.app_context():
        return [f.to_dict() for f in services.search_foods(_current_user_id(), query, min(limit, 50))]


@mcp.tool()
def log_meal(meal_type: str, items: list[dict], date: str | None = None, notes: str | None = None) -> dict:
    """Log a meal.

    meal_type: breakfast, lunch, dinner, or snack.
    items: list of {"food_name": str, "servings": float} or {"food_id": int, "servings": float}.
    date: YYYY-MM-DD, defaults to today.
    """
    with flask_app.app_context():
        return services.log_meal(_current_user_id(), meal_type, items, date, notes).to_dict()


@mcp.tool()
def add_custom_food(
    name: str,
    calories: float,
    protein_g: float = 0,
    carbs_g: float = 0,
    fat_g: float = 0,
    fiber_g: float = 0,
    serving_size: str = "1 serving",
) -> dict:
    """Create a custom food for this user when it isn't in the catalog."""
    with flask_app.app_context():
        data = dict(
            name=name,
            calories=calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fat_g=fat_g,
            fiber_g=fiber_g,
            serving_size=serving_size,
        )
        return services.create_food(_current_user_id(), data).to_dict()


@mcp.tool()
def get_meals(date: str | None = None) -> list[dict]:
    """List the meals logged on a date (default today) with per-item and per-meal nutrition."""
    with flask_app.app_context():
        return [m.to_dict() for m in services.meals_on(_current_user_id(), services.parse_date(date))]


@mcp.tool()
def daily_nutrition_summary(date: str | None = None) -> dict:
    """Totals for a day: calories and macros consumed, calories burned, goals, and remaining calories."""
    with flask_app.app_context():
        return services.daily_summary(_current_user_id(), services.parse_date(date))


if __name__ == "__main__":
    mcp.run()
