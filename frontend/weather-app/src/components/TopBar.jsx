import "./TopBar.css";

export default function TopBar() {
  return (
    <header className="topbar">
      <div className="brand">🌦 MeteoAgent</div>

      <nav className="menu">
        <span className="pill" title="Ask about current conditions">
          ⚡ <span className="label">AI Weather</span>
        </span>
        <span className="pill" title="Get weekend or tomorrow summary">
          📅 <span className="label">Forecast</span>
        </span>
        <span className="pill" title="Compare multiple cities">
          🆚 <span className="label">Compare</span>
        </span>
      </nav>
    </header>
  );
}
