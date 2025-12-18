import { useState } from "react";
import { useApp } from "../context/AppContext.jsx";

export default function InputBar() {
  const [text, setText] = useState("");
  const { sendMessage, isLoading } = useApp();
  const onSend = () => {
    if (!text.trim() || isLoading) return;
    sendMessage(text.trim());
    setText("");
  };
  return (
    <div className="input-bar">
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") onSend();
        }}
        placeholder="Ask about weather, forecast, comparison..."
      />
      <button onClick={onSend} disabled={!text.trim() || isLoading}>
        Send
      </button>
    </div>
  );
}
