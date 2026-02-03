import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import TopBar from "../components/TopBar.jsx";
import { login, signup } from "../api/authApi.js";
import { setToken } from "../api/auth.js";
import "./auth.css";

export default function Signup() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [isLoading, setLoading] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const cleanEmail = email.trim();
    try {
      await signup(cleanEmail, password);
      const res = await login(cleanEmail, password);
      const token = res?.access_token;
      if (!token) throw new Error("Missing access_token");
      setToken(token, cleanEmail);
      navigate("/memory-chat", { replace: true });
    } catch (err) {
      setError(err?.message || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <TopBar />
      <div className="auth-card">
        <h2>Signup</h2>
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
              autoComplete="new-password"
            />
          </label>

          <div className="auth-actions">
            <button className="auth-button" type="submit" disabled={isLoading}>
              {isLoading ? "Creating..." : "Signup"}
            </button>
            <Link className="auth-link" to="/login">
              Already have an account?
            </Link>
          </div>
        </form>

        {error && <p className="auth-error">{error}</p>}
      </div>
    </div>
  );
}
