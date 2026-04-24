import { useState, useRef } from "react";
import { Send, Sparkles } from "lucide-react";
import { useI18n } from "../../i18n";

export function ChatInput({
  onSend,
  disabled,
  onOpenTools,
}: {
  onSend: (content: string) => void;
  disabled: boolean;
  onOpenTools?: () => void;
}) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { t } = useI18n();

  const handleSubmit = () => {
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  return (
    <div className="group relative flex flex-col bg-white rounded-[2rem] border border-brand-100 shadow-sm transition-all focus-within:shadow-xl focus-within:shadow-brand-500/5 focus-within:border-brand-300 p-2">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        disabled={disabled}
        placeholder={t("chat.placeholder")}
        rows={3}
        className="min-h-[120px] w-full resize-none bg-transparent px-6 py-4 text-[16px] text-foreground placeholder:text-accent-dark/30 focus:outline-none disabled:opacity-50 font-sans leading-relaxed"
      />
      <div className="flex items-center justify-between px-2 pb-2 pt-2 border-t border-brand-50">
        <div className="flex items-center gap-2">
          {onOpenTools && (
            <button
              type="button"
              onClick={onOpenTools}
              className="flex items-center gap-2 rounded-xl px-4 py-2 text-[13px] font-bold text-accent-dark/60 hover:bg-brand-50 hover:text-brand-600 transition-all active:scale-95"
            >
              <Sparkles size={16} />
              <span>{t("agentGrid.title")}</span>
            </button>
          )}
        </div>
        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="flex h-11 w-11 items-center justify-center rounded-2xl bg-foreground text-white shadow-lg transition-all hover:scale-105 active:scale-95 disabled:opacity-20 disabled:hover:scale-100"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
