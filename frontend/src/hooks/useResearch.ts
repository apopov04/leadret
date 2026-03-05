import { useState, useRef, useCallback, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { startResearch, fetchJobStatus } from "../api/research";
import type { ResearchJobStatus } from "../types";

export function useResearch() {
  const [job, setJob] = useState<ResearchJobStatus | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const intervalRef = useRef<number | null>(null);
  const dismissRef = useRef<number | null>(null);
  const qc = useQueryClient();

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Clean up timers on unmount
  useEffect(() => () => {
    stopPolling();
    if (dismissRef.current) clearTimeout(dismissRef.current);
  }, [stopPolling]);

  const run = useCallback(
    async (body: { campaign?: string; prompt?: string; provider: string }) => {
      if (isRunning) return;
      setIsRunning(true);
      setJob(null);

      try {
        const { job_id } = await startResearch(body);
        setJob({ job_id, status: "pending", progress: 0, phase: "QUEUED", result: null, error: null });

        intervalRef.current = window.setInterval(async () => {
          try {
            const status = await fetchJobStatus(job_id);
            setJob(status);

            if (status.status === "completed" || status.status === "failed") {
              stopPolling();
              setIsRunning(false);
              qc.invalidateQueries({ queryKey: ["leads"] });
              qc.invalidateQueries({ queryKey: ["stats"] });
              dismissRef.current = window.setTimeout(() => setJob(null), 5000);
            }
          } catch {
            stopPolling();
            setIsRunning(false);
          }
        }, 1500);
      } catch (e: any) {
        setJob({ job_id: "", status: "failed", progress: 1, phase: "ERROR", result: null, error: e.message || "Failed to start research" });
        setIsRunning(false);
      }
    },
    [qc, stopPolling, isRunning]
  );

  return { job, isRunning, run };
}
