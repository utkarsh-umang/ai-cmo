import { Menu, LogOut } from "lucide-react";
import { useAuth } from "../auth/useAuth";
import { useI18n } from "../../i18n";
import { NotificationBell } from "./NotificationBell";

export function TopBar({ onMenuClick }: { onMenuClick: () => void }) {
  const { isAuthenticated, logout } = useAuth();
  const { t } = useI18n();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between bg-bg-cream/40 px-4 backdrop-blur-md transition-colors duration-500 lg:px-12 border-b border-brand-100/30">
      <button className="rounded-xl p-2 text-accent-dark/60 hover:bg-brand-50/50 hover:text-brand-600 transition-all hover:scale-105 active:scale-95 lg:hidden" onClick={onMenuClick}>
        <Menu size={20} />
      </button>
      <div className="flex-1" />
      <div className="flex items-center gap-4">
        <NotificationBell />
        {isAuthenticated && (
          <button
            onClick={logout}
            className="group flex items-center gap-2 rounded-xl border border-brand-200/50 bg-white/60 px-5 py-2 text-[13px] font-bold text-brand-700 shadow-sm transition-all duration-300 hover:border-brand-400 hover:bg-brand-500 hover:text-white active:scale-[0.98]"
          >
            <LogOut size={14} className="transition-transform group-hover:-translate-x-1" />
            {t("common.logout")}
          </button>
        )}
      </div>
    </header>
  );
}
