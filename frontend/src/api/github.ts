import { apiJson } from "./client";
import type {
  GitHubLead,
  GitHubDiscoveryRun,
  GitHubLeadStats,
} from "../types";

export function listGitHubLeads(
  projectId: number,
  params?: Record<string, string>,
): Promise<{ leads: GitHubLead[]; total: number }> {
  const qs = params ? `?${new URLSearchParams(params)}` : "";
  return apiJson(`/projects/${projectId}/github-leads${qs}`);
}

export function getLeadStats(projectId: number): Promise<GitHubLeadStats> {
  return apiJson(`/projects/${projectId}/github-leads/stats`);
}

export function startGitHubDiscovery(
  projectId: number,
  seedUsername: string,
  source = "both",
  maxHops = 1,
): Promise<{ task_id: string; run: GitHubDiscoveryRun }> {
  return apiJson(`/projects/${projectId}/github-discover`, {
    method: "POST",
    body: JSON.stringify({
      seed_username: seedUsername,
      source,
      max_hops: maxHops,
    }),
  });
}

export function listDiscoveryRuns(
  projectId: number,
): Promise<GitHubDiscoveryRun[]> {
  return apiJson(`/projects/${projectId}/github-discovery-runs`);
}

export function updateLeadStatus(
  projectId: number,
  login: string,
  status: string,
): Promise<{ ok: boolean }> {
  return apiJson(`/projects/${projectId}/github-leads/${login}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function generateOutreach(
  projectId: number,
  logins: string[],
  channel: string,
): Promise<{
  ok: boolean;
  count: number;
  approvals: { login: string; approval_id: number }[];
}> {
  return apiJson(`/projects/${projectId}/github-leads/generate-outreach`, {
    method: "POST",
    body: JSON.stringify({ logins, channel }),
  });
}

export function scoreLeads(
  projectId: number,
): Promise<{ scored: number; stats: GitHubLeadStats }> {
  return apiJson(`/projects/${projectId}/github-leads/score`, {
    method: "POST",
  });
}

export function deleteAllLeads(
  projectId: number,
): Promise<{ ok: boolean; deleted: number }> {
  return apiJson(`/projects/${projectId}/github-leads`, { method: "DELETE" });
}
