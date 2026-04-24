import { useEffect, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useLocation } from "react-router";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { useProjects } from "../../hooks/useProjects";

export function AppShell({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { data: projects, isLoading } = useProjects();
  const location = useLocation();
  const hasProjects = projects && projects.length > 0;
  const isChatRoute = location.pathname === "/chat";

  useEffect(() => {
    const robotsMeta = document.querySelector('meta[name="robots"]');
    const previousRobots = robotsMeta?.getAttribute("content") ?? null;
    const previousTitle = document.title;

    if (robotsMeta) {
      robotsMeta.setAttribute("content", "noindex,nofollow,noarchive,nosnippet");
    }
    document.title = "AI-CMO Workspace";

    return () => {
      if (robotsMeta && previousRobots) {
        robotsMeta.setAttribute("content", previousRobots);
      }
      document.title = previousTitle;
    };
  }, []);

  // While loading projects, we show a clean shell to avoid flashing
  if (isLoading) return <div className="h-screen bg-bg-cream" />;

  return (
    <div className={`flex h-screen overflow-hidden ${hasProjects ? "bg-bg-cream" : "bg-bg-coffee"} text-foreground transition-colors duration-700 font-sans relative`}>
      {hasProjects && (
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-brand-500/5 blur-[120px]" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-accent-dark/5 blur-[120px]" />
        </div>
      )}

      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            key="overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-bg-coffee/20 backdrop-blur-sm lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>

      {hasProjects && <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />}
      
      <div className="flex flex-1 flex-col overflow-hidden relative">
        {hasProjects && <TopBar onMenuClick={() => setSidebarOpen(true)} />}
        <main className={`flex-1 overflow-y-auto ${hasProjects && !isChatRoute ? "px-4 lg:px-12 pb-24" : ""}`}>
          <div className={`mx-auto flex min-h-full w-full flex-col ${hasProjects && !isChatRoute ? "max-w-7xl pt-8" : ""}`}>
            <div className="flex-1">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
