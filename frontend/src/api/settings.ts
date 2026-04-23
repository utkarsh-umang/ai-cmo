import { apiJson } from "./client";
import type { AISettings } from "../types";

export function getSettings(): Promise<AISettings> {
  return apiJson<AISettings>("/settings");
}

export function saveSettings(data: {
  OPENAI_API_KEY?: string;
  OPENAI_BASE_URL?: string;
  AICMO_MODEL_DEFAULT?: string;
  // Reddit
  REDDIT_CLIENT_ID?: string;
  REDDIT_CLIENT_SECRET?: string;
  REDDIT_USERNAME?: string;
  REDDIT_PASSWORD?: string;
  AICMO_AUTO_PUBLISH?: string;
  // Twitter
  TWITTER_API_KEY?: string;
  TWITTER_API_SECRET?: string;
  TWITTER_ACCESS_TOKEN?: string;
  TWITTER_ACCESS_SECRET?: string;
  // GEO
  ANTHROPIC_API_KEY?: string;
  GOOGLE_AI_API_KEY?: string;
  AICMO_GEO_CHATGPT?: string;
  // SEO
  PAGESPEED_API_KEY?: string;
  // Search (Tavily)
  TAVILY_API_KEY?: string;
  // SERP
  DATAFORSEO_LOGIN?: string;
  DATAFORSEO_PASSWORD?: string;
  // Email
  AICMO_SMTP_HOST?: string;
  AICMO_SMTP_PORT?: string;
  AICMO_SMTP_USER?: string;
  AICMO_SMTP_PASS?: string;
  AICMO_REPORT_EMAIL?: string;
}): Promise<{ ok: boolean }> {
  return apiJson("/settings", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
