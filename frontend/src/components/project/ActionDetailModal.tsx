import { motion, AnimatePresence } from "framer-motion";
import { X, Info, Bot, MessageSquare } from "lucide-react";
import { useI18n } from "../../i18n";

interface ActionDetailModalProps {
  item: {
    title: string;
    summary: string;
    type: string;
    severity: string;
  } | null;
  isOpen: boolean;
  onClose: () => void;
  onDiscuss: () => void;
}

export function ActionDetailModal({
  item,
  isOpen,
  onClose,
  onDiscuss,
}: ActionDetailModalProps) {
  const { t } = useI18n();

  if (!item) return null;

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
            <div className="relative w-full max-w-lg overflow-hidden rounded-[2rem] bg-white shadow-2xl pointer-events-auto flex flex-col">
              {/* Header */}
              <div className="border-b border-slate-100 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-50 text-sky-600">
                      <Info size={20} />
                    </div>
                    <div>
                      <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
                        {item.type} Details
                      </span>
                      <h2 className="text-xl font-bold text-slate-900 leading-tight">
                        {item.title}
                      </h2>
                    </div>
                  </div>
                  <button
                    onClick={onClose}
                    className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-50 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
                  >
                    <X size={18} />
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="p-6 md:p-8">
                <div className="rounded-2xl bg-slate-50 p-6">
                  <p className="text-sm leading-relaxed text-slate-700">
                    {item.summary}
                  </p>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-end gap-3 border-t border-slate-100 bg-slate-50/50 p-6">
                <button
                  onClick={onClose}
                  className="rounded-xl px-4 py-2 text-sm font-semibold text-slate-500 hover:bg-slate-100 transition-colors"
                >
                  {t("common.close")}
                </button>
                <button
                  onClick={onDiscuss}
                  className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-800 active:scale-95"
                >
                  <MessageSquare size={16} />
                  {t("actionFeed.discuss")}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
