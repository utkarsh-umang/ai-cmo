import type { LatestScans } from "../../types";
import { useI18n } from "../../i18n";

export function ScanHistoryTable({ latest }: { latest: LatestScans }) {
  const { t } = useI18n();

  const rows = [
    { type: t("project.seo"), date: latest.seo?.scanned_at, detail: latest.seo?.score != null ? `${Math.round(latest.seo.score * 100)}%` : "—" },
    { type: t("project.geo"), date: latest.geo?.scanned_at, detail: latest.geo?.score != null ? `${latest.geo.score}/100` : "—" },
    { type: t("project.community"), date: latest.community?.scanned_at, detail: latest.community?.total_hits != null ? t("scan.hits", { count: latest.community.total_hits }) : "—" },
  ];

  return (
    <div className="overflow-hidden rounded-2xl bg-slate-50/50">
      <div className="px-6 py-5">
        <h3 className="font-semibold text-slate-900">{t("scan.latestScans")}</h3>
      </div>
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-slate-400 text-xs uppercase tracking-wider">
            <th className="px-6 py-3 font-medium">{t("scan.type")}</th>
            <th className="px-6 py-3 font-medium">{t("scan.lastScanned")}</th>
            <th className="px-6 py-3 font-medium">{t("scan.result")}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((r) => (
            <tr key={r.type} className="transition-colors hover:bg-white group">
              <td className="px-6 py-4 font-medium text-slate-800">{r.type}</td>
              <td className="px-6 py-4 text-slate-500 tabular-nums">{r.date?.slice(0, 10) ?? t("common.never")}</td>
              <td className="px-6 py-4 text-slate-700 font-medium">{r.detail}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
