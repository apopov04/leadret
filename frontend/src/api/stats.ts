import { apiFetch } from "./client";
import type { Stats } from "../types";

export function fetchStats(campaign: string) {
  const params = new URLSearchParams({ campaign });
  return apiFetch<Stats>(`/stats?${params}`);
}
