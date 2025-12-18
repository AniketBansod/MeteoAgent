import { useMemo } from "react";
import { marked } from "marked";
import DOMPurify from "dompurify";

marked.setOptions({ breaks: true, gfm: true });

export default function Markdown({ text }) {
  const html = useMemo(() => {
    const raw = marked.parse(text || "");
    return DOMPurify.sanitize(raw);
  }, [text]);
  return (
    <div className="markdown" dangerouslySetInnerHTML={{ __html: html }} />
  );
}
