import { useMemo, useState } from "react";

import TopBar from "../components/TopBar.jsx";
import { sendMemoryChat } from "../api/memoryChat.js";

import "./home.css";
import "../components/ChatWindow.css";

function nowId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function MemoryChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState(null);
  const [isLoading, setLoading] = useState(false);

  const canSend = useMemo(() => input.trim().length > 0 && !isLoading, [input, isLoading]);

  const onSend = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;

    setError(null);
    setInput("");
    setMessages((m) => [...m, { id: nowId(), role: "user", text }]);

    setLoading(true);
    try {
      const res = await sendMemoryChat(text);
      const answer = res?.answer ?? "No answer.";
      const used_memories = Array.isArray(res?.used_memories) ? res.used_memories : [];
      const latency_ms = typeof res?.latency_ms === "number" ? res.latency_ms : null;

      setMessages((m) => [
        ...m,
        {
          id: nowId(),
          role: "assistant",
          text: answer,
          used_memories,
          latency_ms,
        },
      ]);
    } catch (err) {
      setError(err?.message || "Request failed");
      setMessages((m) => [...m, { id: nowId(), role: "assistant", text: "Sorry, something went wrong." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="layout">
      <TopBar />

      <div className="columns">
        <div className="panel chat">
          <div className="chat-window">
            {!messages.length ? (
              <div className="chat-window empty-chat">
                <p className="placeholder-text">Ask a question using your saved memories…</p>
              </div>
            ) : (
              messages.map((m) => (
                <div key={m.id} className="chat-block">
                  <div className={`bubble-row ${m.role === "user" ? "right" : "left"}`}>
                    <div className={`bubble ${m.role === "user" ? "user" : "assistant"}`} style={{ whiteSpace: "pre-wrap" }}>
                      {m.text}
                    </div>
                  </div>

                  {m.role === "assistant" && (m.used_memories?.length || m.latency_ms != null) ? (
                    <details style={{ marginTop: 8, opacity: 0.9 }}>
                      <summary style={{ cursor: "pointer" }}>debug</summary>
                      {m.latency_ms != null && (
                        <div style={{ fontSize: 13, marginTop: 6 }}>latency_ms: {m.latency_ms.toFixed(2)}</div>
                      )}
                      {m.used_memories?.length ? (
                        <ul style={{ marginTop: 6 }}>
                          {m.used_memories.map((t, idx) => (
                            <li key={idx} style={{ fontSize: 13 }}>
                              {t}
                            </li>
                          ))}
                        </ul>
                      ) : null}
                    </details>
                  ) : null}
                </div>
              ))
            )}
          </div>

          <form className="input-bar" onSubmit={onSend}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message…"
            />
            <button type="submit" disabled={!canSend}>
              {isLoading ? "..." : "Send"}
            </button>
          </form>

          {error && <div style={{ color: "#ffb4b4", padding: "10px 12px" }}>{error}</div>}
        </div>

        <div className="panel dashboard">
          <div style={{ color: "#fff", opacity: 0.9 }}>
            <h3 style={{ marginTop: 0 }}>Memory Chat</h3>
            <p style={{ marginBottom: 0 }}>
              This is isolated from weather chat and uses your JWT to fetch relevant memories.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
