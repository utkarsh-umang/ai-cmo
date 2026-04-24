import {
  Twitter,
  MessageCircle,
  Linkedin,
  Rocket,
  Newspaper,
  PenTool,
  Search,
  Globe,
  Radio,
  Sparkles,
  BookOpen,
  Camera,
  Hash,
  Code2,
  Coffee,
  MessageSquare,
  FileText,
  GitBranch,
  Zap,
  Briefcase,
  Rss,
} from "lucide-react";
import { useI18n } from "../../i18n";

interface AgentCard {
  id: string;
  icon: typeof Twitter;
  color: string;
  label: string;
  desc: string;
  prompt?: string;
  priority?: number;
}

const AGENTS: AgentCard[] = [
  {
    id: "cmo",
    icon: Sparkles,
    color: "from-indigo-500 to-violet-500",
    label: "CMO Agent",
    desc: "Full marketing strategy and multi-channel planning",
  },
  {
    id: "hackernews",
    icon: Newspaper,
    color: "from-orange-600 to-red-600",
    label: "Hacker News",
    desc: "Write Show HN posts for a developer audience",
    prompt: "I want to create a Hacker News Show HN post. Please hand off to the HN expert.",
    priority: 4,
  },
  {
    id: "twitter",
    icon: Twitter,
    color: "from-sky-400 to-blue-500",
    label: "Twitter/X Expert",
    desc: "Tweets, threads, and engagement strategy",
    prompt: "I want to create Twitter/X marketing content. Please hand off to the Twitter/X expert.",
    priority: 3,
  },
  {
    id: "reddit",
    icon: MessageCircle,
    color: "from-orange-400 to-red-500",
    label: "Reddit Expert",
    desc: "Write authentic posts and subreddit strategy",
    prompt: "I want to create Reddit posts. Please hand off to the Reddit expert.",
    priority: 3,
  },
  {
    id: "linkedin",
    icon: Linkedin,
    color: "from-blue-500 to-blue-700",
    label: "LinkedIn Expert",
    desc: "Professional posts and thought leadership",
    prompt: "I want to create LinkedIn content. Please hand off to the LinkedIn expert.",
  },
  {
    id: "blog",
    icon: FileText,
    color: "from-emerald-500 to-teal-600",
    label: "Blog / SEO Writer",
    desc: "Write articles, SEO content, and blog strategy",
    prompt: "I want to create blog and SEO content. Please hand off to the Blog/SEO expert.",
  },
  {
    id: "seo",
    icon: Search,
    color: "from-violet-500 to-purple-600",
    label: "SEO Auditor",
    desc: "Run technical SEO analysis and recommendations",
    prompt: "I want a technical SEO audit. Please hand off to the SEO audit expert.",
  },
  {
    id: "geo",
    icon: Globe,
    color: "from-cyan-500 to-blue-600",
    label: "AI Visibility (GEO)",
    desc: "Check brand mentions in AI search engines",
    prompt: "I want to check AI visibility and GEO score. Please hand off to the AI visibility expert.",
  },
  {
    id: "community",
    icon: Radio,
    color: "from-pink-500 to-rose-600",
    label: "Community Monitor",
    desc: "Scan discussions on Reddit, HN, and Dev.to",
    prompt: "I want to monitor community discussions. Please hand off to the community monitor.",
  },
];

function PriorityStars({ count }: { count: number }) {
  return <span className="ml-1 text-[10px] text-amber-500">{"★".repeat(count)}</span>;
}

export function AgentGrid({
  onSelect,
  projectName,
  showTitle = true,
}: {
  onSelect: (prompt: string) => void;
  projectName?: string | null;
  showTitle?: boolean;
}) {
  const { t } = useI18n();

  const buildPrompt = (basePrompt: string) => {
    if (!projectName || !basePrompt) return basePrompt;
    return t("agentGrid.projectPrefix", { name: projectName }) + basePrompt;
  };

  const cmoPrompt = projectName ? t("agentGrid.cmoPrompt", { name: projectName }) : "";

  return (
    <div>
      {showTitle && (
        <div className="mb-6 text-center">
          <h2 className="text-lg font-semibold text-slate-900">{t("agentGrid.title")}</h2>
          <p className="mt-1 text-sm text-slate-400">{t("agentGrid.subtitle")}</p>
        </div>
      )}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-4">
        {AGENTS.map((agent) => {
          const Icon = agent.icon;
          const resolvedPrompt = agent.id === "cmo"
            ? cmoPrompt
            : buildPrompt(agent.prompt ?? "");

          return (
            <button
              key={agent.id}
              onClick={() => {
                if (resolvedPrompt) onSelect(resolvedPrompt);
              }}
              disabled={!resolvedPrompt}
              className="group flex flex-col items-start rounded-xl border border-slate-100 p-4 text-left transition-all duration-150 hover:border-slate-200 hover:bg-slate-50 hover:shadow-sm disabled:cursor-default disabled:hover:border-slate-100 disabled:hover:bg-transparent disabled:hover:shadow-none"
            >
              <div
                className={`mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br ${agent.color} text-white shadow-sm`}
              >
                <Icon size={16} />
              </div>
              <span className="text-sm font-semibold text-slate-800">
                {agent.label}
                {agent.priority ? <PriorityStars count={agent.priority} /> : null}
              </span>
              <span className="mt-0.5 text-[11px] leading-tight text-slate-400">
                {agent.desc}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
