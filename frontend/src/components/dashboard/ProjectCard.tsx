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
    seoScore == null ? "bg-slate-300"
    : seoScore >= 0.7 ? "bg-emerald-500"
    : seoScore >= 0.4 ? "bg-amber-400"
    : "bg-rose-500";
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
      className="group block overflow-hidden rounded-3xl bg-white p-5 ring-1 ring-slate-200/70 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_12px_32px_rgb(15,23,42,0.06)] hover:ring-slate-300"
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-50 text-slate-400 transition-colors group-hover:bg-slate-100 group-hover:text-slate-800">
              <Activity size={16} strokeWidth={2} />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-base font-semibold text-slate-800 tracking-tight leading-tight truncate">{project.brand_name}</h3>
                <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${dotColor}`} />
              </div>
              <p className="mt-0.5 text-xs text-slate-400 truncate">{project.url}</p>
            </div>
          </div>
        </div>
        <div className="ml-3 flex items-center gap-2 shrink-0">
          <span className="rounded-md bg-slate-50 px-2 py-1 text-[10px] font-medium tracking-wider text-slate-500 uppercase">
            {project.category === "auto" ? t("project.categoryAuto") : project.category}
          </span>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2">
        {[
          { label: t("projectCard.freshness"), value: freshnessValue },
          { label: t("dashboard.pendingReviews"), value: reviewValue },
          { label: t("score.findings"), value: findingsValue },
          { label: t("project.reports"), value: reportValue },
        ].map((item) => (
          <div key={item.label} className="rounded-2xl bg-slate-50 px-3 py-3">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">
              {item.label}
            </p>
            <p className="mt-1 text-sm font-semibold text-slate-900">{item.value}</p>
          </div>
        ))}
      </div>

      <p className="mt-4 text-xs leading-6 text-slate-500">
        {projectStatus}
      </p>
    </Link>
  );
}
