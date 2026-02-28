import { apiRequest } from "./client";

export async function fetchStatsOverview() {
  return apiRequest("/api/stats/overview", { auth: true });
}

export async function fetchSiteRanking(params = {}) {
  const query = new URLSearchParams();
  if (params.range) query.set("range", params.range);
  if (params.limit) query.set("limit", String(params.limit));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest(`/api/stats/sites${suffix}`, { auth: true });
}

export async function fetchStatsTrend(params = {}) {
  const query = new URLSearchParams();
  if (params.days) query.set("days", String(params.days));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest(`/api/stats/trend${suffix}`, { auth: true });
}

export async function fetchStatsTable() {
  return apiRequest("/api/stats/table", { auth: true });
}
