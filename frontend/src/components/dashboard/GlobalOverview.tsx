import { Link } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { Bot, CheckSquare, GitBranch, Globe, Search, Users } from "lucide-react";
import { apiJson } from "../../api/client";
import { useI18n } from "../../i18n";

interface OverviewData {
  project_count: number;
  avg_seo_score: number | null;
  avg_geo_score: number | null;
  total_community_hits: number;
  total_keywords: number;
  total_competitors: number;
  projects_updated_today: number;
  urgent_findings: number;
  ready_actions: number;
  pending_approvals: number;
  recent_campaigns: Array<{
    id: number;
    goal: string;
    brand_name: string;
    status: string;
    channels: string[];
    created_at: string;
  }>;
}

function useOverview() {
  return useQuery<OverviewData>({
    queryKey: ["overview"],
    queryFn: () => apiJson<OverviewData>("/overview"),
    refetchInterval: 60_000,
  });
}

function SummaryCard({
  label,
  value,
  body,
  actionLabel,
  actionTo,
}: {
  label: string;
  value: string | number;
  body: string;
  actionLabel: string;
  actionTo: string;
}) {
  return (
    <article className="rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-sm">
      <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">
        {label}
      </p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{body}</p>
      {actionTo.startsWith("#") ? (
        <a
          href={actionTo}
          className="mt-4 inline-flex items-center rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-slate-800"
        >
          {actionLabel}
        </a>
      ) : (
        <Link
          to={actionTo}
          className="mt-4 inline-flex items-center rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-slate-800"
        >
          {actionLabel}
        </Link>
      )}
    </article>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number | null;
}) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-slate-200/80 bg-white/90 p-4 shadow-sm">
      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
        <Icon size={18} />
      </div>
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">{label}</p>
        <p className="mt-1 text-lg font-semibold text-slate-950">{value ?? "—"}</p>
      </div>
    </div>
  );
}

export function GlobalOverview() {
  const { data } = useOverview();
  const { t } = useI18n();

  if (!data || data.project_count === 0) return null;

  return (
    <section className="mb-8 space-y-5">
      <div className="rounded-3xl border border-slate-200/80 bg-[radial-gradient(circle_at_top,_rgba(99,102,241,0.08),_transparent_40%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-6 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-white">
            <Bot size={18} />
          </div>
          <div className="max-w-3xl">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">
              {t("dashboard.summaryTitle")}
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
              {t("dashboard.summarySubtitle")}
            </h2>
          </div>
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          <SummaryCard
            label={t("command.changedToday")}
            value={data.projects_updated_today}
            body={t("dashboard.updatedProjects", { count: data.projects_updated_today, total: data.project_count })}
            actionLabel={t("command.reviewProjects")}
            actionTo="#project-grid"
          />
          <SummaryCard
            label={t("command.whatMattersNow")}
            value={data.urgent_findings}
            body={t("dashboard.findingsReady", {
              count: data.urgent_findings,
              approvals: data.pending_approvals,
            })}
            actionLabel={t("command.openOpportunities")}
            actionTo="#project-grid"
          />
          <SummaryCard
            label={t("command.readyToShip")}
            value={data.ready_actions}
            body={t("dashboard.actionsReady", {
              count: data.ready_actions,
              approvals: data.pending_approvals,
            })}
            actionLabel={t("command.reviewDraft")}
            actionTo="/approvals"
          />
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard
          icon={Search}
          label={t("overview.avgSeo")}
          value={data.avg_seo_score != null ? `${data.avg_seo_score}%` : null}
        />
        <MetricCard
          icon={Globe}
          label={t("overview.avgGeo")}
          value={data.avg_geo_score != null ? `${data.avg_geo_score}/100` : null}
        />
        <MetricCard
          icon={Users}
          label={t("overview.communityHits")}
          value={data.total_community_hits}
        />
        <MetricCard
          icon={GitBranch}
          label={t("overview.competitors")}
          value={data.total_competitors}
        />
        <MetricCard
          icon={CheckSquare}
          label={t("dashboard.pendingReviews")}
          value={data.pending_approvals}
        />
      </div>
    </section>
  );
}
