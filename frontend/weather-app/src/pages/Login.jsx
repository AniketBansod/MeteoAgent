import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import TopBar from "../components/TopBar.jsx";
import { login } from "../api/authApi.js";
import { setToken } from "../api/auth.js";
import "./auth.css";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [isLoading, setLoading] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await login(email.trim(), password);
      const token = res?.access_token;
      if (!token) throw new Error("Missing access_token");
      setToken(token, email.trim());
      navigate("/memory-chat", { replace: true });
    } catch (err) {
      setError(err?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <TopBar />
      <div className="auth-card">
        <h2>Login</h2>
        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </label>

          <div className="auth-actions">
            <button className="auth-button" type="submit" disabled={isLoading}>
              {isLoading ? "Signing in..." : "Login"}
            </button>
            <Link className="auth-link" to="/signup">
              Need an account?
            </Link>
          </div>
        </form>

        {error && <p className="auth-error">{error}</p>}
      </div>
    </div>
  );
}
