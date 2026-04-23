import { useEffect, useState } from "react";
import { ArrowRight, CheckCircle2, Globe, KeyRound, Search, Sparkles, Users } from "lucide-react";
import { getEffectiveKeyStatus } from "../../api/userKeys";
import { useI18n } from "../../i18n";
import { useCreateMonitor } from "../../hooks/useMonitors";
import { useSettings } from "../../hooks/useSettings";
import { SettingsDialog } from "../settings/SettingsDialog";

const AGENT_FEATURES = [
  {
    icon: Search,
    labelKey: "welcome.featureSeo" as const,
    descKey: "welcome.featureSeoDesc" as const,
    color: "bg-sky-50 text-sky-600",
  },
  {
    icon: Globe,
    labelKey: "welcome.featureGeo" as const,
    descKey: "welcome.featureGeoDesc" as const,
    color: "bg-emerald-50 text-emerald-600",
  },
  {
    icon: Users,
    labelKey: "welcome.featureCommunity" as const,
    descKey: "welcome.featureCommunityDesc" as const,
    color: "bg-amber-50 text-amber-600",
  },
];

export function WelcomeHero({
  onTaskCreated,
}: {
  onTaskCreated?: (taskId: string, url: string) => void;
}) {
  const { t, locale } = useI18n();
  const [url, setUrl] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [keyRefresh, setKeyRefresh] = useState(0);
  const createMonitor = useCreateMonitor();
  const settingsQuery = useSettings();
  const keyStatus = getEffectiveKeyStatus(settingsQuery.data);
  const keysReady = keyStatus.effective.llm;
  const serverModel = settingsQuery.data?.model?.trim() || "gpt-5.4-mini";
  void keyRefresh;

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    const normalizedUrl = url.trim();
    const result = await createMonitor.mutateAsync({ url: normalizedUrl, cron_expr: "0 9 * * *", locale });
    if (result.task_id && onTaskCreated) {
      onTaskCreated(result.task_id, normalizedUrl);
    }
    setUrl("");
  };

  return (
    <>
      <div className="animate-in fade-in slide-in-from-bottom-6 duration-700 ease-out">
        <div className="relative overflow-hidden rounded-3xl border border-slate-200/70 bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.14),_transparent_42%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)] sm:p-10">
          <div className="absolute -right-12 -top-12 h-48 w-48 rounded-full bg-indigo-100/40 blur-3xl" />
          <div className="absolute -left-8 bottom-0 h-32 w-32 rounded-full bg-sky-100/30 blur-2xl" />

          <div className="relative">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white">
              <Sparkles size={16} />
              {t("landing.heroEyebrow")}
            </div>

            <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
              {t("welcome.title")}
            </h1>
            <p className="mt-4 max-w-3xl text-lg leading-relaxed text-slate-600">
              {t("welcome.subtitle")}
            </p>

            <form onSubmit={handleSubmit} className="mt-8 space-y-4">
              <div className="flex flex-col gap-3 lg:flex-row">
                <input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  type="url"
                  required
                  placeholder={t("monitorForm.urlPlaceholder")}
                  className="flex-1 rounded-2xl border border-slate-200 bg-white px-5 py-3.5 text-base shadow-sm transition-shadow placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                />
                <button
                  type="submit"
                  disabled={createMonitor.isPending || !url.trim()}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-900 px-6 py-3.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-slate-800 hover:shadow-md disabled:opacity-50"
                >
                  {createMonitor.isPending ? t("monitorForm.analyzing") : t("monitorForm.startMonitoring")}
                  <ArrowRight size={16} />
                </button>
              </div>

              <div
                className={`rounded-2xl border px-4 py-3 ${
                  keysReady ? "border-emerald-200 bg-emerald-50/70" : "border-amber-200 bg-amber-50/70"
                }`}
              >
                <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                  <div className="flex items-start gap-3">
                    {keysReady ? (
                      <CheckCircle2 size={18} className="mt-0.5 text-emerald-600" />
                    ) : (
                      <KeyRound size={18} className="mt-0.5 text-amber-600" />
                    )}
                    <div>
                      <p className={`text-sm font-semibold ${keysReady ? "text-emerald-900" : "text-amber-900"}`}>
                        {t(keysReady ? "onboarding.keyReadyTitle" : "onboarding.keyNeededTitle")}
                      </p>
                      <p className={`mt-1 text-sm leading-6 ${keysReady ? "text-emerald-800/80" : "text-amber-800/80"}`}>
                        {t(keysReady ? "onboarding.keyReadyDesc" : "onboarding.keyNeededDesc")}
                      </p>
                      <p className={`mt-2 text-xs ${keysReady ? "text-emerald-800/70" : "text-amber-800/70"}`}>
                        {t("onboarding.privacyHint")}
                      </p>
                      <p className={`mt-1 text-xs ${keysReady ? "text-emerald-800/70" : "text-amber-800/70"}`}>
                        {t("onboarding.serverDefaultModel", { model: serverModel })}
                      </p>
                      <div className="mt-3 grid gap-3 sm:grid-cols-2">
                        <div className="rounded-2xl bg-white/80 px-3 py-3">
                          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                            {t(keysReady ? "onboarding.fullModeTitle" : "onboarding.limitedModeWorksTitle")}
                          </p>
                          <p className="mt-2 text-sm leading-6 text-slate-700">
                            {t(keysReady ? "onboarding.fullModeDesc" : "onboarding.limitedModeWorks")}
                          </p>
                        </div>
                        <div className="rounded-2xl bg-white/80 px-3 py-3">
                          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                            {t(keysReady ? "onboarding.privacyTitle" : "onboarding.limitedModeNeedsKeyTitle")}
                          </p>
                          <p className="mt-2 text-sm leading-6 text-slate-700">
                            {t(keysReady ? "onboarding.privacyDesc" : "onboarding.limitedModeNeedsKey")}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {!keysReady ? (
                    <button
                      type="button"
                      onClick={() => setShowSettings(true)}
                      className="inline-flex items-center gap-2 rounded-full border border-amber-300 bg-white px-4 py-2 text-sm font-semibold text-amber-900 transition-colors hover:border-amber-400 hover:bg-amber-100"
                    >
                      <KeyRound size={14} />
                      {t("onboarding.configureKeys")}
                    </button>
                  ) : null}
                </div>
              </div>
            </form>
          </div>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {AGENT_FEATURES.map((feature) => (
            <article
              key={feature.labelKey}
              className="rounded-2xl border border-slate-200/70 bg-white p-5 shadow-sm"
            >
              <div className={`mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl ${feature.color}`}>
                <feature.icon size={20} />
              </div>
              <h3 className="text-sm font-semibold text-slate-900">{t(feature.labelKey)}</h3>
              <p className="mt-1 text-xs leading-relaxed text-slate-500">{t(feature.descKey)}</p>
            </article>
          ))}
        </div>
      </div>

      {showSettings ? <SettingsDialog onClose={() => setShowSettings(false)} /> : null}
    </>
  );
}
