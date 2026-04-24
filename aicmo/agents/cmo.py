from agents import Agent, handoff

from aicmo.agents.blog import blog_expert
from aicmo.agents.community import community_agent
from aicmo.agents.geo import geo_agent
from aicmo.agents.hackernews import hackernews_expert
from aicmo.agents.linkedin import linkedin_expert
from aicmo.agents.prompt_contracts import build_prompt
from aicmo.agents.reddit import reddit_expert
from aicmo.agents.seo import seo_agent
from aicmo.agents.trend import trend_agent
from aicmo.agents.twitter import twitter_expert
from aicmo.config import get_model
from aicmo.tools.competitor import analyze_competitor
from aicmo.tools.crawl import crawl_website
from aicmo.tools.graph_intel import get_competitive_landscape
from aicmo.tools.research_brief import generate_research_brief
from aicmo.tools.search import web_search


def _multi_channel_tool(agent: Agent, *, tool_name: str, tool_description: str):
    return agent.as_tool(
        tool_name=tool_name,
        tool_description=(
            "Use ONLY for coordinated multi-channel orchestration when the user asked for content across multiple platforms "
            "and the CMO needs to collect outputs without handing off. Never use this for a single-platform request. "
            f"{tool_description}"
        ),
    )


# as_tool wrappers — CMO calls these in multi-channel mode to retain control
twitter_tool = _multi_channel_tool(
    twitter_expert,
    tool_name="generate_twitter_content",
    tool_description="Generate Twitter/X marketing content (tweets + thread). Returns formatted content.",
)
reddit_tool = _multi_channel_tool(
    reddit_expert,
    tool_name="generate_reddit_content",
    tool_description="Generate authentic Reddit posts for r/SideProject and niche subreddits.",
)
linkedin_tool = _multi_channel_tool(
    linkedin_expert,
    tool_name="generate_linkedin_content",
    tool_description="Generate professional LinkedIn posts. Returns long-form and short-form variants.",
)
hackernews_tool = _multi_channel_tool(
    hackernews_expert,
    tool_name="generate_hackernews_content",
    tool_description="Generate Hacker News Show HN post (title + body).",
)
blog_tool = _multi_channel_tool(
    blog_expert,
    tool_name="generate_blog_content",
    tool_description="Generate blog/SEO article outlines, SEO recommendations, or full 2000+ word articles with research.",
)
trend_tool = trend_agent.as_tool(
    tool_name="research_trends",
    tool_description="Research trending topics across community platforms (Reddit, HN, YouTube, Bluesky, Twitter/X, Dev.to). Supports comparative mode for 'X vs Y' queries.",
)

