import { useEffect, useRef } from "react";
import ChatBubble from "./ChatBubble";
import WeatherCard from "./WeatherCard";
import ComparisonSection from "./ComparisonSection";
import ForecastSection from "./ForecastSection";
import MultiCityGrid from "./MultiCityGrid";
import "./ChatWindow.css";

export default function ChatWindow({ messages }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    // Scroll to the latest message smoothly whenever messages change
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!messages?.length) {
    return (
      <div className="chat-window empty-chat">
        <p className="placeholder-text">
          Ask about weather, cities, forecast, or comparison...
        </p>
      </div>
    );
  }

  return (
    <div className="chat-window">
      {messages.map((msg, i) => {
        const isBot = msg.role === "assistant";
        const data = msg?.data || {};

        return (
          <div key={i} className="chat-block">
            <ChatBubble sender={msg.role} text={msg.text} />

            {isBot && data.temp && !data.city1_weather && (
              <WeatherCard data={data} />
            )}

            {isBot && data.city1_weather && data.city2_weather && (
              <ComparisonSection data={data} />
            )}

            {isBot && data.forecast && <ForecastSection data={data.forecast} />}

            {isBot && data.type === "multi" && Array.isArray(data.cities) && (
              <MultiCityGrid items={data.cities} />
            )}
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
