/**
 * frontend/src/api/newsApi.js
 * ───────────────────────────
 * Fetches Indian legal news & court case updates.
 */

import api from "./client";

export async function getIndianLegalNews(query = "", limit = 5) {
  const params = new URLSearchParams();
  if (query) params.append("query", query);
  if (limit) params.append("limit", limit.toString());

  const response = await api.get(`/news/legal?${params.toString()}`);
  return response.data;
}
