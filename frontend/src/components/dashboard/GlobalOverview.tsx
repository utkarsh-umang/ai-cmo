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
    <article className="rounded-3xl border border-brand-100 bg-white/60 p-6 shadow-sm transition-all duration-300 hover:shadow-md hover:bg-white/80">
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-accent-dark/40">
        {label}
      </p>
      <p className="mt-4 text-4xl font-bold tracking-tight text-foreground">{value}</p>
      <p className="mt-3 text-[14px] leading-relaxed text-accent-dark/70 font-bold">{body}</p>
      {actionTo.startsWith("#") ? (
        <a
          href={actionTo}
          className="mt-6 inline-flex items-center rounded-xl bg-brand-500 px-5 py-2.5 text-xs font-bold text-white transition-all hover:bg-brand-600 hover:shadow-lg hover:shadow-brand-500/20"
        >
          {actionLabel}
        </a>
      ) : (
        <Link
          to={actionTo}
          className="mt-6 inline-flex items-center rounded-xl bg-brand-500 px-5 py-2.5 text-xs font-bold text-white transition-all hover:bg-brand-600 hover:shadow-lg hover:shadow-brand-500/20"
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
    <div className="flex items-center gap-4 rounded-[2rem] border border-brand-100 bg-white/60 p-5 shadow-sm transition-all hover:shadow-md hover:bg-white/80">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
        <Icon size={20} />
      </div>
      <div>
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-accent-dark/30">{label}</p>
        <p className="mt-1 text-lg font-bold text-foreground">{value ?? "—"}</p>
      </div>
    </div>
  );
}

export function GlobalOverview() {
  const { data } = useOverview();
  const { t } = useI18n();

  if (!data || data.project_count === 0) return null;

  return (
    <section className="mb-10 space-y-6">
      <div className="rounded-[3rem] border border-brand-100 bg-[radial-gradient(circle_at_top_right,_rgba(201,106,90,0.08),_transparent_45%),linear-gradient(180deg,#ffffff_0%,#f4efeb_100%)] p-8 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-3xl bg-accent-dark text-white shadow-xl shadow-accent-dark/20">
            <Bot size={24} />
          </div>
          <div className="max-w-3xl">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-brand-500">
              {t("dashboard.summaryTitle")}
            </p>
            <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-foreground">
              {t("dashboard.summarySubtitle")}
            </h2>
          </div>
        </div>

        <div className="mt-8 grid gap-5 lg:grid-cols-3">
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

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
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
