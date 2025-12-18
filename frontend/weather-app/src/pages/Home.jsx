import ChatWindow from "../components/ChatWindow.jsx";
import WeatherCard from "../components/WeatherCard.jsx";
import ForecastSection from "../components/ForecastSection.jsx";
import ComparisonSection from "../components/ComparisonSection.jsx";
import TopBar from "../components/TopBar.jsx";
import InputBar from "../components/InputBar.jsx";
import MultiCityGrid from "../components/MultiCityGrid.jsx";
import "./home.css";
import { useApp } from "../context/AppContext.jsx";

export default function Home() {
  const {
    messages,
    activeWeather,
    activeForecast,
    activeComparison,
    activeMulti,
  } = useApp();

  return (
    <div className="layout">
      <TopBar />

      <div className="columns">
        {/* Left Block */}
        <div className="panel chat">
          <ChatWindow messages={messages} />

          {/* Input bar must sit in chat panel */}
          <InputBar />
        </div>

        {/* Right Block */}
        <div className="panel dashboard">
          {activeMulti && activeMulti.length > 0 && (
            <MultiCityGrid items={activeMulti} />
          )}
          {activeWeather && <WeatherCard data={activeWeather} />}
          {activeForecast && <ForecastSection data={activeForecast} />}
          {activeComparison && <ComparisonSection data={activeComparison} />}
        </div>
      </div>
    </div>
  );
}
