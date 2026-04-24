import { motion } from "framer-motion";
import { useState } from "react";
import { ChevronDown, ChevronRight, Sparkles } from "lucide-react";
import type { ChatMessage } from "../../types";
import type { ChatProjectContext } from "../../api/chatContext";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { AgentModal } from "./AgentModal";
import { useI18n } from "../../i18n";

function ContextBadge({ context }: { context: ChatProjectContext }) {
  const [open, setOpen] = useState(false);
  const { t } = useI18n();
  const { project, scores, keywords } = context;

  return (
    <div className="mb-4 rounded-2xl border border-brand-100 bg-brand-50/30">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left text-xs text-brand-700 hover:bg-brand-50/50 rounded-2xl transition-colors"
      >
        <Sparkles size={14} className="text-brand-500" />
        <span className="font-bold">
          {t("chat.projectContextBadge")}: {project.brand_name}
        </span>
        <span className="flex-1" />
        <span className="text-[11px] font-bold text-accent-dark/40 uppercase tracking-widest">
          SEO {scores.seo != null ? `${Math.round(scores.seo * 100)}%` : "—"}
          {" · "}AI {scores.geo ?? "—"}
        </span>
        {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      </button>
      {open && (
        <div className="border-t border-brand-100 px-4 py-4 text-xs text-accent-dark/70 space-y-3 bg-white/40 rounded-b-2xl">
          {keywords.length > 0 && (
            <div>
              <span className="font-bold text-foreground uppercase tracking-widest text-[10px] block mb-1">{t("chat.contextKeywords")}:</span>
              <p>{keywords.join(", ")}</p>
            </div>
          )}
          {context.competitors.length > 0 && (
            <div>
              <span className="font-bold text-foreground uppercase tracking-widest text-[10px] block mb-1">{t("chat.contextCompetitors")}:</span>
              <p>{context.competitors.map((c) => c.label).join(", ")}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ChatContainer({
  messages,
  isStreaming,
  currentAgent,
  sendMessage,
  hasMessages,
  projectId,
  projectContext,
}: {
  messages: ChatMessage[];
  isStreaming: boolean;
  currentAgent: string;
  sendMessage: (content: string) => void;
  hasMessages: boolean;
  projectId: number | null;
  projectContext?: ChatProjectContext | null;
}) {
  const { t } = useI18n();
  const [modalOpen, setModalOpen] = useState(false);
  const projectName = projectContext?.project.brand_name ?? null;

  return (
    <div className="flex flex-1 min-h-0 flex-col px-4">
      {/* Agent badge */}
      <div className="mb-4 shrink-0 flex items-center justify-between px-2">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-accent-dark/30">
          {t("chat.agent", { name: currentAgent })}
        </p>
        {isStreaming && (
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-brand-500 animate-pulse" />
            <span className="text-[10px] font-bold text-brand-500 uppercase tracking-widest">Thinking</span>
          </div>
        )}
      </div>

      <div className="flex flex-1 min-h-0 flex-col w-full max-w-4xl mx-auto">
        {!hasMessages ? (
          <div className="flex flex-1 flex-col items-center justify-center">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="w-full space-y-12"
            >
              <div className="text-center space-y-4">
                <h2 className="font-display text-4xl md:text-5xl font-bold text-foreground tracking-tight">
                  {t("chat.emptyState")}
                </h2>
                <p className="text-lg text-accent-dark/50 max-w-lg mx-auto leading-relaxed">
                  Talk to your CMO agent or select a specialist to help with specific tasks.
                </p>
              </div>
              
              <div className="w-full">
                <ChatInput 
                  onSend={sendMessage} 
                  disabled={isStreaming} 
                  onOpenTools={() => setModalOpen(true)}
                />
              </div>
            </motion.div>
          </div>
        ) : (
          <div className="flex flex-1 min-h-0 flex-col">
            {projectContext && <ContextBadge context={projectContext} />}
            <MessageList messages={messages} isStreaming={isStreaming} />
            <div className="shrink-0 pt-6">
              <ChatInput 
                onSend={sendMessage} 
                disabled={isStreaming} 
                onOpenTools={() => setModalOpen(true)}
              />
            </div>
          </div>
        )}
      </div>

      <AgentModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSelect={sendMessage}
        projectName={projectName}
      />
    </div>
  );
}
