"""Business logic shared by the REST API and the MCP server."""

from datetime import date

from sqlalchemy import or_, select

from .extensions import db
from .models import MEAL_TYPES, Food, Meal, MealItem, Profile, User, Workout


class ValidationError(ValueError):
    pass


def parse_date(value, default_today=True):
    if value in (None, ""):
        if default_today:
            return date.today()
        raise ValidationError("date is required")
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValidationError(f"invalid date {value!r}, expected YYYY-MM-DD")


def visible_foods(user_id):
    return select(Food).where(or_(Food.owner_id.is_(None), Food.owner_id == user_id))


def search_foods(user_id, query="", limit=20):
    stmt = visible_foods(user_id)
    if query:
        stmt = stmt.where(Food.name.ilike(f"%{query}%"))
    return db.session.scalars(stmt.order_by(Food.name).limit(limit)).all()


def get_visible_food(user_id, food_id):
    food = db.session.scalar(visible_foods(user_id).where(Food.id == food_id))
    if food is None:
        raise ValidationError(f"food {food_id} not found")
    return food


def find_food_by_name(user_id, name):
    """Exact (case-insensitive) match first, then the shortest partial match."""
    exact = db.session.scalar(visible_foods(user_id).where(Food.name.ilike(name)))
    if exact:
        return exact
    matches = search_foods(user_id, name, limit=50)
    if not matches:
        raise ValidationError(f"no food matching {name!r}")
    return min(matches, key=lambda f: len(f.name))


def create_food(user_id, data):
    try:
        food = Food(
            name=str(data["name"]).strip(),
            serving_size=data.get("serving_size") or "1 serving",
            calories=float(data["calories"]),
            protein_g=float(data.get("protein_g", 0)),
            carbs_g=float(data.get("carbs_g", 0)),
            fat_g=float(data.get("fat_g", 0)),
            fiber_g=float(data.get("fiber_g", 0)),
            owner_id=user_id,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError(f"invalid food: {exc}")
    if not food.name:
        raise ValidationError("name is required")
    if min(food.calories, food.protein_g, food.carbs_g, food.fat_g, food.fiber_g) < 0:
        raise ValidationError("nutrition values must be non-negative")
    db.session.add(food)
    db.session.commit()
    return food


def log_meal(user_id, meal_type, items, eaten_on=None, notes=None):
    """items: [{"food_id": int, "servings": float}] (food_id may be replaced by "food_name")."""
    meal_type = (meal_type or "").lower()
    if meal_type not in MEAL_TYPES:
        raise ValidationError(f"meal_type must be one of {', '.join(MEAL_TYPES)}")
    if not items:
        raise ValidationError("a meal needs at least one item")

    meal = Meal(user_id=user_id, meal_type=meal_type, eaten_on=parse_date(eaten_on), notes=notes)
    for item in items:
        servings = float(item.get("servings", 1))
        if servings <= 0:
            raise ValidationError("servings must be positive")
        if "food_id" in item:
            food = get_visible_food(user_id, int(item["food_id"]))
        elif "food_name" in item:
            food = find_food_by_name(user_id, item["food_name"])
        else:
            raise ValidationError("each item needs food_id or food_name")
        meal.items.append(MealItem(food=food, servings=servings))

    db.session.add(meal)
    db.session.commit()
    return meal


def meals_on(user_id, day):
    return db.session.scalars(
        select(Meal).where(Meal.user_id == user_id, Meal.eaten_on == day).order_by(Meal.created_at)
    ).all()


def get_profile(user_id):
    profile = db.session.scalar(select(Profile).where(Profile.user_id == user_id))
    if profile is None:
        profile = Profile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()
    return profile


def daily_summary(user_id, day):
    meals = meals_on(user_id, day)
    workouts = db.session.scalars(
        select(Workout).where(Workout.user_id == user_id, Workout.performed_on == day)
    ).all()
    profile = get_profile(user_id)

    keys = ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g")
    consumed = {k: round(sum(m.totals()[k] for m in meals), 1) for k in keys}
    burned = sum(w.calories_burned for w in workouts)
    goals = {
        "calories": profile.calorie_goal,
        "protein_g": profile.protein_goal_g,
        "carbs_g": profile.carbs_goal_g,
        "fat_g": profile.fat_goal_g,
    }
    return {
        "date": day.isoformat(),
        "consumed": consumed,
        "calories_burned": burned,
        "net_calories": round(consumed["calories"] - burned, 1),
        "goals": goals,
        "remaining_calories": round(goals["calories"] - consumed["calories"] + burned, 1),
        "meal_count": len(meals),
        "by_meal_type": {
            t: round(sum(m.totals()["calories"] for m in meals if m.meal_type == t), 1) for t in MEAL_TYPES
        },
        "workouts": [w.to_dict() for w in workouts],
    }


def register_user(email, password):
    email = (email or "").strip().lower()
    if "@" not in email:
        raise ValidationError("a valid email is required")
    if len(password or "") < 8:
        raise ValidationError("password must be at least 8 characters")
    if db.session.scalar(select(User).where(User.email == email)):
        raise ValidationError("email already registered")
    user = User(email=email)
    user.set_password(password)
    user.profile = Profile()
    db.session.add(user)
    db.session.commit()
    return user
