import type { LatestScans, MonitoringSummary } from "../../types";
import { StatusBadge } from "../dashboard/StatusBadge";
import { useI18n } from "../../i18n";

export function ScorePanel({
  latest,
  latestMonitoring,
}: {
  latest: LatestScans;
  previous?: {
    seo?: { scanned_at: string; score: number | null };
    geo?: { scanned_at: string; score: number };
  } | null;
  latestMonitoring?: MonitoringSummary | null;
}) {
  const { t } = useI18n();

  return (
    <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-6">
      <StatusBadge
        label={t("score.seoScore")}
        value={
          latest.seo?.score != null
            ? `${Math.round(latest.seo.score * 100)}%`
            : t("common.noData")
        }
        color={latest.seo?.score != null && latest.seo.score >= 0.8 ? "green" : "gray"}
      />
      <StatusBadge
        label={t("score.geoScore")}
        value={
          latest.geo?.score != null ? `${latest.geo.score}/100` : t("common.noData")
        }
        color={latest.geo?.score != null && latest.geo.score >= 60 ? "green" : "gray"}
      />
      <StatusBadge
        label={t("score.communityHits")}
        value={
          latest.community?.total_hits != null
            ? String(latest.community.total_hits)
            : t("common.noData")
        }
        color={latest.community?.total_hits ? "blue" : "gray"}
      />
      <StatusBadge
        label={t("score.serpKeywords")}
        value={latest.serp?.length ? t("score.tracked", { count: latest.serp.length }) : t("common.noData")}
        color={latest.serp?.length ? "purple" : "gray"}
      />
      <StatusBadge
        label={t("score.findings")}
        value={
          latestMonitoring?.findings_count != null
            ? String(latestMonitoring.findings_count)
            : t("common.noData")
        }
        color={
          (latestMonitoring?.findings_count ?? 0) > 0
            ? "red"
            : "gray"
        }
      />
      <StatusBadge
        label={t("score.recommendations")}
        value={
          latestMonitoring?.recommendations_count != null
            ? String(latestMonitoring.recommendations_count)
            : t("common.noData")
        }
        color={
          (latestMonitoring?.recommendations_count ?? 0) > 0
            ? "blue"
            : "gray"
        }
      />
    </div>
  );
}
