import { apiRequest } from "./client";

export async function fetchPublicConfig() {
  return apiRequest("/api/config/public");
}

export async function fetchPublicSites(params = {}) {
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.tag) query.set("tag", params.tag);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiRequest(`/api/sites/public${suffix}`);
}

export async function recordHomeVisit() {
  return apiRequest("/api/visit", { method: "POST" });
}

export async function recordSiteVisit(siteId) {
  return apiRequest(`/api/visit/${siteId}`, { method: "POST" });
}
