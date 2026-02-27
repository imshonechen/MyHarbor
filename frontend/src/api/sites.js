import { apiRequest } from "./client";

export async function fetchAllSites(params = {}) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    query.set(key, String(value));
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest(`/api/sites${suffix}`, { auth: true });
}

export async function createSite(payload) {
  return apiRequest("/api/sites", {
    method: "POST",
    body: payload,
    auth: true
  });
}

export async function updateSite(siteId, payload) {
  return apiRequest(`/api/sites/${siteId}`, {
    method: "PUT",
    body: payload,
    auth: true
  });
}

export async function deleteSite(siteId) {
  return apiRequest(`/api/sites/${siteId}`, {
    method: "DELETE",
    auth: true
  });
}

export async function toggleSitePublic(siteId) {
  return apiRequest(`/api/sites/${siteId}/toggle`, {
    method: "PATCH",
    auth: true
  });
}

export async function updateSiteSort(items) {
  return apiRequest("/api/sites/sort", {
    method: "PUT",
    body: { items },
    auth: true
  });
}

export async function checkSite(siteId) {
  return apiRequest(`/api/sites/${siteId}/check`, {
    method: "POST",
    auth: true
  });
}

export async function checkAllSites() {
  return apiRequest("/api/sites/check-all", {
    method: "POST",
    auth: true
  });
}

export async function fetchSiteStatusLogs(siteId, params = {}) {
  const query = new URLSearchParams();
  if (params.days) {
    query.set("days", String(params.days));
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest(`/api/sites/${siteId}/status-logs${suffix}`, { auth: true });
}
