import "./WeatherCard.css";

export default function ForecastSection({ data }) {
  if (!data) return null;

  const { city, summary } = data;

  return (
    <div className="card weather-card">
      <h2 className="title">Forecast for {city}</h2>
      <p className="summary-text">{summary}</p>
    </div>
  );
}
