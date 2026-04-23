import { apiJson } from "./client";
import type { TaskRecord, Finding, Recommendation, TaskArtifacts } from "../types";

export function getTask(taskId: string): Promise<TaskRecord> {
  return apiJson<TaskRecord>(`/tasks/${taskId}`);
}

export function listTasks(): Promise<TaskRecord[]> {
  return apiJson<TaskRecord[]>("/tasks");
}

export function getTaskFindings(taskId: string): Promise<Finding[]> {
  return apiJson<Finding[]>(`/tasks/${taskId}/findings`);
}

export function getTaskRecommendations(taskId: string): Promise<Recommendation[]> {
  return apiJson<Recommendation[]>(`/tasks/${taskId}/recommendations`);
}

export function getTaskArtifacts(taskId: string): Promise<TaskArtifacts> {
  return apiJson<TaskArtifacts>(`/tasks/${taskId}/artifacts`);
}
