import "./TopBar.css";
import { Link, useNavigate } from "react-router-dom";
import { clearToken, getEmail, isAuthenticated } from "../api/auth.js";

export default function TopBar() {
  const navigate = useNavigate();
  const authed = isAuthenticated();
  const email = getEmail();

  const onLogout = () => {
    clearToken();
    navigate("/login", { replace: true });
  };

  return (
    <header className="topbar">
      <Link className="brand brand-link" to="/">
        🌦 MeteoAgent
      </Link>

      <div className="menu">
        <span className="pill" title="Ask about current conditions">
          ⚡ <span className="label">AI Weather</span>
        </span>
        <span className="pill" title="Get weekend or tomorrow summary">
          📅 <span className="label">Forecast</span>
        </span>
        <span className="pill" title="Compare multiple cities">
          🆚 <span className="label">Compare</span>
        </span>

        <span className="spacer" />

        {authed ? (
          <>
            <Link className="pill pill-link" to="/memory-chat" title="Chat with your saved memories">
              🧠 <span className="label">Memory Chat</span>
            </Link>
            <button className="pill pill-button" onClick={onLogout} title={email ? `Logout (${email})` : "Logout"}>
              ⎋ <span className="label">Logout</span>
            </button>
          </>
        ) : (
          <>
            <Link className="pill pill-link" to="/login">
              🔐 <span className="label">Login</span>
            </Link>
            <Link className="pill pill-link" to="/signup">
              ➕ <span className="label">Signup</span>
            </Link>
          </>
        )}
      </div>
    </header>
  );
}
