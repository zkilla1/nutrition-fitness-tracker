import { useEffect, useState } from "react";
import { api } from "../api";

export default function MealForm({ date, onLogged }) {
  const [mealType, setMealType] = useState("breakfast");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    const handle = setTimeout(async () => {
      const { foods } = await api(`/foods?q=${encodeURIComponent(query)}&limit=8`);
      setResults(foods);
    }, 200);
    return () => clearTimeout(handle);
  }, [query]);

  function addItem(food) {
    setItems((prev) => [...prev, { food, servings: 1 }]);
    setQuery("");
    setResults([]);
  }

  function updateServings(index, servings) {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, servings } : it)));
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      await api("/meals", {
        method: "POST",
        body: {
          meal_type: mealType,
          eaten_on: date,
          items: items.map((it) => ({ food_id: it.food.id, servings: Number(it.servings) })),
        },
      });
      setItems([]);
      onLogged();
    } catch (err) {
      setError(err.message);
    }
  }

  const total = items.reduce((sum, it) => sum + it.food.calories * Number(it.servings || 0), 0);

  return (
    <form onSubmit={submit} className="stack">
      <select value={mealType} onChange={(e) => setMealType(e.target.value)}>
        {["breakfast", "lunch", "dinner", "snack"].map((t) => (
          <option key={t} value={t}>
            {t[0].toUpperCase() + t.slice(1)}
          </option>
        ))}
      </select>
      <div className="search">
        <input placeholder="Search foods…" value={query} onChange={(e) => setQuery(e.target.value)} />
        {results.length > 0 && (
          <ul className="dropdown">
            {results.map((food) => (
              <li key={food.id} onClick={() => addItem(food)}>
                {food.name} <span className="muted">· {food.serving_size} · {food.calories} kcal</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      {items.map((it, i) => (
        <div key={i} className="item-row">
          <span>{it.food.name}</span>
          <input
            type="number"
            min="0.25"
            step="0.25"
            value={it.servings}
            onChange={(e) => updateServings(i, e.target.value)}
          />
          <button type="button" className="link danger" onClick={() => setItems(items.filter((_, j) => j !== i))}>
            ×
          </button>
        </div>
      ))}
      {items.length > 0 && <p className="muted">Total: {Math.round(total)} kcal</p>}
      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={items.length === 0}>
        Log meal
      </button>
    </form>
  );
}
