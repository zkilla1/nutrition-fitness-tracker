import { useState } from "react";
import { api } from "../api";

export default function AuthForm({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    setError("");
    try {
      const { token } = await api(`/auth/${mode}`, { method: "POST", body: { email, password } });
      onAuth(token);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="card auth" onSubmit={submit}>
      <h2>{mode === "login" ? "Log in" : "Create account"}</h2>
      <label>
        Email
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </label>
      <label>
        Password
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required />
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit">{mode === "login" ? "Log in" : "Sign up"}</button>
      <button type="button" className="link" onClick={() => setMode(mode === "login" ? "register" : "login")}>
        {mode === "login" ? "Need an account? Sign up" : "Have an account? Log in"}
      </button>
    </form>
  );
}
