"""Executor for GitHub user discovery and enrichment tasks."""

from __future__ import annotations

import asyncio
import logging

from opencmo import storage

logger = logging.getLogger(__name__)


async def run_github_enrich_executor(ctx) -> None:
    task = ctx.task
    payload = task["payload"]
    project_id = payload["project_id"]
    seed_username = payload["seed_username"]
    source = payload.get("source", "both")
    max_hops = payload.get("max_hops", 1)

    from opencmo.tools.github_api import (
        enrich_user,
        fetch_followers,
        fetch_following,
        get_rate_remaining,
    )

    # ---- Phase 1: Discover direct connections ----
    await ctx.emit(
        event_type="progress", phase="discover", status="running",
        summary=f"Fetching {source} for {seed_username}...",
    )

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

    for u in unique:
        u["source"] = source
        u["seed_username"] = seed_username

    await storage.batch_upsert_github_leads(project_id, unique)
    await ctx.emit(
        event_type="progress", phase="discover", status="completed",
        summary=f"Discovered {len(unique)} users from {seed_username}",
    )

    # ---- Phase 2: Enrich profiles ----
    await ctx.emit(
        event_type="progress", phase="enrich", status="running",
        summary=f"Enriching {len(unique)} profiles...",
    )

    enriched_count = 0
    batch_size = 20
    for i in range(0, len(unique), batch_size):
        batch = unique[i:i + batch_size]
        await ctx.emit(
            event_type="progress", phase="enrich", status="running",
            summary=f"Enriching {i + 1}-{min(i + batch_size, len(unique))} of {len(unique)}",
        )

        enriched_batch: list[dict] = []
        for u in batch:
            if get_rate_remaining() < 200:
                logger.info("Rate limit low (%d), pausing enrichment", get_rate_remaining())
                await asyncio.sleep(10)

            try:
                profile = await enrich_user(u["login"])
                enriched_batch.append(profile)
                enriched_count += 1
            except Exception as exc:
                logger.warning("Failed to enrich %s: %s", u["login"], exc)

        if enriched_batch:
            await storage.batch_update_enrichment(project_id, enriched_batch)

    await ctx.emit(
        event_type="progress", phase="enrich", status="completed",
        summary=f"Enriched {enriched_count} of {len(unique)} profiles",
    )

    # ---- Phase 3: Multi-hop discovery (if max_hops >= 2) ----
    hop2_discovered = 0
    hop2_enriched = 0
    if max_hops >= 2:
        await ctx.emit(
            event_type="progress", phase="hop2", status="running",
            summary="Starting second-level discovery...",
        )

        # Pick top N direct leads by followers count for second hop
        top_leads = await storage.list_github_leads(
            project_id, enriched=True, limit=10,
        )
        # Sort by followers descending
        top_leads = sorted(top_leads, key=lambda lead_item: lead_item.get("followers", 0), reverse=True)[:10]

        for lead in top_leads:
            if get_rate_remaining() < 300:
                logger.info("Rate limit low, stopping hop2 discovery")
                break

            lead_login = lead["login"]
            hop2_users: list[dict] = []
            try:
                hop2_users = await fetch_followers(lead_login, max_pages=1)
            except Exception:
                continue

            new_users = []
            for u in hop2_users:
                login = u.get("login", "")
                if login and login not in seen:
                    seen.add(login)
                    u["source"] = "hop2"
                    u["seed_username"] = seed_username
                    new_users.append(u)

            if new_users:
                await storage.batch_upsert_github_leads(project_id, new_users)
                hop2_discovered += len(new_users)

                # Enrich hop2 users in smaller batches
                hop2_batch: list[dict] = []
                for u in new_users[:10]:  # limit enrichment per hop2 seed
                    try:
                        profile = await enrich_user(u["login"])
                        hop2_batch.append(profile)
                        hop2_enriched += 1
                    except Exception:
                        pass
                if hop2_batch:
                    await storage.batch_update_enrichment(project_id, hop2_batch)

        await ctx.emit(
            event_type="progress", phase="hop2", status="completed",
            summary=f"Hop2: discovered {hop2_discovered}, enriched {hop2_enriched}",
        )

    # ---- Phase 4: Score all leads with product context ----
    await ctx.emit(
        event_type="progress", phase="score", status="running",
        summary="Computing product-aware outreach scores...",
    )

    from opencmo.services.github_service import compute_outreach_score, has_contact_info

    project = await storage.get_project(project_id)
    category = project.get("category", "") if project else ""
    from opencmo.storage.serp import list_tracked_keywords
    kw_rows = await list_tracked_keywords(project_id)
    keywords = [r["keyword"] for r in kw_rows] if kw_rows else []

    all_leads = await storage.list_github_leads(project_id, enriched=True, limit=2000)
    for lead in all_leads:
        if not has_contact_info(lead):
            await storage.update_lead_score(project_id, lead["login"], 0)
            continue
        score = compute_outreach_score(lead, category=category, keywords=keywords)
        await storage.update_lead_score(project_id, lead["login"], score)

    contactable = sum(1 for lead_item in all_leads if has_contact_info(lead_item))
    await ctx.emit(
        event_type="progress", phase="score", status="completed",
        summary=f"Scored {len(all_leads)} leads, {contactable} contactable",
    )

    total_discovered = len(unique) + hop2_discovered
    total_enriched = enriched_count + hop2_enriched

    # Update discovery run record
    runs = await storage.list_discovery_runs(project_id, limit=1)
    if runs:
        await storage.update_discovery_run(
            runs[0]["id"],
            total_discovered=total_discovered,
            total_enriched=total_enriched,
            status="completed",
            completed_at="datetime('now')",
        )

    await ctx.complete({
        "total_discovered": total_discovered,
        "total_enriched": total_enriched,
        "seed_username": seed_username,
        "max_hops": max_hops,
    })
