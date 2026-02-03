// Use relative URLs in dev (Vite proxy), or explicit backend URL in production
const backend = import.meta.env.VITE_BACKEND_URL || "";

function joinUrl(base, path) {
    if (!base) return path;
    const b = base.endsWith("/") ? base.slice(0, -1) : base;
    const p = path.startsWith("/") ? path : `/${path}`;
    return `${b}${p}`;
}

async function postJson(path, body) {
    const res = await fetch(joinUrl(backend, path), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status}: ${text}`);
    }

    return res.json();
}

export async function signup(email, password) {
    return postJson("/auth/signup", { email, password });
}

export async function login(email, password) {
    return postJson("/auth/login", { email, password });
}
