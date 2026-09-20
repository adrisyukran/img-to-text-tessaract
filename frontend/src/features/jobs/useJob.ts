import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../api/client";
import type { JobStatus } from "../../api/types";

export function useJob(jobId: string | null) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.get<JobStatus>("/jobs/" + jobId),
    enabled: Boolean(jobId),
    retry: false,
    refetchInterval: (current) =>
      current.state.data?.stage === "complete" || current.state.data?.stage === "failed"
        ? false
        : 2000,
  });

  useEffect(() => {
    if (!jobId || typeof EventSource === "undefined") return;
    const source = new EventSource("/api/v1/jobs/" + jobId + "/events");
    const onProgress = (event: MessageEvent<string>) => {
      const next = JSON.parse(event.data) as JobStatus;
      queryClient.setQueryData<JobStatus>(["job", jobId], (current) =>
        !current || next.revision > current.revision ? next : current,
      );
      if (next.stage === "complete" || next.stage === "failed") {
        source.close();
      }
    };
    source.addEventListener("job.progress", onProgress);
    source.onerror = () => {
      source.close();
      void queryClient.invalidateQueries({ queryKey: ["job", jobId] });
    };
    return () => {
      source.removeEventListener("job.progress", onProgress);
      source.close();
    };
  }, [jobId, queryClient]);

  return query;
}
