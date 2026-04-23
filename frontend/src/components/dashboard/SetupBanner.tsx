import { useEffect, useState } from "react";
import { getEffectiveKeyStatus } from "../../api/userKeys";
import { useI18n } from "../../i18n";
import { useSettings } from "../../hooks/useSettings";
import { KeyRound, ChevronRight, X, AlertTriangle, CheckCircle2 } from "lucide-react";

/**
 * Show setup guidance only when the app has no effective LLM configuration.
 * Server defaults count as configured; browser keys are optional overrides.
 */
export function SetupBanner({ onOpenSettings }: { onOpenSettings: () => void }) {
  const { t } = useI18n();
  const settingsQuery = useSettings();
  const [dismissed, setDismissed] = useState(false);
  const [keyRefresh, setKeyRefresh] = useState(0);

  useEffect(() => {
    const refresh = () => setKeyRefresh((value) => value + 1);
    const refreshSettings = () => {
      setKeyRefresh((value) => value + 1);
      void settingsQuery.refetch();
    };
    window.addEventListener("opencmo:keys-changed", refresh);
    window.addEventListener("opencmo:settings-changed", refreshSettings);
    return () => {
      window.removeEventListener("opencmo:keys-changed", refresh);
      window.removeEventListener("opencmo:settings-changed", refreshSettings);
    };
  }, [settingsQuery]);

  if (dismissed || settingsQuery.isLoading) return null;

  const keyStatus = getEffectiveKeyStatus(settingsQuery.data);
  const { llm: hasLLM, tavily: hasTavily } = keyStatus.effective;
  void keyRefresh;

  if (hasLLM) return null;

  return (
    <div className="mb-6 animate-in fade-in slide-in-from-top-4 duration-500">
      <div className="relative overflow-hidden rounded-2xl border border-amber-200/60 bg-gradient-to-r from-amber-50 via-orange-50 to-yellow-50 p-5 shadow-sm">
        <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-amber-200/30 blur-2xl" />
        <div className="absolute -left-4 -bottom-4 h-24 w-24 rounded-full bg-orange-200/20 blur-xl" />

        <div className="relative flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-600">
            <AlertTriangle size={22} />
          </div>

          <div className="min-w-0 flex-1">
            <h3 className="text-[15px] font-semibold text-amber-900">
              {t("setup.title")}
            </h3>
            <p className="mt-1 text-sm leading-relaxed text-amber-700/80">
              {t("setup.description")}
            </p>

            <div className="mt-3 flex flex-wrap gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-lg border border-amber-200/50 bg-white/70 px-3 py-1.5 text-xs font-medium text-amber-800">
                <X size={12} className="text-rose-500" />
                {t("setup.llmKey")}
              </span>
              <span
                className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium ${
                  hasTavily
                    ? "border-emerald-200/50 bg-emerald-50 text-emerald-700"
                    : "border-amber-200/50 bg-white/70 text-amber-800"
                }`}
              >
                {hasTavily ? (
                  <CheckCircle2 size={12} />
                ) : (
                  <X size={12} className="text-rose-500" />
                )}
                {hasTavily ? t("setup.tavilyKey") : t("setup.tavilyOptional")}
              </span>
            </div>

            <button
              onClick={onOpenSettings}
              className="mt-4 inline-flex items-center gap-2 rounded-xl bg-amber-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-amber-700 hover:shadow-md active:scale-95"
            >
              <KeyRound size={14} />
              {t("setup.configureNow")}
              <ChevronRight size={14} />
            </button>
          </div>

          <button
            onClick={() => setDismissed(true)}
            className="shrink-0 rounded-lg p-1.5 text-amber-400 transition-colors hover:bg-amber-100 hover:text-amber-600"
            title={t("setup.dismissHint")}
          >
            <X size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
