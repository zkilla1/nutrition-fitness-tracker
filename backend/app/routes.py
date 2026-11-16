from flask import Blueprint, abort, g, jsonify, request
from sqlalchemy import select

from . import services
from .auth import issue_token, login_required
from .extensions import db
from .models import Meal, User, Workout
from .services import ValidationError

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")
foods_bp = Blueprint("foods", __name__, url_prefix="/api/foods")
meals_bp = Blueprint("meals", __name__, url_prefix="/api/meals")
workouts_bp = Blueprint("workouts", __name__, url_prefix="/api/workouts")
summary_bp = Blueprint("summary", __name__, url_prefix="/api/summary")


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, "expected a JSON object body")
    return data


for bp in (auth_bp, profile_bp, foods_bp, meals_bp, workouts_bp, summary_bp):
    bp.register_error_handler(ValidationError, lambda e: (jsonify(error=str(e)), 400))


# --- auth -------------------------------------------------------------------

@auth_bp.post("/register")
def register():
    data = body()
    user = services.register_user(data.get("email"), data.get("password"))
    return {"token": issue_token(user), "user": {"id": user.id, "email": user.email}}, 201


@auth_bp.post("/login")
def login():
    data = body()
    user = db.session.scalar(select(User).where(User.email == (data.get("email") or "").strip().lower()))
    if user is None or not user.check_password(data.get("password") or ""):
        abort(401, "invalid email or password")
    return {"token": issue_token(user), "user": {"id": user.id, "email": user.email}}


@auth_bp.get("/me")
@login_required
def me():
    return {"id": g.user.id, "email": g.user.email, "profile": services.get_profile(g.user.id).to_dict()}


# --- profile ----------------------------------------------------------------

PROFILE_FIELDS = {
    "display_name": str,
    "height_cm": float,
    "weight_kg": float,
    "calorie_goal": int,
    "protein_goal_g": int,
    "carbs_goal_g": int,
    "fat_goal_g": int,
}


@profile_bp.get("")
@login_required
def get_profile():
    return services.get_profile(g.user.id).to_dict()


@profile_bp.patch("")
@login_required
def update_profile():
    profile = services.get_profile(g.user.id)
    data = body()
    for field, cast in PROFILE_FIELDS.items():
        if field in data:
            value = data[field]
            try:
                setattr(profile, field, None if value is None else cast(value))
            except (TypeError, ValueError):
                raise ValidationError(f"invalid value for {field}")
    db.session.commit()
    return profile.to_dict()


# --- foods ------------------------------------------------------------------

@foods_bp.get("")
@login_required
def list_foods():
    limit = min(int(request.args.get("limit", 20)), 100)
    return {"foods": [f.to_dict() for f in services.search_foods(g.user.id, request.args.get("q", ""), limit)]}


@foods_bp.post("")
@login_required
def create_food():
    return services.create_food(g.user.id, body()).to_dict(), 201


# --- meals ------------------------------------------------------------------

def own_meal(meal_id):
    meal = db.session.get(Meal, meal_id)
    if meal is None or meal.user_id != g.user.id:
        abort(404, "meal not found")
    return meal


@meals_bp.get("")
@login_required
def list_meals():
    if "date" in request.args or not any(k in request.args for k in ("start", "end")):
        meals = services.meals_on(g.user.id, services.parse_date(request.args.get("date")))
    else:
        start = services.parse_date(request.args.get("start"), default_today=False)
        end = services.parse_date(request.args.get("end"))
        meals = db.session.scalars(
            select(Meal)
            .where(Meal.user_id == g.user.id, Meal.eaten_on.between(start, end))
            .order_by(Meal.eaten_on, Meal.created_at)
        ).all()
    return {"meals": [m.to_dict() for m in meals]}


@meals_bp.post("")
@login_required
def create_meal():
    data = body()
    meal = services.log_meal(
        g.user.id, data.get("meal_type"), data.get("items") or [], data.get("eaten_on"), data.get("notes")
    )
    return meal.to_dict(), 201


@meals_bp.get("/<int:meal_id>")
@login_required
def get_meal(meal_id):
    return own_meal(meal_id).to_dict()


@meals_bp.delete("/<int:meal_id>")
@login_required
def delete_meal(meal_id):
    db.session.delete(own_meal(meal_id))
    db.session.commit()
    return "", 204


# --- workouts ---------------------------------------------------------------

@workouts_bp.get("")
@login_required
def list_workouts():
    day = services.parse_date(request.args.get("date"))
    rows = db.session.scalars(select(Workout).where(Workout.user_id == g.user.id, Workout.performed_on == day)).all()
    return {"workouts": [w.to_dict() for w in rows]}


@workouts_bp.post("")
@login_required
def create_workout():
    data = body()
    try:
        workout = Workout(
            user_id=g.user.id,
            activity=str(data["activity"]).strip(),
            duration_min=int(data["duration_min"]),
            calories_burned=int(data.get("calories_burned", 0)),
            performed_on=services.parse_date(data.get("performed_on")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationError(f"invalid workout: {exc}")
    if workout.duration_min <= 0 or workout.calories_burned < 0:
        raise ValidationError("duration must be positive and calories non-negative")
    db.session.add(workout)
    db.session.commit()
    return workout.to_dict(), 201


@workouts_bp.delete("/<int:workout_id>")
@login_required
def delete_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None or workout.user_id != g.user.id:
        abort(404, "workout not found")
    db.session.delete(workout)
    db.session.commit()
    return "", 204


# --- summary ----------------------------------------------------------------

@summary_bp.get("/daily")
@login_required
def daily():
    return services.daily_summary(g.user.id, services.parse_date(request.args.get("date")))
