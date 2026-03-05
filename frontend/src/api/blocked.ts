import { apiFetch } from "./client";
import type { BlockedCompany } from "../types";

export function fetchBlocked() {
  return apiFetch<BlockedCompany[]>("/blocked");
}

export function blockCompany(company_name: string, reason = "") {
  return apiFetch<{ ok: boolean }>("/blocked", {
    method: "POST",
    body: JSON.stringify({ company_name, reason }),
  });
}

export function unblockCompany(company_name: string) {
  return apiFetch<{ ok: boolean }>(`/blocked/${encodeURIComponent(company_name)}`, {
    method: "DELETE",
  });
}
