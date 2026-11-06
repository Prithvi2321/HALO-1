/**
 * src/api/draftingApi.js
 * ──────────────────────
 * API client for the Document Drafting Engine (PRD §6 & §11.1).
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
    return Promise.reject(new Error(msg || "Drafting API request failed."));
  }
);

export async function listTemplates(category) {
  const params = category && category !== "ALL" ? { category } : {};
  const { data } = await api.get("/templates", { params });
  return data;
}

export async function getTemplate(templateId) {
  const { data } = await api.get(`/templates/${templateId}`);
  return data;
}

export async function listDrafts(matterId) {
  const params = matterId ? { matter_id: matterId } : {};
  const { data } = await api.get("/drafts", { params });
  return data;
}

export async function createDraft(templateId, title, matterId, inputs = {}) {
  const { data } = await api.post("/drafts", {
    template_id: templateId,
    title,
    matter_id: matterId,
    inputs,
  });
  return data;
}

export async function getDraft(draftId) {
  const { data } = await api.get(`/drafts/${draftId}`);
  return data;
}

export async function autosaveDraftInputs(draftId, inputs, title) {
  const { data } = await api.put(`/drafts/${draftId}/inputs`, { inputs, title });
  return data;
}

export async function generateDraft(draftId) {
  const { data } = await api.post(`/drafts/${draftId}/generate`);
  return data;
}

export async function getDraftPreview(draftId) {
  const { data } = await api.get(`/drafts/${draftId}/preview`);
  return data;
}

export async function exportDraft(draftId, format = "pdf", allowPartial = true) {
  const { data } = await api.post(`/drafts/${draftId}/exports`, { format, allow_partial: allowPartial });
  return data;
}

export async function smartIntake(templateId, message, fileContent, fileName, currentInputs, targetLanguage) {
  const { data } = await api.post("/drafts/smart-intake", {
    template_id: templateId,
    message,
    file_content: fileContent,
    file_name: fileName,
    current_inputs: currentInputs,
    target_language: targetLanguage,
  });
  return data;
}
