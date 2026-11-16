# Nutrition & Fitness Tracker

A full-stack app for logging meals and workouts against daily calorie and macro goals. It includes an **MCP server**, so LLM agents such as Claude can log meals and query nutrition data straight from the database.

**Stack:** React (Vite) · Python · Flask · PostgreSQL · SQLAlchemy · REST · MCP · Docker

## Features

- **RESTful Flask API** with JWT authentication, meal logging, food search, workouts, and daily summaries.
- **PostgreSQL relational schema:** `users`, `profiles` (goals and body stats), `foods` (a shared catalog plus each user's private custom foods), `meals`, `meal_items`, and `workouts`, with check constraints and per-user date indexes.
- **React dashboard:** calories eaten, burned, and remaining; macro progress bars; food search with autocomplete; and day-by-day meal and workout logs.
- **MCP server** (`backend/mcp_server.py`) with database-backed tools:

| Tool | What it does |
| --- | --- |
| `search_foods` | Search the catalog and the user's custom foods |
| `log_meal` | Log a meal by food name or ID, with servings |
| `add_custom_food` | Add a food that isn't in the catalog |
| `get_meals` | List meals for a date with nutrition totals |
| `daily_nutrition_summary` | Calories and macros consumed vs. goals, calories burned, and remaining |

## Run with Docker

```bash
docker compose up --build
```

- App: http://localhost:8080
- API: http://localhost:5000/api

## Run locally

```bash
# backend (SQLite by default; set DATABASE_URL for Postgres)
cd backend
python -m venv .venv && .venv/Scripts/activate   # or: source .venv/bin/activate
pip install -r requirements.txt
python wsgi.py                                    # http://localhost:5000

# frontend (separate terminal)
cd frontend
npm install
npm run dev                                       # http://localhost:5173, proxies /api to :5000
```

The food catalog is seeded automatically on first start.

## Connect the MCP server to Claude

Register an account in the web app first. The MCP server acts on behalf of that user.

**Claude Code:**

```bash
claude mcp add nutrition --env NUTRITION_USER_EMAIL=you@example.com --env DATABASE_URL=sqlite:///absolute/path/to/backend/nutrition.db -- /path/to/backend/.venv/bin/python /path/to/backend/mcp_server.py
```

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "nutrition": {
      "command": "/path/to/backend/.venv/bin/python",
      "args": ["/path/to/backend/mcp_server.py"],
      "env": {
        "NUTRITION_USER_EMAIL": "you@example.com",
        "DATABASE_URL": "postgresql://nutrition:nutrition@localhost:5432/nutrition"
      }
    }
  }
}
```

Then ask: *"Log two eggs and a cup of oatmeal for breakfast, then tell me how much protein I have left today."*

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/auth/register`, `/api/auth/login` | Returns a JWT |
| GET | `/api/auth/me` | Current user and profile |
| GET/PATCH | `/api/profile` | Goals and body stats |
| GET | `/api/foods?q=` | Search foods |
| POST | `/api/foods` | Create a custom food |
| GET | `/api/meals?date=` or `?start=&end=` | List meals |
| POST | `/api/meals` | `{meal_type, eaten_on, items: [{food_id, servings}]}` |
| GET/DELETE | `/api/meals/{id}` | Read or delete one meal |
| GET/POST | `/api/workouts` | List or log workouts |
| DELETE | `/api/workouts/{id}` | Delete a workout |
| GET | `/api/summary/daily?date=` | Daily totals vs. goals |

## Tests

```bash
cd backend && pytest -q
```

The tests cover auth, validation, meal and summary math, per-user data isolation, and MCP tool calls.
