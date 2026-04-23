"""GitHub user discovery and outreach tools for the agent framework."""

from __future__ import annotations

import json
import logging

from agents import function_tool

from opencmo import llm, storage
from opencmo.tools.github_api import (
    fetch_followers,
    fetch_following,
)

logger = logging.getLogger(__name__)


@function_tool
async def discover_github_users(
    seed_username: str,
    source: str = "both",
    max_hops: int = 1,
    project_id: int = 0,
) -> str:
    """Discover GitHub users from a seed user's followers and following lists.

    Fetches the social graph, stores raw leads, and kicks off background
    enrichment. Use list_github_leads afterwards to browse the results.

    Args:
        seed_username: The GitHub username to start from (e.g. "helallao").
        source: Which list to fetch: "followers", "following", or "both".
        max_hops: Discovery depth — 1 = direct only, 2 = also explore top leads' networks.
        project_id: The project to associate leads with.
    """
    if not seed_username:
        return json.dumps({"error": "seed_username is required"})
    if project_id <= 0:
        return json.dumps({"error": "project_id is required"})

    users: list[dict] = []
    if source in ("both", "followers"):
        users.extend(await fetch_followers(seed_username))
    if source in ("both", "following"):
        users.extend(await fetch_following(seed_username))

    # Deduplicate
    seen: set[str] = set()
    unique: list[dict] = []
    for u in users:
        login = u.get("login", "")
        if login and login not in seen:
            seen.add(login)
            unique.append(u)

    # Store raw leads
    for u in unique:
        u["source"] = source
        u["seed_username"] = seed_username
    count = await storage.batch_upsert_github_leads(project_id, unique)

    # Enqueue background enrichment task
    task_id = ""
    try:
        from opencmo.background import service as bg_service
        task = await bg_service.enqueue_task(
            kind="github_enrich",
            project_id=project_id,
            payload={
                "project_id": project_id,
                "seed_username": seed_username,
                "source": source,
                "max_hops": max_hops,
            },
            dedupe_key=f"github_enrich:{project_id}:{seed_username}",
            priority=40,
        )
        task_id = task.get("task_id", "")
        await storage.create_discovery_run(
            project_id, task_id, seed_username, source, max_hops,
        )
    except Exception as exc:
        logger.warning("Could not enqueue enrichment task: %s", exc)

    return json.dumps({
        "discovered": len(unique),
        "stored": count,
        "seed_username": seed_username,
        "source": source,
        "max_hops": max_hops,
        "task_id": task_id,
        "note": "Enrichment is running in the background. Use list_github_leads to check results.",
    })


@function_tool
async def list_github_leads_tool(
    project_id: int,
    min_score: float = 0,
    has_email: bool = False,
    language: str = "",
    location: str = "",
    limit: int = 50,
) -> str:
    """List discovered GitHub leads with optional filters.

    Args:
        project_id: The project to list leads for.
        min_score: Minimum outreach score (0-100).
        has_email: If true, only return leads with a public email.
        language: Filter by primary programming language.
        location: Filter by location substring.
        limit: Max results to return.
    """
    leads = await storage.list_github_leads(
        project_id,
        min_score=min_score if min_score > 0 else None,
        has_email=has_email or None,
        language=language or None,
        location=location or None,
        enriched=True,
        limit=limit,
    )
    stats = await storage.get_github_lead_stats(project_id)

    # Summarize for the agent
    rows = []
    for lead in leads:
        rows.append({
            "login": lead["login"],
            "name": lead["name"],
            "bio": lead["bio"][:100],
            "email": lead["email"],
            "twitter": lead["twitter_username"],
            "location": lead["location"],
            "languages": lead["top_languages"][:3],
            "stars": lead["total_stars"],
            "score": lead["outreach_score"],
            "status": lead["outreach_status"],
        })

    return json.dumps({"stats": stats, "leads": rows, "showing": len(rows)})


