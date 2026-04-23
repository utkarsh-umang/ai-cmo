"""Shared LLM-based marketing output review for agent final responses."""

from __future__ import annotations

import json
import re

from opencmo import llm

_REVIEWED_AGENT_NAMES = {
    "CMO Agent",
    "Community Monitor",
    "SEO Audit Expert",
    "Trend Research",
    "Blog SEO Expert",
    "AI Visibility Expert",
    "Twitter Expert",
    "Reddit Expert",
    "LinkedIn Expert",
    "Product Hunt Expert",
    "Hacker News Expert",
    "Devto Expert",
    "Zhihu Expert",
    "Xiaohongshu Expert",
    "V2EX Expert",
    "Juejin Expert",
    "Jike Expert",
    "WeChat Expert",
    "OSChina Expert",
    "GitCode Expert",
    "Sspai Expert",
    "InfoQ Expert",
    "Ruanyifeng Weekly Expert",
}

_PROFILE_MAP = {
    "CMO Agent": "strategic_marketing",
    "Community Monitor": "community_social",
    "SEO Audit Expert": "seo_growth",
    "Trend Research": "trend_strategy",
    "Blog SEO Expert": "longform_content",
    "AI Visibility Expert": "positioning_strategy",
    "Twitter Expert": "timeline_native",
    "Reddit Expert": "community_social",
    "LinkedIn Expert": "professional_social",
    "Product Hunt Expert": "launch_positioning",
    "Hacker News Expert": "technical_launch",
    "Devto Expert": "hands_on_longform",
    "Zhihu Expert": "hands_on_longform",
    "Xiaohongshu Expert": "experience_note",
    "V2EX Expert": "developer_forum",
    "Juejin Expert": "hands_on_longform",
    "Jike Expert": "maker_feed",
    "WeChat Expert": "hands_on_longform",
    "OSChina Expert": "developer_forum",
    "GitCode Expert": "developer_forum",
    "Sspai Expert": "longform_content",
    "InfoQ Expert": "technical_launch",
    "Ruanyifeng Weekly Expert": "submission_ready",
}

_PROFILE_GUIDANCE = {
    "strategic_marketing": "Strengthen strategic framing, differentiation, prioritization, and business trade-offs.",
    "community_social": "Reduce marketing tone, cut setup lines, keep one concrete angle per post, and make the voice feel human, useful, and natively community-friendly.",
    "developer_forum": "Make it read like a peer developer posting to a forum or OSS community: direct, practical, technically concrete, and free of promo wrapper text.",
    "maker_feed": "Make it feel like a builder sharing a real update or observation on a feed: casual, specific, lightly personal, and centered on one strong point.",
    "experience_note": "Make it feel like a real hands-on note: scenario first, concrete usage details, believable reactions, and no exaggerated outcome claims.",
    "timeline_native": "Make the copy feel native to an active X timeline: sharper hooks, less setup, fewer hashtags, one strong angle per post, and no intro before the deliverable.",
    "professional_social": "Increase clarity, proof, and executive relevance while keeping the tone concise, insight-led, and professional without generic thought-leadership filler.",
    "seo_growth": "Tie technical findings to demand capture, rankings, and practical growth outcomes.",
    "trend_strategy": "Separate noise from signal, clarify why the trend matters now, and turn insight into content or channel actions.",
    "longform_content": "Make the writing more vivid, specific, and naturally persuasive while preserving structure and utility; tighten intros and remove generic summary filler.",
    "hands_on_longform": "Keep the article practical and example-heavy: scene first, method second, product third. Cut broad claims that are not grounded in concrete usage or implementation detail.",
    "positioning_strategy": "Sharpen market positioning, recommendation potential, and why the brand should be cited or remembered.",
    "launch_positioning": "Make the launch framing clearer, more differentiated, more grounded in user value, and ready to paste into launch fields without extra commentary.",
    "submission_ready": "Make the copy concise, objective, and immediately submit-ready; preserve field structure and remove any explanatory wrapper.",
    "technical_launch": "Keep credibility high, avoid hype, and make the technical and practical value easier to grasp without flattening everything into generic engineering prose.",
}

_REVIEW_SYSTEM = """You are a senior product-marketing editor reviewing outputs from specialized marketing agents.

Apply a light-touch editorial pass so the draft is stronger on:
- audience clarity
- pain/problem articulation
- promised outcome
- proof/evidence framing
- priority and urgency
- next action clarity
- natural, human marketing language

Hard constraints:
- Preserve the original language
- Preserve all factual claims unless they are unsupported by the draft itself
- Preserve code blocks, URLs, markdown structure, and platform-specific constraints
- Do not materially restructure the draft unless clarity is broken
- Do not add fabricated metrics, testimonials, customers, or competitive claims
- Do not mention that you are reviewing or editing the draft
- Do not add setup lines, framing sentences, or process commentary such as "Below is", "Here are", "Based on the context", or "I wrote"
- For platform-content drafts, do not append analysis, explanation, or extra advice unless the user explicitly asked for it
- When multiple variants are present, preserve real angle separation and cut repetitive phrasing aggressively
- Preserve explicit section labels for multi-part deliverables; do not collapse them into unlabeled fragments or decorative separators
- If the draft is already strong, make only light edits

Return valid JSON with this shape only:
{
  "revised_output": "final revised output",
  "weak_points": ["audience" | "pain" | "promise" | "proof" | "priority" | "next_move" | "clarity" | "customer_language" | "anti_ai_tone"]
}"""


