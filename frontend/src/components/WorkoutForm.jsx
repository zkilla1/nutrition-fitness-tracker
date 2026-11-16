import { useState } from "react";
import { api } from "../api";

export default function WorkoutForm({ date, onLogged }) {
  const [activity, setActivity] = useState("");
  const [duration, setDuration] = useState(30);
  const [calories, setCalories] = useState(200);
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      await api("/workouts", {
        method: "POST",
        body: {
          activity,
          duration_min: Number(duration),
          calories_burned: Number(calories),
          performed_on: date,
        },
      });
      setActivity("");
      onLogged();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form onSubmit={submit} className="stack">
      <input placeholder="Activity (e.g. Running)" value={activity} onChange={(e) => setActivity(e.target.value)} required />
      <label>
        Duration (min)
        <input type="number" min="1" value={duration} onChange={(e) => setDuration(e.target.value)} />
      </label>
      <label>
        Calories burned
        <input type="number" min="0" value={calories} onChange={(e) => setCalories(e.target.value)} />
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit">Log workout</button>
    </form>
  );
}
