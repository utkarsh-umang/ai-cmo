"""Async GitHub REST API client with rate-limit awareness."""

from __future__ import annotations

import asyncio
import logging
import os

import httpx

logger = logging.getLogger(__name__)

_API_BASE = "https://api.github.com"
_SEM = asyncio.Semaphore(10)  # max concurrent GitHub requests
_rate_remaining: int = 5000  # optimistic default


async def _get_github_token() -> str | None:
    """Resolve token: DB settings > env var."""
    try:
        from opencmo.storage.settings import get_setting
        val = await get_setting("GITHUB_TOKEN")
        if val:
            return val
    except Exception:
        pass
    return os.environ.get("GITHUB_TOKEN")


async def _github_get(
    path: str,
    *,
    token: str | None = None,
    params: dict | None = None,
) -> dict | list:
    """Single authenticated GET request to api.github.com."""
    global _rate_remaining

    if token is None:
        token = await _get_github_token()

    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with _SEM:
        # Throttle when rate limit is low
        if _rate_remaining < 500:
            logger.info("GitHub rate limit low (%d), throttling", _rate_remaining)
            await asyncio.sleep(2)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{_API_BASE}{path}", headers=headers, params=params)

        # Track rate limits
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining is not None:
            _rate_remaining = int(remaining)

        resp.raise_for_status()
        return resp.json()


async def _github_get_paginated(
    path: str,
    *,
    per_page: int = 100,
    max_pages: int = 3,
) -> list[dict]:
    """Paginated GET that collects multiple pages."""
    all_items: list[dict] = []
    token = await _get_github_token()
    for page in range(1, max_pages + 1):
        items = await _github_get(
            path, token=token, params={"per_page": per_page, "page": page},
        )
        if not isinstance(items, list):
            break
        all_items.extend(items)
        if len(items) < per_page:
            break  # last page
    return all_items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def fetch_user_profile(login: str) -> dict:
    """GET /users/{login} -> profile dict."""
    raw = await _github_get(f"/users/{login}")
    if not isinstance(raw, dict):
        return {}
    return {
        "login": raw.get("login", login),
        "github_id": raw.get("id"),
        "name": raw.get("name") or "",
        "bio": raw.get("bio") or "",
        "company": raw.get("company") or "",
        "location": raw.get("location") or "",
        "email": raw.get("email") or "",
        "blog": raw.get("blog") or "",
        "twitter_username": raw.get("twitter_username") or "",
        "hireable": raw.get("hireable"),
        "followers": raw.get("followers", 0),
        "following": raw.get("following", 0),
        "public_repos": raw.get("public_repos", 0),
        "created_at_gh": raw.get("created_at", ""),
    }


async def fetch_user_repos(login: str, per_page: int = 30) -> list[dict]:
    """GET /users/{login}/repos sorted by most recently pushed."""
    raw = await _github_get(
        f"/users/{login}/repos",
        params={"sort": "pushed", "per_page": per_page, "direction": "desc"},
    )
    if not isinstance(raw, list):
        return []
    return [
        {
            "name": r.get("name", ""),
            "description": r.get("description") or "",
            "language": r.get("language") or "",
            "stars": r.get("stargazers_count", 0),
            "topics": r.get("topics", []),
            "updated_at": r.get("pushed_at", ""),
        }
        for r in raw
    ]


async def fetch_followers(login: str, per_page: int = 100, max_pages: int = 3) -> list[dict]:
    """GET /users/{login}/followers with pagination."""
    items = await _github_get_paginated(
        f"/users/{login}/followers", per_page=per_page, max_pages=max_pages,
    )
    return [{"login": u.get("login", ""), "github_id": u.get("id")} for u in items if u.get("login")]


async def fetch_following(login: str, per_page: int = 100, max_pages: int = 3) -> list[dict]:
    """GET /users/{login}/following with pagination."""
    items = await _github_get_paginated(
        f"/users/{login}/following", per_page=per_page, max_pages=max_pages,
    )
    return [{"login": u.get("login", ""), "github_id": u.get("id")} for u in items if u.get("login")]


async def enrich_user(login: str) -> dict:
    """Fetch profile + repos, compute top languages and stars."""
    profile = await fetch_user_profile(login)
    repos = await fetch_user_repos(login)

    languages: dict[str, int] = {}
    total_stars = 0
    for repo in repos:
        lang = repo.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
        total_stars += repo.get("stars", 0)

    top_langs = [language for language, _count in sorted(languages.items(), key=lambda item: -item[1])[:5]]
    top_repos = sorted(repos, key=lambda r: r.get("stars", 0), reverse=True)[:5]

    return {
        **profile,
        "top_languages": top_langs,
        "total_stars": total_stars,
        "top_repos": [
            {"name": r["name"], "description": r["description"], "language": r["language"], "stars": r["stars"]}
            for r in top_repos
        ],
        "enriched": True,
    }


async def search_repositories(
    query: str,
    *,
    language: str | None = None,
    sort: str = "stars",
    per_page: int = 30,
    max_pages: int = 2,
) -> list[dict]:
    """Search GitHub repos. Returns list of {full_name, description, language, stars, topics, owner_login}."""
    q = query
    if language:
        q += f" language:{language}"

    all_repos: list[dict] = []
    token = await _get_github_token()
    for page in range(1, max_pages + 1):
        raw = await _github_get(
            "/search/repositories",
            token=token,
            params={"q": q, "sort": sort, "per_page": per_page, "page": page},
        )
        if not isinstance(raw, dict):
            break
        items = raw.get("items", [])
        for r in items:
            all_repos.append({
                "full_name": r.get("full_name", ""),
                "description": r.get("description") or "",
                "language": r.get("language") or "",
                "stars": r.get("stargazers_count", 0),
                "topics": r.get("topics", []),
                "owner_login": r.get("owner", {}).get("login", ""),
            })
        if len(items) < per_page:
            break
    return all_repos


async def search_users(
    query: str,
    *,
    sort: str = "followers",
    per_page: int = 30,
    max_pages: int = 2,
) -> list[dict]:
    """Search GitHub users. Returns list of {login, github_id}."""
    all_users: list[dict] = []
    token = await _get_github_token()
    for page in range(1, max_pages + 1):
        raw = await _github_get(
            "/search/users",
            token=token,
            params={"q": query, "sort": sort, "per_page": per_page, "page": page},
        )
        if not isinstance(raw, dict):
            break
        items = raw.get("items", [])
        for u in items:
            login = u.get("login", "")
            if login:
                all_users.append({"login": login, "github_id": u.get("id")})
        if len(items) < per_page:
            break
    return all_users


async def fetch_stargazers(
    owner: str,
    repo: str,
    per_page: int = 100,
    max_pages: int = 2,
) -> list[dict]:
    """Fetch users who starred a repo. Returns list of {login, github_id}."""
    items = await _github_get_paginated(
        f"/repos/{owner}/{repo}/stargazers",
        per_page=per_page,
        max_pages=max_pages,
    )
    return [{"login": u.get("login", ""), "github_id": u.get("id")} for u in items if u.get("login")]


def get_rate_remaining() -> int:
    """Return current known rate limit remaining."""
    return _rate_remaining