cmo_agent = Agent(
    name="CMO Agent",
    instructions=build_prompt(
        base_instructions="""You are an AI Chief Marketing Officer (CMO) helping indie developers and startup founders create marketing content for their products.

Your job is to think like a real marketing leader, not a generic assistant. Convert product facts into audience-aware positioning, channel strategy, differentiated messaging, and the next best growth move.

## Your Workflow

1. **When the user provides a website URL**: Use the `crawl_website` tool to fetch and analyze the product's website content. Then extract:
   - **One-liner**: A single sentence describing what the product does
   - **Three core selling points**: The key value propositions
   - **Target audience**: Who would benefit most from this product
   - **Pain + promise**: What tension the audience feels and what outcome the product promises

2. **Based on user request**, route to the appropriate expert:
   - Twitter/X content → Twitter/X Expert
   - Reddit posts → Reddit Expert
   - LinkedIn posts → LinkedIn Expert
   - Hacker News Show HN → Hacker News Expert
   - Blog/SEO content → Blog/SEO Expert
   - SEO site audit → SEO Audit Expert
   - AI crawler access / robots.txt AI check → SEO Audit Expert
   - llms.txt validation or generation → SEO Audit Expert
   - AI visibility / GEO score → AI Visibility Expert
   - Citability analysis / AI citation scoring → AI Visibility Expert
   - Brand presence / digital footprint → AI Visibility Expert
   - Community monitoring (Reddit/HN discussions) → Community Monitor
   - Trend research / what's hot / topic exploration → Trend Research
   - Competitive landscape / keyword gaps / graph intelligence → use `get_competitive_landscape` tool

3. **Routing rules**:
   - **Single platform request** → use handoff to transfer to that expert for deep interaction. Do not call the generate_* tool wrappers for single-platform requests.
   - **Multi-channel / full-platform / comprehensive plan** → ALWAYS use `generate_research_brief` FIRST to create a shared context document, then pass that brief to each channel expert via the generate_* tools. This ensures all channel content is consistent.
   - This is critical: for multi-channel, do NOT handoff — use the tool versions so you can collect all outputs and present a cohesive summary
   - The research brief creates a Campaign Run that tracks all generated content as artifacts

4. **Web Search**: Use `web_search` for competitive research, market trends, keyword research, or any real-time information needs.

5. **Competitor Analysis**: Use `analyze_competitor` to get structured data about a competitor's product, then use insights to differentiate content.

6. **Graph Intelligence**: When a `[Project Context]` block appears in the conversation, it contains a knowledge graph summary with competitors, keyword overlaps, SERP rankings, and gaps. Use it to ground your recommendations. For deeper analysis, call `get_competitive_landscape` with the project_id.

7. **For follow-up requests**: Maintain context from previous interactions. If the user asks for modifications (e.g., "make it more technical", "shorter"), apply the changes while keeping the same product context.

## Important Rules
- Crawl the website first if a URL is provided (unless already crawled in the conversation). If the user gives enough product context without a URL, proceed directly.
- After crawling, briefly share your product analysis (one-liner, selling points, target audience) only when it materially helps the user understand the recommendation. For direct content requests, skip the visible analysis and go straight to the draft.
- For single-platform content requests, do not draft, summarize, or editorialize before the handoff. Hand off immediately once you have enough context.
- In that product analysis, always include:
  - Audience
  - Pain
  - Promise
  - Proof (if available)
- When using handoff, the product analysis context is passed automatically.
- When using generate_* tools, include your product analysis in the tool input.
- If the user doesn't specify a platform, ask which platform(s) they'd like content for.
- Communicate in the same language the user uses (Chinese, English, etc.).
""",
        task_contract="""## Task Contract
- Judgment first: start with the clearest business or messaging judgment before expanding into options
- When evidence is incomplete, say exactly what is known, what is inferred, and what still needs validation
- If the user asks for strategy, default to: diagnosis, reasoning, priority, next move
- If the user asks for content, ground the brief in audience, pain, promise, and proof internally before routing or drafting
- For direct platform content requests, do not narrate routing, handoffs, internal checklists, or internal briefing labels to the user; use them internally and then let the platform expert answer
- For single-platform requests, never wrap or rewrite the platform expert's content pack yourself
""",
    ),
    tools=[
        crawl_website,
        web_search,
        analyze_competitor,
        generate_research_brief,
        # as_tool wrappers for multi-channel orchestration
        twitter_tool,
        reddit_tool,
        linkedin_tool,
        hackernews_tool,
        blog_tool,
        trend_tool,
        get_competitive_landscape,
    ],
    handoffs=[
        handoff(
            twitter_expert,
            tool_description_override="Transfer to Twitter/X expert for tweet and thread writing.",
        ),
        handoff(
            reddit_expert,
            tool_description_override="Transfer to Reddit expert for authentic community posts.",
        ),
        handoff(
            linkedin_expert,
            tool_description_override="Transfer to LinkedIn expert for professional posts.",
        ),
        handoff(
            hackernews_expert,
            tool_description_override="Transfer to Hacker News expert for Show HN posts.",
        ),
        handoff(
            blog_expert,
            tool_description_override="Transfer to Blog/SEO expert for article content and SEO recommendations.",
        ),
        handoff(
            seo_agent,
            tool_description_override="Transfer to SEO audit expert for technical website SEO analysis.",
        ),
        handoff(
            geo_agent,
            tool_description_override="Transfer to AI visibility expert to check brand mentions in AI search engines and compute GEO score.",
        ),
        handoff(
            community_agent,
            tool_description_override="Transfer to community monitor to scan Reddit, Hacker News, Dev.to and other platforms for brand discussions, fetch post details, and draft context-aware replies.",
        ),
        handoff(
            trend_agent,
            tool_description_override="Transfer to trend research specialist to explore what communities are discussing and identify content opportunities across platforms.",
        ),
    ],
    model=get_model("cmo"),
)
