import { motion, AnimatePresence } from "framer-motion";
import { Bot, Check, Clock3, ExternalLink, MessageSquare, Send, X, Calendar } from "lucide-react";
import { utcDate } from "../../utils/time";
import type { ApprovalRecord } from "../../types";
import { useI18n } from "../../i18n";

interface ApprovalDetailModalProps {
  approval: ApprovalRecord | null;
  isOpen: boolean;
  onClose: () => void;
  onApprove: () => void;
  onReject: () => void;
  busy: boolean;
}

function getPrimaryCopy(approval: ApprovalRecord): string {
  const preview = approval.preview;
  if (typeof preview.text === "string" && preview.text.trim()) return preview.text;
  if (typeof preview.body === "string" && preview.body.trim()) return preview.body;
  return approval.content;
}

function getMetaLabel(approval: ApprovalRecord, t: (key: any) => string): string {
  const preview = approval.preview;
  if (typeof preview.subreddit === "string") return `r/${preview.subreddit}`;
  if (typeof preview.parent_id === "string") return t("approval.replyTo").replace("{{id}}", String(preview.parent_id));
  if (typeof preview.length === "number") return t("approval.chars").replace("{{count}}", String(preview.length));
  return approval.channel;
}

function getTitle(approval: ApprovalRecord): string {
  const preview = approval.preview;
  if (typeof preview.title === "string" && preview.title.trim()) return preview.title;
  if (approval.title.trim()) return approval.title;
  return approval.approval_type.replace(/_/g, " ");
}

function getPreviewString(preview: Record<string, unknown>, key: string): string | null {
  const value = preview[key];
  return typeof value === "string" && value.trim() ? value : null;
}

