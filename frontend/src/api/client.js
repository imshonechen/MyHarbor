const TOKEN_KEY = "myharbor_admin_token";

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setAuthToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAuthToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export async function apiRequest(path, options = {}) {
  const { method = "GET", body, auth = false } = options;
  const headers = { "Content-Type": "application/json" };

  if (auth) {
    const token = getAuthToken();
    if (!token) {
      throw new Error("Unauthorized");
    }
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const message = payload?.detail || payload?.message || `Request failed: ${response.status}`;
    throw new Error(message);
  }

  if (!payload || payload.code !== 0) {
    throw new Error(payload?.message || "Request failed");
  }

  return payload.data;
}