def _unwrap_nested_revised_output(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned or cleaned[0] not in "{[":
        return None

    extracted = _extract_revised_output_field(cleaned)
    if extracted:
        return extracted

    try:
        nested = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    if isinstance(nested, dict):
        nested_output = nested.get("revised_output")
        if isinstance(nested_output, str) and nested_output.strip():
            return nested_output.strip()
    return None


def _extract_revised_output_field(value: str) -> str | None:
    match = re.search(r'"revised_output"\s*:\s*"(?P<content>.*?)"\s*,\s*"weak_points"', value, re.DOTALL)
    if not match:
        return None
    content = match.group("content")
    try:
        return json.loads(f'"{content}"').strip()
    except json.JSONDecodeError:
        return None


def get_marketing_review_profile(agent_name: str | None) -> str:
    return _PROFILE_MAP.get(agent_name or "", "general_marketing")


def should_review_marketing_output(agent_name: str | None, output_text: str) -> bool:
    if not agent_name or agent_name not in _REVIEWED_AGENT_NAMES:
        return False
    if not output_text or len(output_text.strip()) < 40:
        return False
    return True


async def review_marketing_output_with_metadata(
    *,
    agent_name: str | None,
    user_message: str,
    output_text: str,
) -> dict:
    """Run a final marketing-language refinement pass when configured."""
    if not should_review_marketing_output(agent_name, output_text):
        return {
            "final_output": output_text,
            "review_applied": False,
            "profile": get_marketing_review_profile(agent_name),
            "weak_points": [],
        }

    api_key = await llm.get_key_async("OPENAI_API_KEY")
    if not api_key:
        return {
            "final_output": output_text,
            "review_applied": False,
            "profile": get_marketing_review_profile(agent_name),
            "weak_points": [],
        }

    profile = get_marketing_review_profile(agent_name)
    profile_guidance = _PROFILE_GUIDANCE.get(profile, "Improve clarity and persuasion while preserving facts.")

    user_prompt = (
        f"Agent: {agent_name}\n\n"
        f"Review profile: {profile}\n"
        f"Profile guidance: {profile_guidance}\n\n"
        f"User request:\n{user_message}\n\n"
        f"Draft output:\n{output_text}"
    )
    try:
        revised = await llm.chat_completion(
            _REVIEW_SYSTEM,
            user_prompt,
            temperature=0.2,
            timeout=90,
        )
    except Exception:
        return {
            "final_output": output_text,
            "review_applied": False,
            "profile": profile,
            "weak_points": [],
        }

    try:
        parsed = json.loads(revised)
    except json.JSONDecodeError:
        cleaned = revised.strip()
        nested_output = _unwrap_nested_revised_output(cleaned)
        if nested_output:
            return {
                "final_output": nested_output,
                "review_applied": True,
                "profile": profile,
                "weak_points": [],
            }
        if cleaned:
            return {
                "final_output": cleaned,
                "review_applied": True,
                "profile": profile,
                "weak_points": [],
            }
        return {
            "final_output": output_text,
            "review_applied": False,
            "profile": profile,
            "weak_points": [],
        }

    if isinstance(parsed, str):
        nested_output = _unwrap_nested_revised_output(parsed)
        if nested_output:
            return {
                "final_output": nested_output,
                "review_applied": True,
                "profile": profile,
                "weak_points": [],
            }
        return {
            "final_output": parsed.strip() or output_text,
            "review_applied": True,
            "profile": profile,
            "weak_points": [],
        }

    if not isinstance(parsed, dict):
        return {
            "final_output": output_text,
            "review_applied": False,
            "profile": profile,
            "weak_points": [],
        }

    final_output = str(parsed.get("revised_output", "")).strip() or output_text
    nested_output = _unwrap_nested_revised_output(final_output)
    if nested_output:
        final_output = nested_output
    weak_points = parsed.get("weak_points", [])
    if not isinstance(weak_points, list):
        weak_points = []

    return {
        "final_output": final_output,
        "review_applied": True,
        "profile": profile,
        "weak_points": [str(item) for item in weak_points[:5]],
    }


async def review_marketing_output(
    *,
    agent_name: str | None,
    user_message: str,
    output_text: str,
) -> str:
    result = await review_marketing_output_with_metadata(
        agent_name=agent_name,
        user_message=user_message,
        output_text=output_text,
    )
    return result["final_output"]
