// ComparisonSection.jsx

import "./ComparisonSection.css";

export default function ComparisonSection({ data }) {
  if (!data) return null;

  const comparison = data;

  // Not comparison? Don't render anything
  if (!comparison.city1_weather || !comparison.city2_weather) {
    return null;
  }

  const cityA = comparison.city1_weather;
  const cityB = comparison.city2_weather;

  return (
    <div className="comparison-card">
      <h2 className="comparison-title">{comparison.winner}</h2>

      <div className="comparison-grid">
        <div className="comparison-city">
          <h3>{cityA.city}</h3>
          <p>
            <strong>Temp:</strong> {cityA.temp}°C
          </p>
          <p>
            <strong>Humidity:</strong> {cityA.humidity}%
          </p>
          <p>
            <strong>Wind:</strong> {cityA.wind_kmh} km/h
          </p>
          <p>
            <strong>Feels:</strong> {cityA.feels ?? cityA.feels_like ?? "-"}°C
          </p>
        </div>

        <div className="comparison-city">
          <h3>{cityB.city}</h3>
          <p>
            <strong>Temp:</strong> {cityB.temp}°C
          </p>
          <p>
            <strong>Humidity:</strong> {cityB.humidity}%
          </p>
          <p>
            <strong>Wind:</strong> {cityB.wind_kmh} km/h
          </p>
          <p>
            <strong>Feels:</strong> {cityB.feels ?? cityB.feels_like ?? "-"}°C
          </p>
        </div>
      </div>
    </div>
  );
}
