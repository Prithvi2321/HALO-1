/**
 * src/api/workspaceApi.js
 * ───────────────────────
 * API client for Practice Dashboard, Matters, Calendar & Statutory Deadlines (PRD §7 & §11.2).
 */

import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const data = err?.response?.data;
    const msg = data?.detail?.message || (typeof data?.detail === "string" ? data.detail : "") || data?.message || err.message;
    return Promise.reject(new Error(msg || "Workspace API request failed."));
  }
);

// ─── Clients ─────────────────────────────────────────────────────────────────

export async function listClients() {
  const { data } = await api.get("/clients");
  return data;
}

export async function createClient(clientData) {
  const { data } = await api.post("/clients", clientData);
  return data;
}

// ─── Matters ─────────────────────────────────────────────────────────────────

export async function listMatters(status, forumType, search) {
  const params = {};
  if (status && status !== "ALL") params.status = status;
  if (forumType && forumType !== "ALL") params.forum_type = forumType;
  if (search) params.search = search;
  const { data } = await api.get("/matters", { params });
  return data;
}

export async function createMatter(matterData) {
  const { data } = await api.post("/matters", matterData);
  return data;
}

export async function getMatter(matterId) {
  const { data } = await api.get(`/matters/${matterId}`);
  return data;
}

export async function getMatterTimeline(matterId) {
  const { data } = await api.get(`/matters/${matterId}/timeline`);
  return data;
}

export async function addMatterNote(matterId, content, authorName) {
  const { data } = await api.post(`/matters/${matterId}/notes`, {
    content,
    author_name: authorName,
  });
  return data;
}

// ─── Calendar & Statutory Deadlines ──────────────────────────────────────────

export async function listDeadlineRules() {
  const { data } = await api.get("/deadlines/rules");
  return data;
}

export async function computeDeadline(ruleId, anchorDate, matterId) {
  const { data } = await api.post("/deadlines/compute", {
    rule_id: ruleId,
    anchor_date: anchorDate,
    matter_id: matterId,
  });
  return data;
}

export async function listEvents(fromDate, toDate, matterId, eventType) {
  const params = {};
  if (fromDate) params.from_date = fromDate;
  if (toDate) params.to_date = toDate;
  if (matterId) params.matter_id = matterId;
  if (eventType) params.event_type = eventType;
  const { data } = await api.get("/events", { params });
  return data;
}

export async function createEvent(eventData) {
  const { data } = await api.post("/events", eventData);
  return data;
}

export async function confirmEvent(eventId) {
  const { data } = await api.post(`/events/${eventId}/confirm`);
  return data;
}

export async function getDashboardSummary() {
  const { data } = await api.get("/dashboard/summary");
  return data;
}
