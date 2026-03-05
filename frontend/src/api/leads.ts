import { apiFetch } from "./client";
import type { Lead } from "../types";

export function fetchQueue(campaign: string, limit = 50, offset = 0) {
  const params = new URLSearchParams({ campaign, limit: String(limit), offset: String(offset) });
  return apiFetch<Lead[]>(`/leads/queue?${params}`);
}

export function fetchRated(campaign: string, limit = 200) {
  const params = new URLSearchParams({ campaign, limit: String(limit) });
  return apiFetch<Lead[]>(`/leads/rated?${params}`);
}

export function fetchLead(id: number) {
  return apiFetch<Lead>(`/leads/${id}`);
}

export function patchLead(id: number, body: Partial<Pick<Lead, "user_rating" | "website_url" | "feedback">>) {
  return apiFetch<Lead>(`/leads/${id}`, { method: "PATCH", body: JSON.stringify(body) });
}

export function deleteLead(id: number) {
  return apiFetch<{ ok: boolean }>(`/leads/${id}`, { method: "DELETE" });
}
