import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles } from "lucide-react";
import { AgentGrid } from "./AgentGrid";
import { useI18n } from "../../i18n";

export function AgentModal({
  isOpen,
  onClose,
  onSelect,
  projectName,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (prompt: string) => void;
  projectName?: string | null;
}) {
  const { t } = useI18n();

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-[60] bg-bg-coffee/40 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 z-[70] w-full max-w-4xl -translate-x-1/2 -translate-y-1/2 px-6"
          >
            <div className="max-h-[80vh] overflow-hidden rounded-[2.5rem] border border-brand-100 bg-white shadow-2xl">
              <div className="sticky top-0 flex items-center justify-between border-b border-brand-50 bg-white/80 px-8 py-5 backdrop-blur-md">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
                    <Sparkles size={20} />
                  </div>
                  <div>
                    <h2 className="font-display text-xl font-bold text-foreground">
                      {t("agentGrid.title")}
                    </h2>
                    <p className="text-xs font-bold text-accent-dark/40 uppercase tracking-widest">
                      {t("agentGrid.subtitle")}
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="rounded-xl p-2 text-accent-dark/40 hover:bg-brand-50 hover:text-brand-600 transition-all"
                >
                  <X size={20} />
                </button>
              </div>
              <div className="overflow-y-auto p-8">
                <AgentGrid
                  onSelect={(prompt) => {
                    onSelect(prompt);
                    onClose();
                  }}
                  projectName={projectName}
                  showTitle={false}
                />
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
