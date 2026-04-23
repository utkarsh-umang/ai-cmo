"""GitHub outreach service — auto-discovery, scoring, and outreach generation."""

from __future__ import annotations

import asyncio
import json
import logging

import httpx

from opencmo import llm, storage

logger = logging.getLogger(__name__)

# Category → likely programming languages
_CATEGORY_LANGUAGES: dict[str, list[str]] = {
    "devtools": ["Python", "Go", "Rust", "TypeScript", "JavaScript"],
    "saas": ["TypeScript", "JavaScript", "Python", "Ruby"],
    "ai": ["Python", "Jupyter Notebook", "C++", "Rust"],
    "marketing": ["TypeScript", "JavaScript", "Python"],
    "analytics": ["Python", "R", "TypeScript", "SQL"],
    "ecommerce": ["TypeScript", "JavaScript", "PHP", "Ruby"],
    "fintech": ["Python", "Go", "Java", "Rust"],
    "productivity": ["TypeScript", "JavaScript", "Swift", "Kotlin"],
    "security": ["Python", "Go", "Rust", "C"],
    "infra": ["Go", "Rust", "Python", "C++"],
    "education": ["Python", "JavaScript", "TypeScript"],
    "design": ["TypeScript", "JavaScript", "Swift"],
}


def _is_rate_limit_error(exc: Exception) -> bool:
    message = str(exc).lower()
    if "rate limit" in message:
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {403, 429}
    return False


def compute_outreach_score(
    lead: dict,
    *,
    category: str = "",
    keywords: list[str] | None = None,
) -> float:
    """Score a lead 0-100 with product awareness.

    Reachability (base):
        email +20, twitter +15, blog +10, hireable +10
    Activity:
        stars>10 +5, repos>5 +5, followers>20 +5
    Product relevance:
        tech stack matches category +15
        bio mentions keywords +10
        active (has repos) +5
    """
    score = 0.0

    # --- Reachability (must have at least email or twitter) ---
    if lead.get("email"):
        score += 20
    if lead.get("twitter_username"):
        score += 15
    if lead.get("blog"):
        score += 10
    if lead.get("hireable"):
        score += 10

    # --- Activity ---
    if (lead.get("total_stars") or 0) > 10:
        score += 5
    if (lead.get("public_repos") or 0) > 5:
        score += 5
    if (lead.get("followers") or 0) > 20:
        score += 5

    # --- Product relevance ---
    if category:
        expected_langs = _CATEGORY_LANGUAGES.get(category, [])
        lead_langs = lead.get("top_languages") or []
        if any(lang in expected_langs for lang in lead_langs):
            score += 15

    if keywords:
        bio = (lead.get("bio") or "").lower()
        repo_text = " ".join(
            r.get("description", "").lower()
            for r in (lead.get("top_repos") or [])
        )
        combined = bio + " " + repo_text
        matched = sum(1 for kw in keywords if kw.lower() in combined)
        if matched >= 2:
            score += 10
        elif matched >= 1:
            score += 5

    if lead.get("top_languages"):
        score += 5

    return min(score, 100)


def has_contact_info(lead: dict) -> bool:
    """Return True if the lead has at least email or twitter."""
    return bool(lead.get("email") or lead.get("twitter_username"))


# ---------------------------------------------------------------------------
# Auto-discovery from product context
# ---------------------------------------------------------------------------

def _build_search_queries(
    category: str,
    keywords: list[str],
    competitors: list[dict],
) -> list[str]:
    """Build GitHub search queries from product analysis."""
    queries: list[str] = []

    # Keyword-based repo search (top 3 keywords)
    for kw in keywords[:3]:
        queries.append(kw)

    # Category + keyword combos
    if category and keywords:
        queries.append(f"{category} {keywords[0]}")

    # Competitor names as search terms (people interested in competitors)
    for comp in competitors[:3]:
        name = comp.get("name", "")
        if name:
            queries.append(name)

    return queries


