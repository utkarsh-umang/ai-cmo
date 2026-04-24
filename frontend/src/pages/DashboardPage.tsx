import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router";
import { useProjects } from "../hooks/useProjects";
import { useCreateMonitor } from "../hooks/useMonitors";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { AnimatedPage } from "../components/common/AnimatedPage";
import { SkeletonCard } from "../components/common/SkeletonCard";
import { ProjectCard } from "../components/dashboard/ProjectCard";
import { AnalysisDialog } from "../components/monitors/AnalysisDialog";
import { useI18n } from "../i18n";
import { ArrowRight, Loader2, Users } from "lucide-react";
import { GlobalOverview } from "../components/dashboard/GlobalOverview";
import { InsightBanner } from "../components/dashboard/InsightBanner";
import { ChatInput } from "../components/chat/ChatInput";

export function DashboardPage() {
  const { data: projects, isLoading, error } = useProjects();
  const createMonitor = useCreateMonitor();
  const navigate = useNavigate();
  const { t, locale } = useI18n();
  const [url, setUrl] = useState("");
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedTaskUrl, setSelectedTaskUrl] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

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

  const handleSetupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    const result = await createMonitor.mutateAsync({ url: url.trim(), cron_expr: "0 9 * * *", locale });
    if (result.task_id) {
      handleTaskCreated(result.task_id, url.trim());
    }
  };

  const handleChatStart = (message: string) => {
    navigate(`/chat?q=${encodeURIComponent(message)}`);
  };

  // If there are projects, show the dashboard
  if (projects && projects.length > 0) {
    return (
      <AnimatedPage>
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">{t("dashboard.title")}</h1>
          <p className="text-[15px] text-slate-500 mt-1.5">{t("dashboard.subtitle")}</p>
        </div>

        <GlobalOverview />
        <InsightBanner />

        <div className="mb-10 max-w-3xl">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3 ml-1">
            Command Center
          </h2>
          <ChatInput onSend={handleChatStart} disabled={false} />
        </div>

        <div id="project-grid" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#111111] font-sans selection:bg-indigo-500/30">
      {/* Decorative blobs for a premium feel */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-500/10 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-blue-500/10 blur-[120px]" />
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-10 w-full max-w-2xl px-6 text-center"
      >
        {/* Pixel Art Octopus Logo */}
        <div className="mb-12 flex justify-center">
          <div className="relative group">
            <div className="absolute inset-0 bg-white/20 blur-xl rounded-full scale-150 group-hover:scale-175 transition-transform duration-500 opacity-50" />
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" className="relative text-white">
              <path d="M12 24H16V20H20V16H44V20H48V24H52V44H48V48H44V52H36V48H32V44H28V48H24V52H16V48H12V44H12 24Z" fill="white" />
              <path d="M20 28H24V32H20V28ZM40 28H44V32H40V28Z" fill="#111111" />
              <path d="M24 36H40V40H24V36Z" fill="#111111" />
            </svg>
          </div>
        </div>

        <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">
          Meet Okara, the AI CMO
        </h1>
        <p className="text-lg md:text-xl text-slate-400 mb-12 max-w-md mx-auto">
          The only AI CMO you need for growth and marketing.
        </p>

        <form onSubmit={handleSetupSubmit} className="relative group max-w-xl mx-auto">
          <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-blue-500 rounded-[28px] blur opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
          <div className="relative flex items-center p-2 rounded-[24px] bg-[#1a1a1a] border border-white/10 backdrop-blur-xl">
            <input
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="yourbusiness.com"
              className="flex-1 bg-transparent border-none focus:ring-0 text-white placeholder:text-slate-500 px-6 py-4 text-lg"
            />
            <button
              type="submit"
              disabled={createMonitor.isPending || !url.trim()}
              className="flex items-center gap-2 bg-[#d1d5db]/10 hover:bg-[#d1d5db]/20 text-white px-6 py-4 rounded-[18px] font-medium transition-all duration-200 border border-white/5 disabled:opacity-50"
            >
              {createMonitor.isPending ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <>
                  Get Started
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </div>
        </form>

        <div className="mt-12 flex items-center justify-center gap-2 text-slate-500 text-sm font-medium">
          <Users size={16} />
          <span>100K+ users growing with Okara</span>
        </div>
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
