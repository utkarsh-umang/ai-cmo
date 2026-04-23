import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getInsights, getInsightsSummary, markInsightRead } from "../api/insights";
import { useI18n } from "../i18n";

export function useInsightsSummary(projectId?: number) {
  const { locale } = useI18n();
  return useQuery({
    queryKey: ["insights-summary", projectId ?? null, locale],
    queryFn: () => getInsightsSummary(projectId, locale),
    refetchInterval: 30_000,
  });
}

export function useInsights(projectId?: number, unread = false) {
  const { locale } = useI18n();
  return useQuery({
    queryKey: ["insights", projectId ?? null, unread, locale],
    queryFn: () => getInsights(projectId, unread, locale),
  });
}

export function useMarkInsightRead() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => markInsightRead(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["insights-summary"] });
      qc.invalidateQueries({ queryKey: ["insights"] });
    },
  });
}
