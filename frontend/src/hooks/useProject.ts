import { useQuery } from "@tanstack/react-query";
import { getProject, getProjectSummary, getNextActions, pauseProject, resumeProject } from "../api/projects";
import type { NextAction } from "../api/projects";
import type { ProjectSummary } from "../types";

export function useProject(id: number) {
  return useQuery({
    queryKey: ["project", id],
    queryFn: () => getProject(id),
  });
}

export function useProjectSummary(id: number) {
  return useQuery<ProjectSummary>({
    queryKey: ["project-summary", id],
    queryFn: () => getProjectSummary(id),
  });
}

export function useNextActions(id: number, enabled = true) {
  return useQuery<{ actions: NextAction[] }>({
    queryKey: ["next-actions", id],
    queryFn: () => getNextActions(id),
    enabled,
    refetchInterval: 60_000,
  });
}

import { useMutation, useQueryClient } from "@tanstack/react-query";

export function useSetProjectPause() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, pause }: { id: number; pause: boolean }) =>
      pause ? pauseProject(id) : resumeProject(id),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({ queryKey: ["project-summary", id] });
    },
  });
}
