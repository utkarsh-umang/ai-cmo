import { Link } from "react-router";
import { Activity } from "lucide-react";
import type { Project } from "../../types";
import { useI18n } from "../../i18n";
import { utcDate } from "../../utils/time";

function getLatestActivity(project: Project) {
  const timestamps = [
    project.latest?.seo?.scanned_at,
    project.latest?.geo?.scanned_at,
    project.latest?.community?.scanned_at,
    ...(project.latest?.serp ?? []).map((item) => item.checked_at ?? null),
  ]
    .filter((value): value is string => Boolean(value))
    .map((value) => utcDate(value).getTime());

  if (timestamps.length === 0) return null;
  return new Date(Math.max(...timestamps));
}

function hasReadyReport(project: Project) {
  return Boolean(
    project.latest_reports?.strategic?.human ||
      project.latest_reports?.strategic?.agent ||
      project.latest_reports?.periodic?.human ||
      project.latest_reports?.periodic?.agent,
  );
}

export function ProjectCard({ project }: { project: Project }) {
  const { latest } = project;
  const { t, locale } = useI18n();

  const seoScore = latest?.seo?.score ?? null;
  const dotColor =
    seoScore == null ? "bg-accent-dark/20"
    : seoScore >= 0.7 ? "bg-emerald-500"
    : seoScore >= 0.4 ? "bg-brand-400"
    : "bg-brand-600";
  const latestActivity = getLatestActivity(project);
  const freshnessValue = latestActivity
    ? Date.now() - latestActivity.getTime() <= 24 * 60 * 60 * 1000
      ? t("projectCard.fresh")
      : new Intl.DateTimeFormat(locale, {
          month: "short",
          day: "numeric",
        }).format(latestActivity)
    : t("common.noData");
  const findingsValue = project.latest_monitoring?.findings_count != null
    ? String(project.latest_monitoring.findings_count)
    : t("common.noData");
  const reviewValue = project.pending_approvals != null
    ? String(project.pending_approvals)
    : t("common.noData");
  const reportValue = hasReadyReport(project) ? t("projectCard.reportReady") : t("projectCard.reportPending");
  const projectStatus =
    (project.pending_approvals ?? 0) > 0
      ? t("projectCard.pendingApprovals", { count: project.pending_approvals ?? 0 })
      : (project.latest_monitoring?.findings_count ?? 0) > 0
        ? t("projectCard.findingsSummary", { count: project.latest_monitoring?.findings_count ?? 0 })
        : hasReadyReport(project)
          ? t("projectCard.reportSummary")
          : t("projectCard.noScans");

  return (
    <Link
      to={`/projects/${project.id}`}
      className="group block overflow-hidden rounded-[2rem] bg-white p-6 border border-brand-100/50 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-brand-500/5 hover:border-brand-300"
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-bg-cream text-accent-dark transition-all duration-300 group-hover:bg-brand-500 group-hover:text-white">
              <Activity size={20} strokeWidth={2.5} />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="font-display text-lg font-bold text-foreground tracking-tight truncate group-hover:text-brand-600 transition-colors">{project.brand_name}</h3>
                <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${dotColor}`} />
              </div>
              <p className="mt-0.5 text-xs font-bold text-accent-dark/40 truncate tracking-wide">{project.url.replace(/^https?:\/\/(www\.)?/, '')}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3">
        {[
          { label: t("projectCard.freshness"), value: freshnessValue },
          { label: t("dashboard.pendingReviews"), value: reviewValue },
          { label: t("score.findings"), value: findingsValue },
          { label: t("project.reports"), value: reportValue },
        ].map((item) => (
          <div key={item.label} className="rounded-2xl bg-bg-cream/60 px-4 py-3.5 transition-colors group-hover:bg-bg-cream/80">
            <p className="text-[9px] font-black uppercase tracking-[0.2em] text-accent-dark/30">
              {item.label}
            </p>
            <p className="mt-1.5 text-sm font-bold text-foreground">{item.value}</p>
          </div>
        ))}
      </div>

      <div className="mt-6 flex items-center justify-between border-t border-brand-50 pt-4">
        <p className="text-xs font-bold text-accent-dark/60 leading-tight">
          {projectStatus}
        </p>
        <span className="text-[10px] font-black uppercase tracking-widest text-brand-500 opacity-0 group-hover:opacity-100 transition-opacity">
          View Detail →
        </span>
      </div>
    </Link>
  );
}
