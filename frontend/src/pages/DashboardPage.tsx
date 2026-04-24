import { useState } from "react";
import { motion } from "framer-motion";
import { useProjects } from "../hooks/useProjects";
import { useCreateMonitor } from "../hooks/useMonitors";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { AnimatedPage } from "../components/common/AnimatedPage";
import { SkeletonCard } from "../components/common/SkeletonCard";
import { ProjectCard } from "../components/dashboard/ProjectCard";
import { AnalysisDialog } from "../components/monitors/AnalysisDialog";
import { useI18n } from "../i18n";
import { ArrowRight, Loader2 } from "lucide-react";
import { GlobalOverview } from "../components/dashboard/GlobalOverview";
import { InsightBanner } from "../components/dashboard/InsightBanner";

export function DashboardPage() {
  const { data: projects, isLoading, error } = useProjects();
  const createMonitor = useCreateMonitor();
  const { t, locale } = useI18n();
  const [url, setUrl] = useState("");
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedTaskUrl, setSelectedTaskUrl] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  if (isLoading) {
    return (
      <AnimatedPage>
        <div className="mb-10">
          <div className="h-8 w-48 rounded-lg bg-brand-50 animate-pulse mb-2" />
          <div className="h-4 w-72 rounded bg-brand-50/50 animate-pulse" />
        </div>
        <SkeletonCard count={3} />
      </AnimatedPage>
    );
  }
  if (error) return <ErrorAlert message={error.message} />;

  const handleTaskCreated = (taskId: string, url: string) => {
    setSelectedTaskId(taskId);
    setSelectedTaskUrl(url);
    setDialogOpen(true);
  };

  const handleSetupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    const result = await createMonitor.mutateAsync({ url: url.trim(), cron_expr: "0 9 * * *", locale });
    if (result.task_id) {
      handleTaskCreated(result.task_id, url.trim());
    }
  };


  // If there are projects, show the dashboard
  if (projects && projects.length > 0) {
    return (
      <AnimatedPage>
        <div className="mb-6">
          <h1 className="text-4xl font-bold tracking-tight text-foreground">{t("dashboard.title")}</h1>
          <p className="text-[15px] text-accent-dark/80 mt-1.5">{t("dashboard.subtitle")}</p>
        </div>

        <GlobalOverview />
        <InsightBanner />


        <div id="project-grid" className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p, i) => (
            <motion.div
              key={p.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <ProjectCard project={p} />
            </motion.div>
          ))}
        </div>

        {selectedTaskId && dialogOpen && (
          <AnalysisDialog
            taskId={selectedTaskId}
            url={selectedTaskUrl ?? ""}
            onClose={() => setDialogOpen(false)}
          />
        )}
      </AnimatedPage>
    );
  }

  // Otherwise, show the setup UI (Landing)
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-bg-coffee font-sans selection:bg-brand-500/30">
      {/* Decorative blobs for a premium feel */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-brand-500/10 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-accent-dark/10 blur-[120px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-10 w-full max-w-3xl px-6 text-center"
      >
        <div className="mb-2 flex justify-center">
          <div className="relative group">
            <div className="absolute inset-0 bg-brand-200/20 blur-2xl rounded-full scale-150 group-hover:scale-175 transition-transform duration-700 opacity-50" />
            <img src="/logo.png" alt="AI-CMO Logo" className="relative w-20 h-20 md:w-24 md:h-24 object-contain" />
          </div>
        </div>

        <h4 className="font-display text-xl md:text-5xl font-bold tracking-tight text-bg-cream mb-10">
          The AI CMO
        </h4>

        <form onSubmit={handleSetupSubmit} className="relative group max-w-2xl mx-auto">
          <div className="absolute -inset-1 bg-gradient-to-r from-brand-500 to-accent-dark rounded-[32px] blur opacity-20 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
          <div className="relative flex items-center p-1.5 rounded-[28px] bg-bg-coffee border border-white/10 backdrop-blur-2xl shadow-2xl">
            <input
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="yourbusiness.com"
              className="flex-1 bg-transparent border-none focus:ring-0 text-white placeholder:text-white/30 px-8 py-5 text-xl font-sans"
            />
            <button
              type="submit"
              disabled={createMonitor.isPending || !url.trim()}
              className="flex items-center gap-3 bg-brand-500 hover:bg-brand-600 text-white px-8 py-5 rounded-[22px] font-bold transition-all duration-300 shadow-lg disabled:opacity-50"
            >
              {createMonitor.isPending ? (
                <Loader2 size={22} className="animate-spin" />
              ) : (
                <>
                  Get Started
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </form>

      </motion.div>

      {selectedTaskId && dialogOpen && (
        <AnalysisDialog
          taskId={selectedTaskId}
          url={selectedTaskUrl ?? ""}
          onClose={() => setDialogOpen(false)}
        />
      )}
    </div>
  );
}
