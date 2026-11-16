def food_id(client, headers, name):
    foods = client.get(f"/api/foods?q={name}", headers=headers).json["foods"]
    assert foods, f"no food matching {name}"
    return foods[0]["id"]


def test_register_login_me(client, auth):
    auth("a@example.com")
    resp = client.post("/api/auth/login", json={"email": "A@example.com", "password": "password123"})
    assert resp.status_code == 200
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {resp.json['token']}"})
    assert me.json["email"] == "a@example.com"
    assert me.json["profile"]["calorie_goal"] == 2000


def test_bad_login_and_missing_token(client, auth):
    auth()
    assert client.post("/api/auth/login", json={"email": "zach@example.com", "password": "nope"}).status_code == 401
    assert client.get("/api/meals").status_code == 401
    assert client.get("/api/meals", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_duplicate_and_weak_registration(client, auth):
    auth()
    assert client.post("/api/auth/register", json={"email": "zach@example.com", "password": "password123"}).status_code == 400
    assert client.post("/api/auth/register", json={"email": "x@example.com", "password": "short"}).status_code == 400


def test_log_meal_and_daily_summary(client, auth):
    h = auth()
    egg = food_id(client, h, "Egg")
    oats = food_id(client, h, "Oatmeal")
    resp = client.post(
        "/api/meals",
        headers=h,
        json={"meal_type": "breakfast", "eaten_on": "2026-01-05", "items": [{"food_id": egg, "servings": 2}, {"food_id": oats}]},
    )
    assert resp.status_code == 201, resp.json
    assert resp.json["totals"]["calories"] == 72 * 2 + 166

    client.post("/api/workouts", headers=h, json={"activity": "Run", "duration_min": 30, "calories_burned": 300, "performed_on": "2026-01-05"})

    summary = client.get("/api/summary/daily?date=2026-01-05", headers=h).json
    assert summary["consumed"]["calories"] == 310
    assert summary["calories_burned"] == 300
    assert summary["net_calories"] == 10
    assert summary["remaining_calories"] == 2000 - 310 + 300
    assert summary["by_meal_type"]["breakfast"] == 310


def test_meal_validation(client, auth):
    h = auth()
    assert client.post("/api/meals", headers=h, json={"meal_type": "brunch", "items": [{"food_id": 1}]}).status_code == 400
    assert client.post("/api/meals", headers=h, json={"meal_type": "lunch", "items": []}).status_code == 400
    assert client.post("/api/meals", headers=h, json={"meal_type": "lunch", "items": [{"food_id": 1, "servings": 0}]}).status_code == 400
    assert client.post("/api/meals", headers=h, json={"meal_type": "lunch", "eaten_on": "nope", "items": [{"food_id": 1}]}).status_code == 400


def test_custom_foods_are_private(client, auth):
    alice = auth("alice@example.com")
    bob = auth("bob@example.com")
    resp = client.post("/api/foods", headers=alice, json={"name": "Grandma's lasagna", "calories": 450, "protein_g": 22})
    assert resp.status_code == 201
    custom_id = resp.json["id"]

    assert client.get("/api/foods?q=lasagna", headers=alice).json["foods"]
    assert not client.get("/api/foods?q=lasagna", headers=bob).json["foods"]
    resp = client.post("/api/meals", headers=bob, json={"meal_type": "dinner", "items": [{"food_id": custom_id}]})
    assert resp.status_code == 400


def test_meals_are_isolated_between_users(client, auth):
    alice = auth("alice@example.com")
    bob = auth("bob@example.com")
    meal = client.post("/api/meals", headers=alice, json={"meal_type": "snack", "items": [{"food_id": 1}]}).json
    assert client.get(f"/api/meals/{meal['id']}", headers=bob).status_code == 404
    assert client.delete(f"/api/meals/{meal['id']}", headers=bob).status_code == 404
    assert client.delete(f"/api/meals/{meal['id']}", headers=alice).status_code == 204


def test_profile_update(client, auth):
    h = auth()
    resp = client.patch("/api/profile", headers=h, json={"calorie_goal": 2500, "weight_kg": 80.5})
    assert resp.json["calorie_goal"] == 2500 and resp.json["weight_kg"] == 80.5
    assert client.patch("/api/profile", headers=h, json={"calorie_goal": "lots"}).status_code == 400
