import { useI18n } from "../../i18n";
import type { TranslationKey } from "../../i18n";

const PRESETS = [
  { key: "daily",   cron: "0 9 * * *" },
  { key: "weekly",  cron: "0 9 * * 1" },
  { key: "monthly", cron: "0 9 1 * *" },
] as const;

export function ScheduleSelector({
  value,
  onChange,
  compact = false,
}: {
  value: string;
  onChange: (cron: string) => void;
  compact?: boolean;
}) {
  const { t } = useI18n();

  return (
    <div className="space-y-2">
      {!compact && (
        <label className="text-xs font-medium text-zinc-500 uppercase tracking-wider">
          {t("schedule.label")}
        </label>
      )}
      <div className="flex flex-wrap gap-1.5">
        {PRESETS.map((preset) => {
          const isActive = preset.cron === value;
          return (
            <button
              key={preset.key}
              type="button"
              onClick={() => onChange(preset.cron)}
              className={`
                rounded-full px-3 py-1.5 text-xs font-medium
                transition-all duration-200 border
                ${isActive
                  ? "bg-indigo-50 border-indigo-200 text-indigo-700 shadow-sm shadow-indigo-100"
                  : "bg-white border-zinc-200/80 text-zinc-500 hover:border-zinc-300 hover:bg-zinc-50"
                }
              `}
            >
              {t(`schedule.${preset.key}`)}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Convert a cron expression to a human-readable description.
 * Accepts a translation function `t` for locale-aware output.
 */
export function cronToHuman(
  cron: string,
  _locale: string,
  t?: (key: TranslationKey, params?: Record<string, string | number>) => string,
): string {
  const parts = cron.trim().split(/\s+/);
  if (parts.length !== 5) return cron;

  const min = parts[0] ?? "0";
  const hour = parts[1] ?? "*";
  const dayOfMonth = parts[2] ?? "*";
  const dayOfWeek = parts[4] ?? "*";

  const timeStr = `${hour.padStart(2, "0")}:${min.padStart(2, "0")}`;

  // Fallback for callers that don't pass t
  if (!t) {
    if (hour === "*" && min === "0") return "Every hour";
    if (hour === "*" && min === "*") return "Every minute";
    return cron;
  }

  // Every minute / every hour
  if (hour === "*" && min === "0") {
    return t("cron.everyHour");
  }
  if (hour === "*" && min === "*") {
    return t("cron.everyMinute");
  }

  // Every N hours
  const hourMatch = hour.match(/^\*\/(\d+)$/);
  if (hourMatch) {
    return t("cron.everyNHours", { n: hourMatch[1]! });
  }

  // Specific day of week
  if (dayOfWeek !== "*" && dayOfMonth === "*") {
    const dayIdx = parseInt(dayOfWeek);
    const dayKey = `cron.day.${dayIdx}` as TranslationKey;
    const dayName = t(dayKey);
    return t("cron.weeklyAt", { day: dayName, time: timeStr });
  }

  // Specific day of month
  if (dayOfMonth !== "*") {
    const d = parseInt(dayOfMonth);
    return t("cron.monthlyAt", { day: d, time: timeStr });
  }

  // Daily at specific time
  if (hour !== "*" && dayOfWeek === "*" && dayOfMonth === "*") {
    return t("cron.dailyAt", { time: timeStr });
  }

  return cron;
}