export function ApprovalDetailModal({
  approval,
  isOpen,
  onClose,
  onApprove,
  onReject,
  busy,
}: ApprovalDetailModalProps) {
  const { t } = useI18n();

  if (!approval) return null;

  const whyThis = getPreviewString(approval.preview, "why_this");
  const whyNow = getPreviewString(approval.preview, "why_now");
  const whyHere = getPreviewString(approval.preview, "why_here");

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-[100] bg-slate-900/40 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed inset-0 z-[101] flex items-center justify-center p-4 pointer-events-none"
          >
            <div className="relative w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-[2.5rem] bg-white shadow-2xl pointer-events-auto flex flex-col">
              {/* Header */}
              <div className="border-b border-slate-100 p-6 md:p-8">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-600 ring-1 ring-brand-200">
                      <MessageSquare size={24} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-xs font-black uppercase tracking-[0.2em] text-accent-dark/30">
                          {approval.agent_name || "AI-CMO Agent"}
                        </p>
                        {approval.source_insight_id && (
                          <span className="flex items-center gap-1 rounded-full border border-violet-100 bg-violet-50 px-2.5 py-0.5 text-[10px] font-bold text-violet-600">
                            <Bot size={12} />
                            {t("approvals.autopilot")}
                          </span>
                        )}
                      </div>
                      <h2 className="mt-1 font-display text-2xl font-bold text-foreground">
                        {getTitle(approval)}
                      </h2>
                    </div>
                  </div>
                  <button
                    onClick={onClose}
                    className="flex h-10 w-10 items-center justify-center rounded-full bg-bg-cream text-accent-dark/40 hover:bg-brand-50 hover:text-brand-600 transition-colors"
                  >
                    <X size={20} />
                  </button>
                </div>

                <div className="flex flex-wrap items-center gap-y-4 gap-x-12 text-[10px]">
                  <div className="flex flex-col gap-1">
                    <span className="font-black uppercase tracking-[0.2em] text-accent-dark/20">{t("approvals.channel")}</span>
                    <span className="font-bold text-foreground capitalize">{approval.channel.replace(/_/g, " ")}</span>
                  </div>
                  {approval.target_label && (
                    <div className="flex flex-col gap-1">
                      <span className="font-black uppercase tracking-[0.2em] text-accent-dark/20">{t("approvals.target")}</span>
                      <span className="font-bold text-foreground">{approval.target_label}</span>
                    </div>
                  )}
                  {approval.target_url && (
                    <div className="flex flex-col gap-1 max-w-[240px]">
                      <span className="font-black uppercase tracking-[0.2em] text-accent-dark/20">{t("approvals.targetUrl")}</span>
                      <a href={approval.target_url} target="_blank" rel="noreferrer" className="font-bold text-brand-600 hover:text-brand-700 truncate flex items-center gap-1">
                        {approval.target_url} <ExternalLink size={10} />
                      </a>
                    </div>
                  )}
                  <div className="flex flex-col gap-1">
                    <span className="font-black uppercase tracking-[0.2em] text-accent-dark/20">{t("approvals.created")}</span>
                    <span className="font-bold text-accent-dark/60 flex items-center gap-1.5"><Calendar size={12} /> {utcDate(approval.created_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6 md:p-8">
                <div className="space-y-6">
                  <div className="rounded-[2rem] border border-slate-200/70 bg-bg-cream/30 p-8">
                    <div className="mb-6 flex items-center justify-between">
                      <span className="text-xs font-black uppercase tracking-[0.2em] text-accent-dark/30">
                        {t("approvals.preview")}
                      </span>
                      <span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-accent-dark/60 border border-slate-100">
                        {getMetaLabel(approval, t)}
                      </span>
                    </div>
                    <p className="whitespace-pre-wrap text-lg leading-relaxed text-slate-800 font-medium">
                      {getPrimaryCopy(approval)}
                    </p>
                  </div>

                  {approval.source_insight_id && (whyThis || whyNow || whyHere) && (
                    <div className="rounded-[2rem] border border-violet-100 bg-violet-50/30 p-8">
                      <h3 className="mb-4 text-xs font-black uppercase tracking-[0.2em] text-violet-500">
                        {t("approvals.aiReasoning")}
                      </h3>
                      <div className="space-y-4">
                        {whyThis && (
                          <div className="flex gap-3">
                            <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400" />
                            <p className="text-sm text-violet-800/80 leading-relaxed">
                              <span className="font-bold text-violet-900">{t("approval.whyThis")}:</span> {whyThis}
                            </p>
                          </div>
                        )}
                        {whyNow && (
                          <div className="flex gap-3">
                            <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400" />
                            <p className="text-sm text-violet-800/80 leading-relaxed">
                              <span className="font-bold text-violet-900">{t("approval.whyNow")}:</span> {whyNow}
                            </p>
                          </div>
                        )}
                        {whyHere && (
                          <div className="flex gap-3">
                            <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400" />
                            <p className="text-sm text-violet-800/80 leading-relaxed">
                              <span className="font-bold text-violet-900">{t("approval.whyHere")}:</span> {whyHere}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-end gap-4 border-t border-slate-100 bg-bg-cream/20 p-6 md:p-8">
                <button
                  onClick={onReject}
                  disabled={busy}
                  className="flex h-14 items-center justify-center gap-2 rounded-2xl border border-rose-200 bg-white px-8 text-sm font-bold text-rose-600 shadow-sm transition-all hover:bg-rose-50 hover:border-rose-300 disabled:opacity-50"
                >
                  <X size={18} />
                  {t("approvals.reject")}
                </button>
                <button
                  onClick={onApprove}
                  disabled={busy}
                  className="flex h-14 items-center justify-center gap-3 rounded-2xl bg-emerald-500 px-10 text-sm font-bold text-white shadow-lg shadow-emerald-500/20 transition-all hover:bg-emerald-600 hover:shadow-emerald-500/40 disabled:opacity-50"
                >
                  <Check size={18} />
                  {t("approvals.approvePublish")}
                  <Send size={18} />
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
