import { createContext, useContext, useMemo, useState } from "react";
import { sendChat, fetchWeatherBatch } from "../api/chat.js";

const AppCtx = createContext(null);
export const useApp = () => useContext(AppCtx);

export function AppProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeWeather, setActiveWeather] = useState(null);
  const [activeForecast, setActiveForecast] = useState(null);
  const [activeComparison, setActiveComparison] = useState(null);
  const [activeMulti, setActiveMulti] = useState(null); // array of weather objects

  const append = (role, text, data) =>
    setMessages((m) => [...m, { role, text, data, ts: Date.now() }]);

  const parseForWidgets = (answer) => {
    if (!answer) return;
    // crude extraction heuristics for demo; backend sends structured in text
    const cityMatch = answer.match(/^(\w[\w\s]+)/);
    const tempMatch = answer.match(/(\d+\.?\d*)°C/);
    const feelsMatch = answer.match(/feels\s(\d+\.?\d*)°C/i);
    const humMatch = answer.match(/humidity\s(\d+)%/i);
    const windMatch = answer.match(/wind\s(\d+\.?\d*)\s?km\/h/i);
    const condMatch = answer.match(/,\s([a-zA-Z ]+)$/);
    if (tempMatch) {
      setActiveWeather({
        city: cityMatch ? cityMatch[1].trim() : undefined,
        temp: Number(tempMatch[1]),
        feels: feelsMatch ? Number(feelsMatch[1]) : Number(tempMatch[1]),
        humidity: humMatch ? Number(humMatch[1]) : undefined,
        wind_kmh: windMatch ? Number(windMatch[1]) : undefined,
        condition: condMatch ? condMatch[1].trim() : undefined,
      });
    }
  };

  const sendMessage = async (text) => {
    setError(null);
    append("user", text);

    // Frontend small-talk fallback for greetings
    const smallTalk =
      /^(hi+|hey+|hello+|good\s*(morning|afternoon|evening)|what's up|how are you)\b/i;
    if (smallTalk.test(text)) {
      const reply =
        "Hello! I'm MeteoAgent. Ask me about current weather, multi-city comparisons, or forecasts (weekend, tomorrow, or a specific hour).";
      append("assistant", reply);
      return;
    }
    setLoading(true);
    try {
      const res = await sendChat(text);
      const answer = res?.answer ?? "No answer.";
      append("assistant", answer);
      // attach widgets from known shapes
      parseForWidgets(answer);
      // if response includes a comparison JSON line or forecast summary, stash for dashboard
      if (res?.winner && (res?.city1_weather || res?.city2_weather)) {
        setActiveComparison({
          winner: res.winner,
          city1_weather: res.city1_weather,
          city2_weather: res.city2_weather,
          scores: res.scores,
        });
      }
      if (res?.summary && res?.city) {
        setActiveForecast({ city: res.city, summary: res.summary });
      }

      // Multi-city support: if backend detected multiple city names (>2), fetch batch details
      if (Array.isArray(res?.cities) && res.cities.filter(Boolean).length > 2) {
        try {
          const unique = Array.from(
            new Set(res.cities.map((c) => (c || "").trim()).filter(Boolean))
          );
          const batch = await fetchWeatherBatch(unique);
          if (Array.isArray(batch) && batch.length) {
            setActiveMulti(batch);
            append(
              "assistant",
              "Here are the current conditions for all cities:",
              { type: "multi", cities: batch }
            );
          }
        } catch (e) {
          console.warn("Batch fetch failed", e);
        }
      } else {
        setActiveMulti(null);
      }
    } catch (e) {
      console.error(e);
      setError("Request failed. Please try again.");
      append("assistant", "Sorry, something went wrong fetching the weather.");
    } finally {
      setLoading(false);
    }
  };

  const value = useMemo(
    () => ({
      messages,
      isLoading,
      error,
      activeWeather,
      activeForecast,
      activeComparison,
      activeMulti,
      sendMessage,
    }),
    [
      messages,
      isLoading,
      error,
      activeWeather,
      activeForecast,
      activeComparison,
      activeMulti,
    ]
  );

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}
