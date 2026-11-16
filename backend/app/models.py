from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    meals: Mapped[list["Meal"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Profile(db.Model):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(100))
    height_cm: Mapped[float | None]
    weight_kg: Mapped[float | None]
    calorie_goal: Mapped[int] = mapped_column(default=2000)
    protein_goal_g: Mapped[int] = mapped_column(default=150)
    carbs_goal_g: Mapped[int] = mapped_column(default=200)
    fat_goal_g: Mapped[int] = mapped_column(default=65)

    user: Mapped[User] = relationship(back_populates="profile")

    def to_dict(self):
        return {
            "display_name": self.display_name,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "calorie_goal": self.calorie_goal,
            "protein_goal_g": self.protein_goal_g,
            "carbs_goal_g": self.carbs_goal_g,
            "fat_goal_g": self.fat_goal_g,
        }


class Food(db.Model):
    """Nutrition facts per serving. owner_id NULL = shared catalog food; otherwise a user's custom food."""

    __tablename__ = "foods"
    __table_args__ = (
        UniqueConstraint("name", "owner_id", name="uq_food_name_owner"),
        CheckConstraint("calories >= 0 AND protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0", name="ck_food_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    serving_size: Mapped[str] = mapped_column(String(50), default="1 serving")
    calories: Mapped[float]
    protein_g: Mapped[float] = mapped_column(default=0)
    carbs_g: Mapped[float] = mapped_column(default=0)
    fat_g: Mapped[float] = mapped_column(default=0)
    fiber_g: Mapped[float] = mapped_column(default=0)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "serving_size": self.serving_size,
            "calories": self.calories,
            "protein_g": self.protein_g,
            "carbs_g": self.carbs_g,
            "fat_g": self.fat_g,
            "fiber_g": self.fiber_g,
            "custom": self.owner_id is not None,
        }


MEAL_TYPES = ("breakfast", "lunch", "dinner", "snack")


class Meal(db.Model):
    __tablename__ = "meals"
    __table_args__ = (Index("ix_meals_user_date", "user_id", "eaten_on"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    meal_type: Mapped[str] = mapped_column(String(20))
    eaten_on: Mapped[date]
    notes: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    user: Mapped[User] = relationship(back_populates="meals")
    items: Mapped[list["MealItem"]] = relationship(back_populates="meal", cascade="all, delete-orphan")

    def totals(self):
        keys = ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g")
        return {k: round(sum(getattr(i.food, k) * i.servings for i in self.items), 1) for k in keys}

    def to_dict(self):
        return {
            "id": self.id,
            "meal_type": self.meal_type,
            "eaten_on": self.eaten_on.isoformat(),
            "notes": self.notes,
            "items": [i.to_dict() for i in self.items],
            "totals": self.totals(),
        }


class MealItem(db.Model):
    __tablename__ = "meal_items"
    __table_args__ = (CheckConstraint("servings > 0", name="ck_meal_item_servings_pos"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    meal_id: Mapped[int] = mapped_column(ForeignKey("meals.id", ondelete="CASCADE"))
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.id"))
    servings: Mapped[float] = mapped_column(default=1)

    meal: Mapped[Meal] = relationship(back_populates="items")
    food: Mapped[Food] = relationship()

    def to_dict(self):
        return {
            "id": self.id,
            "food": self.food.to_dict(),
            "servings": self.servings,
            "calories": round(self.food.calories * self.servings, 1),
        }


class Workout(db.Model):
    __tablename__ = "workouts"
    __table_args__ = (Index("ix_workouts_user_date", "user_id", "performed_on"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    activity: Mapped[str] = mapped_column(String(100))
    duration_min: Mapped[int]
    calories_burned: Mapped[int] = mapped_column(default=0)
    performed_on: Mapped[date]

    def to_dict(self):
        return {
            "id": self.id,
            "activity": self.activity,
            "duration_min": self.duration_min,
            "calories_burned": self.calories_burned,
            "performed_on": self.performed_on.isoformat(),
        }
