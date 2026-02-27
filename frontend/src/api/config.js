import { apiRequest } from "./client";

export async function fetchSystemConfig() {
  return apiRequest("/api/config", { auth: true });
}

export async function updateSystemConfig(payload) {
  return apiRequest("/api/config", {
    method: "PUT",
    body: payload,
    auth: true
  });
}