async def auto_discover_from_product(
    project_id: int,
    *,
    on_progress=None,
) -> dict:
    """Fully automatic GitHub lead discovery from product context.

    1. Build search queries from project's category, keywords, competitors
    2. Search GitHub repos → collect owner + stargazers
    3. Search GitHub users directly
    4. Enrich profiles
    5. Score with product awareness
    6. Only keep leads with contact info (email or twitter)
    """
    from opencmo.tools.github_api import (
        enrich_user,
        fetch_stargazers,
        get_rate_remaining,
        search_repositories,
        search_users,
    )

    project = await storage.get_project(project_id)
    if not project:
        return {"error": "Project not found", "discovered": 0, "contactable": 0}

    category = project.get("category", "")
    brand = project.get("brand_name", "")

    # Gather keywords and competitors
    from opencmo.storage.serp import list_tracked_keywords
    kw_rows = await list_tracked_keywords(project_id)
    keywords = [r["keyword"] for r in kw_rows] if kw_rows else []

    competitors_rows = await storage.list_competitors(project_id)
    competitors = [{"name": c["name"], "url": c.get("url", "")} for c in competitors_rows]

    if not keywords and not competitors:
        # Fallback: use brand + category as search terms
        keywords = [brand, category] if category else [brand]

    queries = _build_search_queries(category, keywords, competitors)
    logger.info("GitHub auto-discovery for project %d: %d queries", project_id, len(queries))

    # --- Phase 1: Collect candidate logins ---
    seen: set[str] = set()
    candidates: list[dict] = []
    warnings: list[str] = []

    def note_warning(message: str) -> None:
        if message not in warnings:
            warnings.append(message)

    # 1a. Search repos and collect owners + top stargazers
    for query in queries[:5]:
        if get_rate_remaining() < 300:
            logger.info("Rate limit low, stopping repo search")
            break
        try:
            repos = await search_repositories(query, per_page=10, max_pages=1)
            for repo in repos[:5]:
                owner = repo.get("owner_login", "")
                if owner and owner not in seen:
                    seen.add(owner)
                    candidates.append({"login": owner, "source": "repo_owner", "seed_username": query})

                # Fetch stargazers from top repos (high-intent users)
                if repo.get("stars", 0) > 50:
                    full_name = repo.get("full_name", "")
                    if "/" in full_name:
                        parts = full_name.split("/", 1)
                        try:
                            stargazers = await fetch_stargazers(parts[0], parts[1], per_page=30, max_pages=1)
                            for sg in stargazers:
                                login = sg.get("login", "")
                                if login and login not in seen:
                                    seen.add(login)
                                    candidates.append({"login": login, "source": "stargazer", "seed_username": full_name})
                        except Exception:
                            pass
        except Exception as exc:
            logger.warning("Repo search failed for %r: %s", query, exc)
            if _is_rate_limit_error(exc):
                note_warning("GitHub API rate limit exceeded during repository discovery. Results may be incomplete.")

    # 1b. Search users directly with keyword queries
    for query in queries[:3]:
        if get_rate_remaining() < 300:
            break
        try:
            users = await search_users(query, per_page=20, max_pages=1)
            for u in users:
                login = u.get("login", "")
                if login and login not in seen:
                    seen.add(login)
                    candidates.append({"login": login, "source": "user_search", "seed_username": query})
        except Exception as exc:
            logger.warning("User search failed for %r: %s", query, exc)
            if _is_rate_limit_error(exc):
                note_warning("GitHub API rate limit exceeded during user discovery. Results may be incomplete.")

    if not candidates:
        return {"discovered": 0, "enriched": 0, "contactable": 0, "warnings": warnings}

    # Store raw leads
    for c in candidates:
        c["github_id"] = c.get("github_id")
    await storage.batch_upsert_github_leads(project_id, candidates)

    # --- Phase 2: Enrich profiles ---
    enriched_count = 0
    enriched_profiles: list[dict] = []
    batch_size = 20

    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i + batch_size]
        for c in batch:
            if get_rate_remaining() < 200:
                logger.info("Rate limit low (%d), pausing enrichment", get_rate_remaining())
                await asyncio.sleep(10)
            try:
                profile = await enrich_user(c["login"])
                enriched_profiles.append(profile)
                enriched_count += 1
            except Exception as exc:
                logger.debug("Enrich failed for %s: %s", c["login"], exc)

        if enriched_profiles:
            await storage.batch_update_enrichment(project_id, enriched_profiles[-len(batch):])

    # --- Phase 3: Score with product context, keep only contactable ---
    contactable = 0
    for profile in enriched_profiles:
        if not has_contact_info(profile):
            # Remove non-contactable leads
            continue

        score = compute_outreach_score(
            profile, category=category, keywords=keywords,
        )
        await storage.update_lead_score(project_id, profile["login"], score)
        contactable += 1

    # Delete leads without contact info
    all_leads = await storage.list_github_leads(project_id, enriched=True, limit=5000)
    for lead in all_leads:
        if not has_contact_info(lead):
            # Update score to 0 so they sink to bottom / get filtered
            await storage.update_lead_score(project_id, lead["login"], 0)

    return {
        "discovered": len(candidates),
        "enriched": enriched_count,
        "contactable": contactable,
        "warnings": warnings,
    }


