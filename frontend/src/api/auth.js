import { apiRequest, clearAuthToken, setAuthToken } from "./client";

export async function loginAdmin(username, password) {
  const data = await apiRequest("/api/auth/login", {
    method: "POST",
    body: { username, password }
  });
  setAuthToken(data.token);
  return data;
}

export async function fetchCurrentAdmin() {
  return apiRequest("/api/auth/me", { auth: true });
}

export function logoutAdmin() {
  clearAuthToken();
}

