import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useProjects } from "../hooks/useProjects";
import { useCreateMonitor } from "../hooks/useMonitors";
import { useTaskPoll } from "../hooks/useTasks";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { AnimatedPage } from "../components/common/AnimatedPage";
import { SkeletonCard } from "../components/common/SkeletonCard";
import { ProjectCard } from "../components/dashboard/ProjectCard";
import { WelcomeHero } from "../components/dashboard/WelcomeHero";
import { GlobalOverview } from "../components/dashboard/GlobalOverview";
import { InsightBanner } from "../components/dashboard/InsightBanner";
import { MonitorForm } from "../components/monitors/MonitorForm";
import { AnalysisDialog } from "../components/monitors/AnalysisDialog";
import { useI18n } from "../i18n";
import { Eye, Loader2 } from "lucide-react";

const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.97 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      delay: i * 0.06,
      duration: 0.45,
      ease: [0.25, 0.46, 0.45, 0.94] as const,
    },
  }),
};

export function DashboardPage() {
  const { data: projects, isLoading, error } = useProjects();
  const createMonitor = useCreateMonitor();
  const { t, locale } = useI18n();
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedTaskUrl, setSelectedTaskUrl] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: taskData } = useTaskPoll(selectedTaskId);
  const taskDone = taskData?.status === "completed" || taskData?.status === "failed";

  useEffect(() => {
    if (!taskDone || !selectedTaskId || dialogOpen) return;
    const timeoutId = window.setTimeout(() => {
      setSelectedTaskId(null);
      setSelectedTaskUrl(null);
    }, 3000);
    return () => window.clearTimeout(timeoutId);
  }, [dialogOpen, selectedTaskId, taskDone]);

  if (isLoading) {
    return (
      <AnimatedPage>
        <div className="mb-10">
          <div className="h-8 w-48 rounded-lg bg-slate-100 animate-pulse mb-2" />
          <div className="h-4 w-72 rounded bg-slate-50 animate-pulse" />
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

  return (
    <AnimatedPage>
      {projects?.length ? (
        <>
          <div className="mb-6">
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">{t("dashboard.title")}</h1>
            <p className="text-[15px] text-slate-500 mt-1.5">{t("dashboard.subtitle")}</p>
          </div>

          <GlobalOverview />
          <InsightBanner />

          <div className="mb-8">
            <MonitorForm
              onSubmit={async (data) => {
                const result = await createMonitor.mutateAsync({ ...data, locale });
                if (result.task_id) {
                  handleTaskCreated(result.task_id, data.url);
                }
              }}
              isLoading={createMonitor.isPending}
            />
            {selectedTaskId && selectedTaskUrl && !dialogOpen && !taskDone && (
              <button
                onClick={() => setDialogOpen(true)}
                className="mt-3 flex w-full items-center gap-3 rounded-xl bg-indigo-50 px-4 py-3 text-sm text-indigo-700 ring-1 ring-inset ring-indigo-200 transition-colors hover:bg-indigo-100"
              >
                <Loader2 size={16} className="animate-spin" />
                <span className="flex-1 truncate text-left">
                  {t("monitors.aiAnalyzing")}: {selectedTaskUrl}
                </span>
                <span className="flex items-center gap-1 text-xs font-medium">
                  <Eye size={14} />
                  {t("monitors.viewDetails")}
                </span>
              </button>
            )}
          </div>
        </>
      ) : (
        <div className="mb-8">
          <WelcomeHero onTaskCreated={handleTaskCreated} />
        </div>
      )}

      {projects?.length ? (
        <div id="project-grid" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p, i) => (
            <motion.div
              key={p.id}
              custom={i}
              variants={cardVariants}
              initial="hidden"
              animate="visible"
              whileHover={{
                y: -4,
                transition: { duration: 0.2, ease: "easeOut" },
              }}
            >
              <ProjectCard project={p} />
            </motion.div>
          ))}
        </div>
      ) : null}

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
