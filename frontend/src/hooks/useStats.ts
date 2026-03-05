import { useQuery } from "@tanstack/react-query";
import { fetchStats } from "../api/stats";

export function useStats(campaign: string) {
  return useQuery({
    queryKey: ["stats", campaign],
    queryFn: () => fetchStats(campaign),
  });
}
