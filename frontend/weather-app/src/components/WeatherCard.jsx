// WeatherCard.jsx

import "./WeatherCard.css";

export default function WeatherCard({ data }) {
  if (!data) return null;

  // skip if this is comparison
  if (data.city1_weather || data.city2_weather) return null;

  const {
    city,
    temp,
    feels,     // <- correct key from context
    humidity,
    wind_kmh,
    condition,
  } = data;

  return (
    <div className="weather-card">
      <h2 className="weather-city">{city}</h2>

      <div className="weather-temp">
        {Math.round(temp)}°C
      </div>

      <div className="weather-details">
        <p><strong>Feels like:</strong> {feels ? Math.round(feels) : "-"}°C</p>
        <p><strong>Humidity:</strong> {humidity ?? "-"}%</p>
        <p><strong>Wind:</strong> {wind_kmh ?? "-"} km/h</p>
        <p><strong>Condition:</strong> {condition ?? "-"} </p>
      </div>
    </div>
  );
}
