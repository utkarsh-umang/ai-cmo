import { Menu, LogOut } from "lucide-react";
import { useAuth } from "../auth/useAuth";
import { useI18n } from "../../i18n";
import { NotificationBell } from "./NotificationBell";

export function TopBar({ onMenuClick }: { onMenuClick: () => void }) {
  const { isAuthenticated, logout } = useAuth();
  const { t } = useI18n();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between bg-white/40 px-4 backdrop-blur-md transition-colors duration-500 lg:px-8 border-b border-slate-200/40">
      <button className="rounded-lg p-2 text-slate-500 hover:bg-slate-100/50 hover:text-slate-900 transition-all hover:scale-105 active:scale-95 lg:hidden" onClick={onMenuClick}>
        <Menu size={20} />
      </button>
      <div className="flex-1" />
      <div className="flex items-center gap-3 pr-2 lg:pr-4">
        <NotificationBell />
        {isAuthenticated && (
          <button
            onClick={logout}
            className="group flex items-center gap-2 rounded-full border border-rose-100 bg-rose-50/30 px-4 py-2 text-xs font-semibold text-rose-600 shadow-sm transition-all duration-200 hover:border-rose-200 hover:bg-rose-50 hover:text-rose-700 active:scale-[0.98]"
          >
            <LogOut size={14} className="transition-transform group-hover:-translate-x-0.5" />
            {t("common.logout")}
          </button>
        )}
      </div>
    </header>

  );
}
