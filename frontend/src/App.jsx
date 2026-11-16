import { useState } from "react";
import { getToken, setToken } from "./api";
import AuthForm from "./components/AuthForm";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [token, setTokenState] = useState(getToken());

  function handleAuth(newToken) {
    setToken(newToken);
    setTokenState(newToken);
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>Nutrition &amp; Fitness Tracker</h1>
        {token && (
          <button className="link" onClick={() => handleAuth(null)}>
            Log out
          </button>
        )}
      </header>
      <main>{token ? <Dashboard /> : <AuthForm onAuth={handleAuth} />}</main>
    </div>
  );
}
