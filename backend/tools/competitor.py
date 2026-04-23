from agents import function_tool

from opencmo.tools.crawl import fetch_url_content


@function_tool
async def analyze_competitor(url: str) -> str:
    """Crawl a competitor's website and return structured product intelligence.

    Returns product name, tagline, key features, pricing info, and target audience
    extracted from the page content.

    Args:
        url: The competitor's website URL.
    """
    try:
        content, _source = await fetch_url_content(
            url,
            max_chars=8000,
            tavily_extract_depth="advanced",
        )

        report = f"""## Competitor Analysis: {url}

### Raw Content (for AI analysis)
{content}

### Instructions for CMO Agent
Based on the above content, extract and present:
- **Product Name**: The name of the product
- **Tagline**: Their main value proposition in one sentence
- **Key Features**: Top 3-5 features or capabilities
- **Pricing**: Any pricing information found (or "Not found on page")
- **Target Audience**: Who this product is aimed at
- **Positioning**: How they position themselves in the market

Then compare with our product to identify differentiation opportunities."""

        return report
    except Exception as e:
        return f"Failed to analyze competitor at {url}: {e}"
