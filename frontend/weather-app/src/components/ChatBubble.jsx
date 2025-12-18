import Markdown from "./Markdown.jsx";

export default function ChatBubble({ sender, text }) {
  const isUser = sender === "user";

  return (
    <div className={`bubble-row ${isUser ? "right" : "left"}`}>
      <div className={`bubble ${isUser ? "user" : "assistant"}`}>
        {isUser ? text : <Markdown text={text} />}
      </div>
    </div>
  );
}
