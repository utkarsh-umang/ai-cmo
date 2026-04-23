import { useState } from "react";
import { Link } from "react-router";
import { Trash2, Clock, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";
import type { Monitor } from "../../types";
import { RunScanButton } from "./RunScanButton";
import { RunHistoryPanel } from "./RunHistoryPanel";
import { ScheduleSelector, cronToHuman } from "./ScheduleSelector";
import { useUpdateMonitor } from "../../hooks/useMonitors";
import { useI18n } from "../../i18n";

export function MonitorList({
  monitors,
  onDelete,
  onTaskCreated,
  onSelectRun,
}: {
  monitors: Monitor[];
  onDelete: (id: number) => void;
  onTaskCreated?: (taskId: string, url: string) => void;
  onSelectRun?: (taskId: string, url: string) => void;
}) {
  const { t, locale } = useI18n();
  const updateMonitor = useUpdateMonitor();
  const [editingId, setEditingId] = useState<number | null>(null);

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {monitors.map((m) => {
        const isEditing = editingId === m.id;

        return (
          <div
            key={m.id}
            className="group relative overflow-hidden rounded-xl border border-zinc-200/60 bg-white p-5 shadow-sm ring-1 ring-zinc-950/5 transition-all duration-300 hover:shadow-lg"
          >
            {/* Header: brand + category */}
            <div className="mb-3 flex items-start justify-between">
              <div className="min-w-0 flex-1">
                <Link
                  to={`/projects/${m.project_id}`}
                  className="text-base font-semibold text-zinc-900 hover:text-indigo-600 transition-colors"
                >
                  {m.brand_name}
                </Link>
                <a
                  href={m.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-0.5 flex items-center gap-1 text-xs text-zinc-400 hover:text-indigo-500 transition-colors"
                >
                  <span className="truncate">{m.url}</span>
                  <ExternalLink size={10} className="shrink-0" />
                </a>
              </div>
              <span className="ml-2 shrink-0 rounded-md bg-indigo-50 ring-1 ring-indigo-200/50 px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-indigo-600">
                {m.job_type}
              </span>
            </div>

            {/* Schedule info row */}
            <div className="mb-3 flex items-center justify-between">
              <button
                onClick={() => setEditingId(isEditing ? null : m.id)}
                className="flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium text-zinc-600 transition-all hover:bg-zinc-50 active:scale-95"
              >
                <Clock size={12} className="text-zinc-400" />
                <span>{cronToHuman(m.cron_expr, locale, t)}</span>
                {isEditing ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              </button>

              {/* Enable/Disable toggle */}
              <button
                onClick={() =>
                  updateMonitor.mutate({ id: m.id, enabled: !m.enabled })
                }
                className="relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors duration-200 focus:outline-none"
                style={{
                  backgroundColor: m.enabled ? "#6366f1" : "#d4d4d8",
                }}
                title={m.enabled ? t("schedule.disable") : t("schedule.enable")}
              >
                <span
                  className={`
                    inline-block h-3.5 w-3.5 rounded-full bg-white shadow-sm transition-transform duration-200
                    ${m.enabled ? "translate-x-[18px]" : "translate-x-[3px]"}
                  `}
                />
              </button>
            </div>

            {/* Inline schedule editor (collapsible) */}
            {isEditing && (
              <div className="mb-3 rounded-xl bg-zinc-50/80 p-3 ring-1 ring-zinc-100 animate-in fade-in slide-in-from-top-2 duration-200">
                <ScheduleSelector
                  value={m.cron_expr}
                  onChange={(cron) => {
                    updateMonitor.mutate({ id: m.id, cron_expr: cron });
                    setEditingId(null);
                  }}
                  compact
                />
              </div>
            )}

            {/* Meta: last run */}
            <div className="mb-4 text-[11px] text-zinc-400">
              {t("monitorList.lastRun")}: {m.last_run_at?.slice(0, 16).replace("T", " ") ?? t("common.never")}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between border-t border-zinc-100 pt-3">
              <RunScanButton
                monitorId={m.id}
                projectId={m.project_id}
                onTaskCreated={(taskId) => onTaskCreated?.(taskId, m.url)}
                onViewResults={(taskId) => onSelectRun?.(taskId, m.url)}
              />
              <button
                onClick={() => onDelete(m.id)}
                title="Delete monitor"
                className="rounded-xl p-2 text-zinc-300 transition-all duration-200 hover:bg-rose-50 hover:text-rose-500 hover:scale-110 active:scale-95"
              >
                <Trash2 size={16} />
              </button>
            </div>

            <RunHistoryPanel
              monitorId={m.id}
              url={m.url}
            />
          </div>
        );
      })}
    </div>
  );
}
