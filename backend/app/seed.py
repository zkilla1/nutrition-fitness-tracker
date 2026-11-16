"""Seed the shared food catalog. Values are approximate per-serving nutrition facts (USDA FoodData Central)."""

from sqlalchemy import select

from .extensions import db
from .models import Food

CATALOG = [
    # name, serving, kcal, protein, carbs, fat, fiber
    ("Chicken breast, grilled", "100 g", 165, 31, 0, 3.6, 0),
    ("Salmon, baked", "100 g", 206, 22, 0, 12, 0),
    ("Egg, large", "1 egg", 72, 6.3, 0.4, 4.8, 0),
    ("Greek yogurt, plain nonfat", "170 g", 100, 17, 6, 0.7, 0),
    ("Oatmeal, cooked", "1 cup", 166, 5.9, 28, 3.6, 4),
    ("Brown rice, cooked", "1 cup", 218, 4.5, 46, 1.6, 3.5),
    ("White rice, cooked", "1 cup", 205, 4.3, 45, 0.4, 0.6),
    ("Banana", "1 medium", 105, 1.3, 27, 0.4, 3.1),
    ("Apple", "1 medium", 95, 0.5, 25, 0.3, 4.4),
    ("Broccoli, steamed", "1 cup", 55, 3.7, 11, 0.6, 5.1),
    ("Avocado", "1/2 fruit", 120, 1.5, 6.4, 11, 5),
    ("Almonds", "28 g", 164, 6, 6.1, 14, 3.5),
    ("Peanut butter", "2 tbsp", 188, 8, 6, 16, 2),
    ("Whole wheat bread", "1 slice", 81, 4, 14, 1.1, 1.9),
    ("Whey protein shake", "1 scoop", 120, 24, 3, 1.5, 0),
    ("Sweet potato, baked", "1 medium", 103, 2.3, 24, 0.2, 3.8),
    ("Black beans, cooked", "1/2 cup", 114, 7.6, 20, 0.5, 7.5),
    ("Whole milk", "1 cup", 149, 7.7, 12, 8, 0),
    ("Cheddar cheese", "28 g", 113, 7, 0.4, 9.3, 0),
    ("Pasta, cooked", "1 cup", 221, 8.1, 43, 1.3, 2.5),
    ("Ground beef 90% lean, cooked", "100 g", 217, 26, 0, 12, 0),
    ("Tofu, firm", "100 g", 144, 17, 3, 8.7, 2.3),
    ("Spinach, raw", "1 cup", 7, 0.9, 1.1, 0.1, 0.7),
    ("Olive oil", "1 tbsp", 119, 0, 0, 13.5, 0),
]


def seed_foods():
    existing = set(db.session.scalars(select(Food.name).where(Food.owner_id.is_(None))))
    added = 0
    for name, serving, kcal, p, c, f, fiber in CATALOG:
        if name in existing:
            continue
        db.session.add(
            Food(name=name, serving_size=serving, calories=kcal, protein_g=p, carbs_g=c, fat_g=f, fiber_g=fiber)
        )
        added += 1
    db.session.commit()
    return added


if __name__ == "__main__":
    from . import create_app

    with create_app().app_context():
        print(f"Added {seed_foods()} foods.")
