import "./MultiCityGrid.css";

export default function MultiCityGrid({ items }) {
  if (!Array.isArray(items) || !items.length) return null;
  return (
    <div className="multi-grid">
      {items.map((w, idx) => (
        <div key={idx} className="mini-card">
          <div className="mini-city">{w.city}</div>
          <div className="mini-temp">{Math.round(w.temp)}°C</div>
          <div className="mini-row">
            <span>Feels</span>
            <strong>{w.feels != null ? Math.round(w.feels) : "-"}°C</strong>
          </div>
          <div className="mini-row">
            <span>Humidity</span>
            <strong>{w.humidity != null ? w.humidity : "-"}%</strong>
          </div>
          <div className="mini-row">
            <span>Wind</span>
            <strong>{w.wind_kmh != null ? w.wind_kmh : "-"} km/h</strong>
          </div>
          <div className="mini-cond">{w.condition || "-"}</div>
        </div>
      ))}
    </div>
  );
}
