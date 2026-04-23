import { useQuery } from "@tanstack/react-query";
import { getSettings } from "../api/settings";
import type { AISettings } from "../types";

export function useSettings() {
  return useQuery<AISettings>({
    queryKey: ["settings"],
    queryFn: getSettings,
    staleTime: 30_000,
  });
}
