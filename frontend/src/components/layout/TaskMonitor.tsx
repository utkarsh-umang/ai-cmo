import { useAllTasks } from "../../hooks/useTasks";
import { Loader2, Activity } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { AnalysisDialog } from "../monitors/AnalysisDialog";

export function GlobalTaskMonitor() {
  const { data: tasks } = useAllTasks();
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedUrl, setSelectedUrl] = useState<string | null>(null);

  const runningTasks = (tasks ?? []).filter(
    (t) => t.status === "running" || t.status === "pending"
  );

  if (runningTasks.length === 0) return null;

  return (
    <>
      <div className="fixed bottom-6 right-6 z-40 flex flex-col gap-3">
        <AnimatePresence>
          {runningTasks.map((task) => (
            <motion.div
              key={task.task_id}
              initial={{ opacity: 0, x: 50, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 50, scale: 0.9 }}
              className="flex w-72 items-center gap-4 rounded-3xl border border-brand-100 bg-white p-4 shadow-2xl backdrop-blur-xl"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
                <Loader2 size={20} className="animate-spin" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-brand-500">
                  {task.task_kind === "scan" ? "Active Scan" : "Generating Report"}
                </p>
                <p className="mt-0.5 truncate text-sm font-bold text-foreground">
                  {task.summary || "Analyzing project..."}
                </p>
              </div>
              <button
                onClick={() => {
                  setSelectedTaskId(task.task_id);
                  // Try to find URL if possible, or just use a placeholder
                  setSelectedUrl("Scanning...");
                }}
                className="flex h-8 w-8 items-center justify-center rounded-xl bg-bg-cream text-accent-dark hover:bg-brand-500 hover:text-white transition-all"
              >
                <Activity size={14} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {selectedTaskId && (
        <AnalysisDialog
          taskId={selectedTaskId}
          url={selectedUrl ?? ""}
          onClose={() => setSelectedTaskId(null)}
        />
      )}
    </>
  );
}
