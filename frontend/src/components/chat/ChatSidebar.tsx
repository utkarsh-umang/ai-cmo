import { Plus, Trash2, MessageSquare, X } from "lucide-react";
import type { ChatSessionSummary } from "../../types";
import { useI18n } from "../../i18n";

function SessionGroups({
  sessions,
  activeSessionId,
  onSelect,
  onDelete,
}: {
  sessions: ChatSessionSummary[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const { t } = useI18n();

  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86400000).toDateString();

  const groups: { label: string; items: ChatSessionSummary[] }[] = [];
  const todayItems: ChatSessionSummary[] = [];
  const yesterdayItems: ChatSessionSummary[] = [];
  const olderItems: ChatSessionSummary[] = [];

  for (const s of sessions) {
    const d = new Date(s.updated_at + "Z").toDateString();
    if (d === today) todayItems.push(s);
    else if (d === yesterday) yesterdayItems.push(s);
    else olderItems.push(s);
  }

  if (todayItems.length) groups.push({ label: t("chat.today"), items: todayItems });
  if (yesterdayItems.length) groups.push({ label: t("chat.yesterday"), items: yesterdayItems });
  if (olderItems.length) groups.push({ label: t("chat.older"), items: olderItems });

  return (
    <div className="flex-1 overflow-y-auto p-2">
      {groups.length === 0 && (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-50">
            <MessageSquare size={18} className="text-slate-300" />
          </div>
          <p className="text-xs text-slate-400">{t("chat.noHistory")}</p>
        </div>
      )}
      {groups.map((group) => (
        <div key={group.label} className="mb-3">
          <p className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
            {group.label}
          </p>
          {group.items.map((s) => (
            <div
              key={s.id}
              className={`group flex items-center rounded-xl px-2.5 py-2 text-sm transition-all ${
                s.id === activeSessionId
                  ? "bg-indigo-50 font-medium text-indigo-700"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <button
                onClick={() => onSelect(s.id)}
                className="min-w-0 flex-1 text-left"
              >
                <p className="truncate">{s.title || t("chat.newChat")}</p>
                {s.project_name ? (
                  <p className="mt-0.5 truncate text-[10px] font-medium uppercase tracking-[0.16em] text-slate-400">
                    {s.project_name}
                  </p>
                ) : null}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(s.id);
                }}
                className="ml-1 shrink-0 rounded-lg p-1 opacity-0 transition-all hover:bg-rose-50 hover:text-rose-500 group-hover:opacity-100"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

export function ChatSidebar({
  sessions,
  activeSessionId,
  onSelect,
  onDelete,
  onNewChat,
  mobileOpen = false,
  onCloseMobile,
}: {
  sessions: ChatSessionSummary[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onNewChat: () => void;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}) {
  const { t } = useI18n();

  return (
    <>
      <div className="hidden w-64 shrink-0 flex-col rounded-2xl border border-slate-200 bg-white lg:flex">
        <div className="border-b border-slate-100 p-3">
          <button
            onClick={onNewChat}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-3 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-indigo-700 hover:shadow-md"
          >
            <Plus size={16} />
            {t("chat.newChat")}
          </button>
        </div>
        <SessionGroups
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelect={onSelect}
          onDelete={onDelete}
        />
      </div>

      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label={t("common.cancel")}
            onClick={onCloseMobile}
            className="absolute inset-0 bg-slate-950/35"
          />
          <div className="absolute inset-y-0 left-0 flex w-[min(22rem,calc(100vw-1.5rem))] flex-col border-r border-slate-200 bg-white shadow-2xl">
            <div className="flex items-center gap-2 border-b border-slate-100 p-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
                <MessageSquare size={16} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-slate-900">{t("chat.history")}</p>
                {sessions.length === 0 ? (
                  <p className="truncate text-xs text-slate-400">{t("chat.noHistory")}</p>
                ) : null}
              </div>
              <button
                type="button"
                onClick={onCloseMobile}
                className="flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
              >
                <X size={16} />
              </button>
            </div>
            <div className="border-b border-slate-100 p-3">
              <button
                onClick={() => {
                  onNewChat();
                  onCloseMobile?.();
                }}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-3 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-indigo-700 hover:shadow-md"
              >
                <Plus size={16} />
                {t("chat.newChat")}
              </button>
            </div>
            <SessionGroups
              sessions={sessions}
              activeSessionId={activeSessionId}
              onSelect={(id) => {
                onSelect(id);
                onCloseMobile?.();
              }}
              onDelete={onDelete}
            />
          </div>
        </div>
      ) : null}
    </>
  );
}
