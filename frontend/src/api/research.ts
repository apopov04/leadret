import { apiFetch } from "./client";
import type { ResearchJobStatus, ProviderInfo } from "../types";

export function startResearch(body: { campaign?: string; prompt?: string; provider: string }) {
  return apiFetch<{ job_id: string }>("/research", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchJobStatus(jobId: string) {
  return apiFetch<ResearchJobStatus>(`/research/${jobId}`);
}

export function fetchProviders() {
  return apiFetch<ProviderInfo[]>("/config/providers");
}
