import { useState } from "react";
import { AlertTriangle, ExternalLink, Settings } from "lucide-react";
import { ApprovalGridItem } from "../components/approval/ApprovalGridItem";
import { ApprovalDetailModal } from "../components/approval/ApprovalDetailModal";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { useApproveApproval, useApprovals, useRejectApproval } from "../hooks/useApprovals";
import { ApiError } from "../api/client";
import { useNavigate } from "react-router";
import { useI18n } from "../i18n";
import type { ApprovalRecord } from "../types";
import { EmptyState } from "../components/common/EmptyState";
import { motion } from "framer-motion";

export function ApprovalsPage() {
  const [selectedApproval, setSelectedApproval] = useState<ApprovalRecord | null>(null);
  const approvalsQuery = useApprovals("pending", 100); // Increased limit for grid
  const approveMutation = useApproveApproval();
  const rejectMutation = useRejectApproval();
  const navigate = useNavigate();
  const { t } = useI18n();

  const [actionError, setActionError] = useState<{
    message: string;
    errorCode?: string;
  } | null>(null);

  const pendingCount = approvalsQuery.data?.length ?? 0;
  const busy = approveMutation.isPending || rejectMutation.isPending;
  const queryError = approvalsQuery.error instanceof Error ? approvalsQuery.error.message : "";

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out h-full flex flex-col">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900">{t("approvals.title")}</h1>
          <p className="text-sm text-zinc-500 mt-1">
            {t("approvals.subtitle")}
          </p>
        </div>
        <div className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 shadow-sm">
          {t("approvals.showingPending").replace("{{count}}", String(pendingCount))}
        </div>
      </div>

      {queryError ? <div className="mb-6"><ErrorAlert message={queryError} /></div> : null}

      {/* Contextual error banner for auto_publish_disabled */}
      {actionError?.errorCode === "auto_publish_disabled" ? (
        <div className="mb-6 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50/80 p-4 shadow-sm">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-amber-900">
              {t("approvals.autoPublishDisabled")}
            </p>
            <p className="mt-1 text-sm text-amber-700">
              {t("approvals.autoPublishHint")}
            </p>
            <button
              onClick={() => navigate("/?tab=settings")}
              className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-xs font-semibold text-amber-800 shadow-sm transition hover:bg-amber-50"
            >
              <Settings className="h-3.5 w-3.5" />
              {t("approvals.goToSettings")}
              <ExternalLink className="h-3 w-3" />
            </button>
          </div>
          <button
            onClick={() => setActionError(null)}
            className="text-amber-400 hover:text-amber-600 text-lg leading-none"
          >
            ×
          </button>
        </div>
      ) : actionError ? (
        <div className="mb-6"><ErrorAlert message={actionError.message} /></div>
      ) : null}

      <div className="flex-1 pb-20">
        {approvalsQuery.isLoading ? (
          <div className="flex h-[420px] items-center justify-center">
            <LoadingSpinner />
          </div>
        ) : pendingCount === 0 ? (
          <EmptyState
            title={t("approvals.empty")}
            description={t("approvals.emptyDesc")}
          />
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-2">
            {approvalsQuery.data?.map((approval, i) => (
              <motion.div
                key={approval.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <ApprovalGridItem
                  approval={approval}
                  onClick={() => setSelectedApproval(approval)}
                />
              </motion.div>
            ))}
          </div>
        )}
      </div>

      <ApprovalDetailModal
        isOpen={!!selectedApproval}
        approval={selectedApproval}
        onClose={() => setSelectedApproval(null)}
        busy={busy}
        onApprove={() => {
          if (selectedApproval) {
            setActionError(null);
            approveMutation.mutate(
              { id: selectedApproval.id },
              {
                onSuccess: () => {
                  setSelectedApproval(null);
                },
                onError: (err) => {
                  if (err instanceof ApiError) {
                    setActionError({
                      message: err.message,
                      errorCode: err.errorCode,
                    });
                  } else {
                    setActionError({ message: String(err) });
                  }
                },
              },
            );
          }
        }}
        onReject={() => {
          if (selectedApproval) {
            setActionError(null);
            rejectMutation.mutate(
              { id: selectedApproval.id },
              {
                onSuccess: () => {
                  setSelectedApproval(null);
                },
                onError: (err) => {
                  setActionError({
                    message: err instanceof Error ? err.message : String(err),
                  });
                },
              },
            );
          }
        }}
      />
    </div>
  );
}