@function_tool
async def score_github_leads(project_id: int) -> str:
    """Score all enriched GitHub leads for outreach priority.

    Uses product-aware scoring: tech stack match, keyword relevance,
    reachability (email/twitter/blog), and activity metrics.
    Leads without any contact info get score 0.

    Args:
        project_id: The project whose leads to score.
    """
    from opencmo.services.github_service import compute_outreach_score, has_contact_info

    project = await storage.get_project(project_id)
    category = project.get("category", "") if project else ""

    from opencmo.storage.serp import list_tracked_keywords
    kw_rows = await list_tracked_keywords(project_id)
    keywords = [r["keyword"] for r in kw_rows] if kw_rows else []

    leads = await storage.list_github_leads(project_id, enriched=True, limit=1000)
    updated = 0

    for lead in leads:
        if not has_contact_info(lead):
            await storage.update_lead_score(project_id, lead["login"], 0)
            updated += 1
            continue

        score = compute_outreach_score(lead, category=category, keywords=keywords)
        await storage.update_lead_score(project_id, lead["login"], score)
        updated += 1

    stats = await storage.get_github_lead_stats(project_id)
    return json.dumps({
        "scored": updated,
        "stats": stats,
        "note": "Scores updated with product-aware scoring. Use list_github_leads to view ranked leads.",
    })


@function_tool
async def generate_github_outreach(
    project_id: int,
    logins: str,
    channel: str = "email",
    tone: str = "friendly-professional",
) -> str:
    """Generate personalized outreach messages for selected GitHub leads.

    Messages are created as approval queue items for human review before sending.

    Args:
        project_id: The project context for the outreach.
        logins: Comma-separated GitHub usernames to generate outreach for.
        channel: Outreach channel: "email", "twitter_dm", or "github_issue".
        tone: Message tone: "friendly-professional", "casual-dev", or "technical".
    """
    login_list = [login.strip() for login in logins.split(",") if login.strip()]
    if not login_list:
        return json.dumps({"error": "No logins provided"})

    project = await storage.get_project(project_id)
    if not project:
        return json.dumps({"error": "Project not found"})

    brand_kit = await storage.get_brand_kit(project_id)
    brand_context = ""
    if brand_kit:
        brand_context = f"Brand: {project['brand_name']}. Tone: {brand_kit.get('tone_of_voice', '')}. Audience: {brand_kit.get('target_audience', '')}."
    else:
        brand_context = f"Brand: {project['brand_name']}. URL: {project['url']}. Category: {project['category']}."

    results = []
    for login in login_list:
        lead = await storage.get_github_lead(project_id, login)
        if not lead:
            continue

        lead_context = (
            f"GitHub user: @{lead['login']}\n"
            f"Name: {lead['name'] or 'Unknown'}\n"
            f"Bio: {lead['bio'] or 'No bio'}\n"
            f"Location: {lead['location'] or 'Unknown'}\n"
            f"Languages: {', '.join(lead.get('top_languages', []) or ['Unknown'])}\n"
            f"Stars: {lead.get('total_stars', 0)}\n"
            f"Top repos: {json.dumps(lead.get('top_repos', [])[:3])}\n"
        )

        channel_instruction = {
            "email": "Write a professional but warm email (subject + body). Reference their specific work. Keep under 200 words.",
            "twitter_dm": "Write a brief Twitter DM (under 280 chars). Be casual and reference shared interests.",
            "github_issue": "Write a GitHub Issue title + body that's genuinely relevant to one of their repos. Do NOT spam.",
        }.get(channel, "Write a short outreach message.")

        system_prompt = (
            f"You are crafting a personalized developer outreach message.\n\n"
            f"## Brand Context\n{brand_context}\n\n"
            f"## Recipient\n{lead_context}\n\n"
            f"## Channel: {channel}\n{channel_instruction}\n\n"
            f"## Tone: {tone}\n\n"
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
            logger.warning("LLM generation failed for %s: %s", login, exc)
            continue

        # Create approval queue item
        approval_type = f"github_outreach_{channel}"
        approval_channel = f"github_{channel}"
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

    return json.dumps({
        "generated": len(results),
        "approvals": results,
        "note": "Outreach messages created in the approval queue for human review.",
    })
