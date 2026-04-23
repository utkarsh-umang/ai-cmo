import { useLayoutEffect, useRef } from "react";
import type { ChatMessage } from "../../types";
import { MessageBubble } from "./MessageBubble";
import { StreamingIndicator } from "./StreamingIndicator";
import { useI18n } from "../../i18n";
import { Sparkles } from "lucide-react";

export function MessageList({
  messages,
  isStreaming,
}: {
  messages: ChatMessage[];
  isStreaming: boolean;
}) {
  const listRef = useRef<HTMLDivElement>(null);
  const { t } = useI18n();

  useLayoutEffect(() => {
    const list = listRef.current;
    if (!list) return;
    list.scrollTop = list.scrollHeight;
  }, [messages, isStreaming]);

  return (
    <div
      ref={listRef}
      className="flex-1 space-y-4 overflow-y-auto overscroll-contain rounded-2xl border border-slate-200 bg-white p-4"
    >
      {messages.length === 0 && (
        <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50">
            <Sparkles size={20} className="text-indigo-500" />
          </div>
          <p className="max-w-xs text-sm text-slate-400">{t("chat.emptyState")}</p>
        </div>
      )}
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {isStreaming && <StreamingIndicator />}
    </div>
  );
}
