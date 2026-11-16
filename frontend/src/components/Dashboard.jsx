import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import MealForm from "./MealForm";
import WorkoutForm from "./WorkoutForm";

const today = () => new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD in local time

function MacroBar({ label, value, goal, unit = "g" }) {
  const pct = goal ? Math.min(100, (value / goal) * 100) : 0;
  return (
    <div className="macro">
      <div className="macro-head">
        <span>{label}</span>
        <span>
          {Math.round(value)} / {goal} {unit}
        </span>
      </div>
      <div className="bar">
        <div className="fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [date, setDate] = useState(today());
  const [summary, setSummary] = useState(null);
  const [meals, setMeals] = useState([]);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [s, m] = await Promise.all([api(`/summary/daily?date=${date}`), api(`/meals?date=${date}`)]);
      setSummary(s);
      setMeals(m.meals);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }, [date]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function deleteMeal(id) {
    await api(`/meals/${id}`, { method: "DELETE" });
    refresh();
  }

  async function deleteWorkout(id) {
    await api(`/workouts/${id}`, { method: "DELETE" });
    refresh();
  }

  return (
    <div className="dashboard">
      <div className="date-row">
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>
      {error && <p className="error">{error}</p>}

      {summary && (
        <section className="card">
          <div className="calories">
            <div>
              <strong>{Math.round(summary.consumed.calories)}</strong>
              <span>eaten</span>
            </div>
            <div>
              <strong>{summary.calories_burned}</strong>
              <span>burned</span>
            </div>
            <div>
              <strong>{Math.round(summary.remaining_calories)}</strong>
              <span>remaining</span>
            </div>
          </div>
          <MacroBar label="Calories" value={summary.consumed.calories} goal={summary.goals.calories} unit="kcal" />
          <MacroBar label="Protein" value={summary.consumed.protein_g} goal={summary.goals.protein_g} />
          <MacroBar label="Carbs" value={summary.consumed.carbs_g} goal={summary.goals.carbs_g} />
          <MacroBar label="Fat" value={summary.consumed.fat_g} goal={summary.goals.fat_g} />
        </section>
      )}

      <div className="grid">
        <section className="card">
          <h2>Log a meal</h2>
          <MealForm date={date} onLogged={refresh} />
        </section>
        <section className="card">
          <h2>Log a workout</h2>
          <WorkoutForm date={date} onLogged={refresh} />
        </section>
      </div>

      <section className="card">
        <h2>Meals</h2>
        {meals.length === 0 && <p className="muted">Nothing logged for this day.</p>}
        {meals.map((meal) => (
          <div key={meal.id} className="meal">
            <div className="meal-head">
              <strong className="capitalize">{meal.meal_type}</strong>
              <span>{Math.round(meal.totals.calories)} kcal</span>
              <button className="link danger" onClick={() => deleteMeal(meal.id)}>
                Delete
              </button>
            </div>
            <ul>
              {meal.items.map((item) => (
                <li key={item.id}>
                  {item.servings} × {item.food.name} <span className="muted">({item.food.serving_size})</span> —{" "}
                  {Math.round(item.calories)} kcal
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      {summary?.workouts.length > 0 && (
        <section className="card">
          <h2>Workouts</h2>
          <ul>
            {summary.workouts.map((w) => (
              <li key={w.id}>
                {w.activity}: {w.duration_min} min, {w.calories_burned} kcal{" "}
                <button className="link danger" onClick={() => deleteWorkout(w.id)}>
                  Delete
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