async def generate_outreach_batch(
    project_id: int,
    logins: list[str],
    channel: str = "email",
) -> dict:
    """Generate personalized outreach for a batch of leads, create approval items."""
    project = await storage.get_project(project_id)
    if not project:
        return {"ok": False, "error": "Project not found"}

    brand_kit = await storage.get_brand_kit(project_id)
    brand_context = ""
    if brand_kit:
        brand_context = (
            f"Brand: {project['brand_name']}. "
            f"Tone: {brand_kit.get('tone_of_voice', '')}. "
            f"Audience: {brand_kit.get('target_audience', '')}."
        )
    else:
        brand_context = (
            f"Brand: {project['brand_name']}. "
            f"URL: {project['url']}. "
            f"Category: {project['category']}."
        )

    channel_instruction = {
        "email": "Write a professional but warm email (subject line + body). Reference their specific work. Keep under 200 words.",
        "twitter_dm": "Write a brief Twitter DM (under 280 chars). Be casual and reference shared interests.",
        "github_issue": "Write a GitHub Issue title + body that's genuinely relevant to one of their repos. Do NOT spam.",
    }.get(channel, "Write a short outreach message.")

    results = []
    for login in logins:
        lead = await storage.get_github_lead(project_id, login)
        if not lead:
            continue

        lead_context = (
            f"GitHub: @{lead['login']}\n"
            f"Name: {lead['name'] or 'Unknown'}\n"
            f"Bio: {lead['bio'] or 'No bio'}\n"
            f"Location: {lead['location'] or 'Unknown'}\n"
            f"Languages: {', '.join(lead.get('top_languages', []) or ['Unknown'])}\n"
            f"Stars: {lead.get('total_stars', 0)}\n"
            f"Top repos: {json.dumps(lead.get('top_repos', [])[:3])}\n"
        )

        system_prompt = (
            f"You are crafting a personalized developer outreach message.\n\n"
            f"## Brand Context\n{brand_context}\n\n"
            f"## Recipient\n{lead_context}\n\n"
            f"## Channel: {channel}\n{channel_instruction}\n\n"
            f"Be genuine and personalize based on their actual repos/work. "
            f"Never sound like marketing spam. Provide value first."
        )

        try:
            message = await llm.chat_completion_messages(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate a {channel} outreach message for @{login}."},
                ],
                temperature=0.8,
            )
        except Exception as exc:
            logger.warning("LLM failed for %s: %s", login, exc)
            continue

        approval_channel = f"github_{channel}"
        approval_type = f"github_outreach_{channel}"

        try:
            approval = await storage.create_approval(
                project_id=project_id,
                channel=approval_channel,
                approval_type=approval_type,
                content=message,
                payload={
                    "login": login,
                    "channel": channel,
                    "recipient_email": lead.get("email", ""),
                    "recipient_twitter": lead.get("twitter_username", ""),
                },
                preview={
                    "recipient": f"@{login}",
                    "name": lead.get("name", ""),
                    "channel": channel,
                },
                title=f"GitHub outreach to {lead.get('name') or login}",
                target_label=f"@{login}",
                target_url=f"https://github.com/{login}",
                agent_name="GitHub Outreach Expert",
            )
            await storage.update_lead_outreach(
                project_id, login, "draft_pending", channel=channel,
            )
            results.append({"login": login, "approval_id": approval["id"]})
        except Exception as exc:
            logger.warning("Failed to create approval for %s: %s", login, exc)

    return {"ok": True, "count": len(results), "approvals": results}
