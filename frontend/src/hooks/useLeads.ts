import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchQueue, fetchRated, patchLead, deleteLead } from "../api/leads";
import { blockCompany } from "../api/blocked";

export function useQueueLeads(campaign: string) {
  return useQuery({
    queryKey: ["leads", "queue", campaign],
    queryFn: () => fetchQueue(campaign),
  });
}

export function useRatedLeads(campaign: string) {
  return useQuery({
    queryKey: ["leads", "rated", campaign],
    queryFn: () => fetchRated(campaign),
  });
}

export function useRateLead(campaign: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, rating }: { id: number; rating: number }) =>
      patchLead(id, { user_rating: rating }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads", "queue", campaign] });
      qc.invalidateQueries({ queryKey: ["leads", "rated", campaign] });
      qc.invalidateQueries({ queryKey: ["stats", campaign] });
    },
  });
}

export function useDeleteLead(campaign: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteLead(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads", "queue", campaign] });
      qc.invalidateQueries({ queryKey: ["stats", campaign] });
    },
  });
}

export function useBlockCompany(campaign: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (company_name: string) => blockCompany(company_name, "Blocked from dashboard"),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads", "queue", campaign] });
      qc.invalidateQueries({ queryKey: ["stats", campaign] });
      qc.invalidateQueries({ queryKey: ["blocked"] });
    },
  });
}

export function useResetRating(campaign: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => patchLead(id, { user_rating: null as unknown as number }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads", "queue", campaign] });
      qc.invalidateQueries({ queryKey: ["leads", "rated", campaign] });
      qc.invalidateQueries({ queryKey: ["stats", campaign] });
    },
  });
}

export function useUpdateWebsite(campaign: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, url }: { id: number; url: string }) =>
      patchLead(id, { website_url: url }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads", "queue", campaign] });
    },
  });
}
