import { useState } from "react";
import { Link, useLocation } from "react-router";
import {
  LayoutDashboard,
  MessageSquare,
  CheckSquare,
  FolderOpen,
  Settings,
  X,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { listProjects } from "../../api/projects";
import { useSettings } from "../../hooks/useSettings";
import { getEffectiveKeyStatus } from "../../api/userKeys";
import { useI18n } from "../../i18n";
import type { TranslationKey } from "../../i18n";
import { SettingsDialog } from "../settings/SettingsDialog";

const NAV: { to: string; labelKey: TranslationKey; icon: typeof LayoutDashboard }[] = [
  { to: "/workspace", labelKey: "nav.dashboard", icon: LayoutDashboard },
  { to: "/approvals", labelKey: "nav.approvals", icon: CheckSquare },
  { to: "/chat", labelKey: "nav.aiChat", icon: MessageSquare },
];

export function Sidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { pathname } = useLocation();
  const { t } = useI18n();
  const [showSettings, setShowSettings] = useState(false);
  const settingsQuery = useSettings();
  const keyStatus = getEffectiveKeyStatus(settingsQuery.data);
  const needsSetup = !keyStatus.effective.llm;
  const { data: projects } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });

  return (
    <>
      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-64 transform flex-col bg-white border-r border-brand-100/50 transition-transform lg:static lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-16 items-center justify-between px-6 mt-2">
          <Link to="/workspace" className="font-display text-xl font-bold text-foreground tracking-tight" onClick={onClose}>
            AI-CMO
          </Link>
          <button className="text-accent-dark/40 hover:text-foreground transition-colors lg:hidden" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 space-y-1.5 p-4 mt-2">
          {NAV.map(({ to, labelKey, icon: Icon }) => {
            const active = to === "/workspace" ? pathname === to : pathname.startsWith(to);
            return (
              <Link
                key={to}
                to={to}
                onClick={onClose}
                className={`flex items-center gap-3 rounded-xl px-4 py-2.5 text-[14px] font-bold transition-all duration-300 ${
                  active
                    ? "bg-brand-50 text-brand-600 shadow-sm shadow-brand-100/50"
                    : "text-accent-dark/70 hover:bg-brand-50/50 hover:text-brand-600 active:scale-[0.98]"
                }`}
              >
                <Icon size={18} className={`transition-colors ${active ? "text-brand-500" : "text-accent-dark/40"}`} />
                {t(labelKey)}
              </Link>
            );
          })}
        </nav>

        {projects && projects.length > 0 && (
          <div className="pt-6 pb-4 px-4">
            <p className="mb-2 px-4 text-[10px] font-black uppercase tracking-[0.2em] text-accent-dark/30">
              {t("nav.projects")}
            </p>
            <div className="space-y-1">
              {projects.map((p) => (
                <Link
                  key={p.id}
                  to={`/projects/${p.id}`}
                  onClick={onClose}
                  className={`group flex items-center gap-2 rounded-xl px-4 py-2 text-[13px] font-bold transition-all duration-300 ${
                    pathname === `/projects/${p.id}`
                      ? "bg-brand-50/80 text-brand-700"
                      : "text-accent-dark/60 hover:bg-brand-50/30 hover:text-brand-600"
                  }`}
                >
                  <FolderOpen size={14} className={`transition-colors ${pathname === `/projects/${p.id}` ? "text-brand-400" : "text-accent-dark/30 group-hover:text-brand-400"}`} />
                  <span className="truncate">{p.brand_name}</span>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Settings button at bottom */}
        <div className="p-4 mb-2">
          <button
            onClick={() => setShowSettings(true)}
            className="group flex w-full items-center gap-3 rounded-xl px-4 py-2.5 text-[14px] font-bold text-accent-dark/70 transition-all duration-300 hover:bg-brand-50/50 hover:text-brand-600 active:scale-[0.98]"
          >
            <span className="relative">
              <Settings size={18} className="transition-transform group-hover:rotate-90 text-accent-dark/40 group-hover:text-brand-500" />
              {needsSetup && (
                <span className="absolute -top-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-brand-500 ring-2 ring-white" />
              )}
            </span>
            {t("settings.title")}
          </button>
        </div>
      </aside>

      {showSettings && <SettingsDialog onClose={() => setShowSettings(false)} />}
    </>
  );
}
