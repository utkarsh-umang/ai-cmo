import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { getTask, getTaskArtifacts, getTaskFindings, getTaskRecommendations } from "../api/tasks";
import type { Finding, Recommendation, TaskArtifacts } from "../types";

const STALE_TASK_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes (matches backend stale threshold)

export function useTaskPoll(taskId: string | null) {
  return useQuery({
    queryKey: ["task", taskId],
    queryFn: () => getTask(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") return false;
      return 2000;
    },
  });
}

/**
 * Returns true when the task is still reported as "running" but the progress
 * list has not grown for longer than STALE_TASK_TIMEOUT_MS (2 min).
 */
export function useTaskStale(
  status: string | undefined,
  progressLength: number,
): boolean {
  const lastChangeRef = useRef<{ length: number; at: number }>({
    length: progressLength,
    at: Date.now(),
  });

  if (progressLength !== lastChangeRef.current.length) {
    lastChangeRef.current = { length: progressLength, at: Date.now() };
  }

  if (status !== "running") return false;
  return Date.now() - lastChangeRef.current.at > STALE_TASK_TIMEOUT_MS;
}

export function useTaskFindings(taskId: string | null, enabled = true) {
  return useQuery<Finding[]>({
    queryKey: ["task-findings", taskId],
    queryFn: () => getTaskFindings(taskId!),
    enabled: !!taskId && enabled,
  });
}

export function useTaskRecommendations(taskId: string | null, enabled = true) {
  return useQuery<Recommendation[]>({
    queryKey: ["task-recommendations", taskId],
    queryFn: () => getTaskRecommendations(taskId!),
    enabled: !!taskId && enabled,
  });
}

export function useTaskArtifacts(taskId: string | null, enabled = true, live = false) {
  return useQuery<TaskArtifacts>({
    queryKey: ["task-artifacts", taskId],
    queryFn: () => getTaskArtifacts(taskId!),
    enabled: !!taskId && enabled,
    refetchInterval: live ? 2000 : false,
  });
}
