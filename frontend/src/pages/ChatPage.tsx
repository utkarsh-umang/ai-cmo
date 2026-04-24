import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";
import { useChat } from "../hooks/useChat";
import { useChatContext } from "../hooks/useChatContext";
import { useProjects } from "../hooks/useProjects";
import { ChatContainer } from "../components/chat/ChatContainer";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { useI18n } from "../i18n";
import { ChevronDown, Sparkles } from "lucide-react";

function parseProjectId(value: string | null): number | null {
  if (!value) return null;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

export function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [initialProjectId] = useState<number | null>(() =>
    parseProjectId(searchParams.get("project_id")),
  );
  const chat = useChat(initialProjectId);
  const { data: projects } = useProjects();
  const { data: chatContext } = useChatContext(chat.projectId);
  const { t } = useI18n();


  useEffect(() => {
    if (!chat.sessionReady) return;

    // Handle initial query from dashboard
    const initialQuery = searchParams.get("q");
    if (initialQuery) {
      void chat.sendMessage(initialQuery);
      const nextParams = new URLSearchParams(searchParams);
      nextParams.delete("q");
      setSearchParams(nextParams, { replace: true });
      return;
    }

    const currentProjectId = parseProjectId(searchParams.get("project_id"));
    if (currentProjectId === chat.projectId) return;

    const nextParams = new URLSearchParams(searchParams);
    if (chat.projectId != null) {
      nextParams.set("project_id", String(chat.projectId));
    } else {
      nextParams.delete("project_id");
    }
    setSearchParams(nextParams, { replace: true });
  }, [chat.projectId, chat.sessionReady, searchParams, setSearchParams, chat.sendMessage]);

  if (!chat.sessionReady) return <LoadingSpinner />;

  return (
    <div className="flex flex-1 flex-col items-center font-sans">
      <div className="w-full max-w-4xl flex-1 flex flex-col min-h-0">
        {/* Minimal project switcher */}
        <div className="mb-6 flex justify-center">
          <div className="relative group">
            <select
              value={chat.projectId ?? ""}
              onChange={(event) => {
                void chat.selectProject(parseProjectId(event.target.value));
              }}
              className="appearance-none rounded-2xl border border-brand-100 bg-white pl-10 pr-12 py-3 text-sm font-bold text-foreground shadow-sm transition-all hover:border-brand-300 focus:ring-4 focus:ring-brand-500/10 outline-none"
            >
              <option value="">{t("chat.allProjects")}</option>
              {(projects ?? []).map((project) => (
                <option key={project.id} value={project.id}>
                  {project.brand_name}
                </option>
              ))}
            </select>
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-brand-500 pointer-events-none">
              <Sparkles size={16} />
            </div>
            <div className="absolute right-4 top-1/2 -translate-y-1/2 text-accent-dark/30 pointer-events-none group-hover:text-accent-dark/60 transition-colors">
              <ChevronDown size={16} />
            </div>
          </div>
        </div>

        <ChatContainer
          messages={chat.messages}
          isStreaming={chat.isStreaming}
          currentAgent={chat.currentAgent}
          sendMessage={chat.sendMessage}
          hasMessages={chat.messages.length > 0}
          projectContext={chatContext ?? null}
        />
      </div>
    </div>
  );
}
