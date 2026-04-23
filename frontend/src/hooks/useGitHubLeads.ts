import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listGitHubLeads,
  getLeadStats,
  startGitHubDiscovery,
  listDiscoveryRuns,
  generateOutreach,
  scoreLeads,
} from "../api/github";

export function useGitHubLeads(
  projectId: number,
  filters?: Record<string, string>,
) {
  return useQuery({
    queryKey: ["github-leads", projectId, filters],
    queryFn: () => listGitHubLeads(projectId, filters),
  });
}

export function useLeadStats(projectId: number) {
  return useQuery({
    queryKey: ["github-lead-stats", projectId],
    queryFn: () => getLeadStats(projectId),
  });
}

export function useDiscoveryRuns(projectId: number) {
  return useQuery({
    queryKey: ["github-discovery-runs", projectId],
    queryFn: () => listDiscoveryRuns(projectId),
    refetchInterval: (query) => {
      const runs = query.state.data;
      if (runs?.some((r) => r.status === "running")) return 5000;
      return false;
    },
  });
}

export function useStartDiscovery() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      projectId,
      seedUsername,
      source,
      maxHops,
    }: {
      projectId: number;
      seedUsername: string;
      source?: string;
      maxHops?: number;
    }) => startGitHubDiscovery(projectId, seedUsername, source, maxHops),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({
        queryKey: ["github-leads", vars.projectId],
      });
      qc.invalidateQueries({
        queryKey: ["github-lead-stats", vars.projectId],
      });
      qc.invalidateQueries({
        queryKey: ["github-discovery-runs", vars.projectId],
      });
    },
  });
}

export function useGenerateOutreach() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      projectId,
      logins,
      channel,
    }: {
      projectId: number;
      logins: string[];
      channel: string;
    }) => generateOutreach(projectId, logins, channel),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({
        queryKey: ["github-leads", vars.projectId],
      });
      qc.invalidateQueries({ queryKey: ["approvals"] });
    },
  });
}

export function useScoreLeads() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId }: { projectId: number }) =>
      scoreLeads(projectId),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({
        queryKey: ["github-leads", vars.projectId],
      });
      qc.invalidateQueries({
        queryKey: ["github-lead-stats", vars.projectId],
      });
    },
  });
}
