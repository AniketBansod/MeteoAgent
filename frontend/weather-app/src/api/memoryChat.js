import { getToken } from "./auth.js";

// Use relative URLs in dev (Vite proxy), or explicit backend URL in production
const backend = import.meta.env.VITE_BACKEND_URL || "";

function joinUrl(base, path) {
    if (!base) return path;
    const b = base.endsWith("/") ? base.slice(0, -1) : base;
    const p = path.startsWith("/") ? path : `/${path}`;
    return `${b}${p}`;
}

export async function sendMemoryChat(message) {
    const token = getToken();
    if (!token) throw new Error("Not authenticated");

    const res = await fetch(joinUrl(backend, "/memory/chat"), {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message }),
    });

    if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status}: ${text}`);
    }

    return res.json();
}
