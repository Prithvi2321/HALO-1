/**
 * src/api/telegramApi.js
 * ──────────────────────
 * API client for Telegram Bot Gateway (PRD §8 & §11.3).
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
    const msg = data?.detail || data?.message || err.message;
    return Promise.reject(new Error(msg || "Telegram API request failed."));
  }
);

export async function generatePairingCode(userId = 1) {
  const { data } = await api.post("/telegram/pairing-codes", null, {
    params: { user_id: userId },
  });
  return data;
}

export async function getPairingStatus(userId = 1) {
  const { data } = await api.get("/telegram/status", {
    params: { user_id: userId },
  });
  return data;
}

export async function unpairTelegram(userId = 1) {
  const { data } = await api.delete("/telegram/link", {
    params: { user_id: userId },
  });
  return data;
}

