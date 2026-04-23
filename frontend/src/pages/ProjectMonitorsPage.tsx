import { useEffect, useState } from "react";
import { Eye, Loader2 } from "lucide-react";
import { useParams } from "react-router";
import { useMonitors, useDeleteMonitor } from "../hooks/useMonitors";
import { useProjectSummary } from "../hooks/useProject";
import { useTaskPoll } from "../hooks/useTasks";
import { MonitorList } from "../components/monitors/MonitorList";
import { AnalysisDialog } from "../components/monitors/AnalysisDialog";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { EmptyState } from "../components/common/EmptyState";
import { useI18n } from "../i18n";

export function ProjectMonitorsPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data, isLoading: projectLoading, error } = useProjectSummary(projectId);
  const { data: allMonitors, isLoading: monitorsLoading } = useMonitors();
  const deleteMonitor = useDeleteMonitor();
  const { t } = useI18n();
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedTaskUrl, setSelectedTaskUrl] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const { data: taskData } = useTaskPoll(selectedTaskId);
  const taskDone = taskData?.status === "completed" || taskData?.status === "failed";

  const monitors = allMonitors?.filter((m) => m.project_id === projectId) ?? [];

  useEffect(() => {
    if (!taskDone || !selectedTaskId || dialogOpen) return;
    const timeoutId = window.setTimeout(() => {
      setSelectedTaskId(null);
      setSelectedTaskUrl(null);
    }, 3000);
    return () => window.clearTimeout(timeoutId);
  }, [dialogOpen, selectedTaskId, taskDone]);

  if (projectLoading || monitorsLoading) return <LoadingSpinner />;
  if (error || !data) return <ErrorAlert message={t("common.projectNotFound")} />;

  const handleTaskCreated = (taskId: string, url: string) => {
    setSelectedTaskId(taskId);
    setSelectedTaskUrl(url);
    setDialogOpen(true);
  };

  return (
    <div>
      <ProjectHeader project={data.project} isPaused={data.is_paused} />
      <ProjectTabs projectId={projectId} />

      <div className="space-y-4">
        {selectedTaskId && selectedTaskUrl && !dialogOpen && !taskDone && (
          <button
            onClick={() => setDialogOpen(true)}
            className="flex w-full items-center gap-3 rounded-xl bg-indigo-50 px-4 py-3 text-sm text-indigo-700 ring-1 ring-inset ring-indigo-200 transition-colors hover:bg-indigo-100"
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
        {monitors.length === 0 ? (
          <EmptyState
            title={t("monitors.noMonitors")}
            description={t("monitors.noMonitorsDesc")}
          />
        ) : (
          <MonitorList
            monitors={monitors}
            onDelete={(id) => deleteMonitor.mutate(id)}
            onTaskCreated={handleTaskCreated}
          />
        )}
      </div>

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
