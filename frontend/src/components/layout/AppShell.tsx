import { useEffect, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Sidebar } from "./Sidebar";
import { SiteFooter } from "./SiteFooter";
import { TopBar } from "./TopBar";

export function AppShell({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

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

  return (
    <div className="flex h-screen overflow-hidden bg-[#fafafa] text-slate-800 transition-colors duration-500 font-sans">
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-50/50 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-blue-50/50 blur-[120px]" />
      </div>

      {/* Mobile overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            key="overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-slate-900/20 backdrop-blur-sm lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </AnimatePresence>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex flex-1 flex-col overflow-hidden relative z-10">
        <TopBar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto px-4 pb-12 lg:px-12">
          <div className="mx-auto flex min-h-full w-full max-w-6xl flex-col pt-6">
            <div className="flex-1">
              {children}
            </div>
            <SiteFooter />
          </div>
        </main>
      </div>
    </div>

  );
}
