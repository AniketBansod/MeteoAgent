const TOKEN_KEY = "access_token";
const EMAIL_KEY = "user_email";

export function getToken() {
    try {
        return localStorage.getItem(TOKEN_KEY);
    } catch {
        return null;
    }
}

export function setToken(token, email) {
    if (!token) return;
    try {
        localStorage.setItem(TOKEN_KEY, token);
        if (email) localStorage.setItem(EMAIL_KEY, email);
    } catch {
        // ignore
    }
}

export function clearToken() {
    try {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(EMAIL_KEY);
    } catch {
        // ignore
    }
}

export function isAuthenticated() {
    return Boolean(getToken());
}

export function getEmail() {
    try {
        return localStorage.getItem(EMAIL_KEY);
    } catch {
        return null;
    }
}
