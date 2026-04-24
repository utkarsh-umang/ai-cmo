import { Bot, MessageSquare, ExternalLink } from "lucide-react";
import type { ApprovalRecord } from "../../types";
import { useI18n } from "../../i18n";

interface ApprovalGridItemProps {
  approval: ApprovalRecord;
  onClick: () => void;
}

function getTitle(approval: ApprovalRecord): string {
  const preview = approval.preview;
  if (typeof preview.title === "string" && preview.title.trim()) {
    return preview.title;
  }
  if (approval.title.trim()) {
    return approval.title;
  }
  return approval.approval_type.replace(/_/g, " ");
}

function getSnippet(approval: ApprovalRecord): string {
  const preview = approval.preview;
  const content = (typeof preview.text === "string" && preview.text.trim()) 
    ? preview.text 
    : (typeof preview.body === "string" && preview.body.trim()) 
    ? preview.body 
    : approval.content;
  
  return content.length > 120 ? content.substring(0, 120) + "..." : content;
}

export function ApprovalGridItem({ approval, onClick }: ApprovalGridItemProps) {
  const { t } = useI18n();

  return (
    <button
      onClick={onClick}
      className="group relative flex flex-col items-start overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white p-5 text-left shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-brand-300 hover:shadow-xl hover:shadow-brand-500/5"
    >
      <div className="mb-4 flex w-full items-start justify-between gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-bg-cream text-accent-dark transition-all duration-300 group-hover:bg-brand-500 group-hover:text-white">
          <MessageSquare size={18} />
        </div>
        <div className="flex flex-wrap justify-end gap-1.5">
          {approval.source_insight_id && (
            <span className="flex items-center gap-1 rounded-full border border-violet-100 bg-violet-50 px-2 py-0.5 text-[10px] font-bold text-violet-600">
              <Bot size={10} />
              {t("approvals.autopilot")}
            </span>
          )}
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold capitalize text-slate-500">
            {approval.channel.replace(/_/g, " ")}
          </span>
        </div>
      </div>

      <div className="mb-3">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-accent-dark/30">
          {approval.agent_name || "AI-CMO Agent"}
        </p>
        <h3 className="mt-1 line-clamp-1 font-display text-base font-bold text-foreground group-hover:text-brand-600 transition-colors">
          {getTitle(approval)}
        </h3>
      </div>

      <p className="mb-4 flex-1 text-sm leading-relaxed text-accent-dark/60">
        {getSnippet(approval)}
      </p>

      <div className="flex w-full items-center justify-between border-t border-slate-50 pt-3">
        <span className="text-[10px] font-black uppercase tracking-widest text-brand-500 opacity-0 group-hover:opacity-100 transition-opacity">
          Review Detail →
        </span>
        {approval.target_label && (
          <span className="truncate text-[10px] font-bold text-accent-dark/40">
            {approval.target_label}
          </span>
        )}
      </div>
    </button>
  );
}
