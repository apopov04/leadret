import { apiFetch } from "./client";
import type { Campaign } from "../types";

export function fetchCampaigns() {
  return apiFetch<Campaign[]>("/campaigns");
}

export function createCampaign(name: string, description: string) {
  return apiFetch<Campaign>("/campaigns", {
    method: "POST",
    body: JSON.stringify({ name, description }),
  });
}

export function updateCampaign(filename: string, name: string, description: string) {
  return apiFetch<Campaign>(`/campaigns/${filename}`, {
    method: "PATCH",
    body: JSON.stringify({ name, description }),
  });
}

export function deleteCampaign(filename: string) {
  return apiFetch<void>(`/campaigns/${filename}`, { method: "DELETE" });
}
