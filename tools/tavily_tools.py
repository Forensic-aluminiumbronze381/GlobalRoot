"""
Tavily Tools — Real-time web research, page reading, deep research, and crawling
"""
import requests

try:
    from tavily import TavilyClient
except Exception:
    TavilyClient = None

from config import TAVILY_API_KEY, TAVILY_BASE_URL, TAVILY_TIMEOUT


def web_research(query: str, depth: str = "advanced") -> str:
    clean_query = query.strip()
    if not clean_query:
        return "❌ Search query cannot be empty."

    if not TAVILY_API_KEY:
        return "❌ TAVILY_API_KEY is not set."

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": clean_query,
        "search_depth": depth if depth in {"basic", "advanced"} else "advanced",
        "max_results": 5,
        "include_answer": True,
        "include_raw_content": False,
    }

    try:
        response = requests.post(
            f"{TAVILY_BASE_URL}/search",
            json=payload,
            timeout=TAVILY_TIMEOUT,
        )
        response.raise_for_status()
    except Exception as exc:
        return f"❌ Tavily search failed: {type(exc).__name__}: {exc}"

    data = response.json()
    answer = (data.get("answer") or "").strip()
    results = data.get("results") or []

    lines = []
    if answer:
        lines.append("Summary:")
        lines.append(answer)

    if results:
        lines.append("")
        lines.append("Sources:")
        for index, result in enumerate(results[:5], start=1):
            title = (result.get("title") or "No title").strip()
            url = (result.get("url") or "No URL").strip()
            content = (result.get("content") or "No content").strip()
            lines.append(f"{index}. {title}")
            lines.append(f"URL: {url}")
            lines.append(f"Summary: {content[:500]}")

    if not lines:
        return "❌ Tavily search returned no results."

    return "\n".join(lines)


def read_page(url: str) -> str:
    clean_url = url.strip()
    if not clean_url:
        return "❌ URL cannot be empty."

    if not TAVILY_API_KEY:
        return "❌ TAVILY_API_KEY is not set."

    payload = {
        "api_key": TAVILY_API_KEY,
        "urls": [clean_url],
        "extract_depth": "advanced",
        "include_images": False,
    }

    try:
        response = requests.post(
            f"{TAVILY_BASE_URL}/extract",
            json=payload,
            timeout=TAVILY_TIMEOUT,
        )
        response.raise_for_status()
    except Exception as exc:
        return f"❌ Tavily page read failed: {type(exc).__name__}: {exc}"

    data = response.json()
    results = data.get("results") or []
    if not results:
        return "❌ Page content could not be retrieved."

    first = results[0]
    title = (first.get("title") or clean_url).strip()
    raw_content = (first.get("raw_content") or first.get("content") or "").strip()
    if not raw_content:
        return f"❌ Page was read but content was empty: {clean_url}"

    return f"Title: {title}\nURL: {clean_url}\n\n{raw_content[:12000]}"


def deep_research(query: str) -> str:
    """Tavily SDK advanced search — comprehensive, detailed research (15 sources)."""
    clean_query = query.strip()
    if not clean_query:
        return "❌ Research query cannot be empty."

    if not TAVILY_API_KEY:
        return "❌ TAVILY_API_KEY is not set."

    if TavilyClient is None:
        return (
            "❌ Tavily SDK is not installed.\n"
            "Install it with: pip install tavily-python"
        )

    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(
            query=clean_query,
            search_depth="advanced",
            max_results=15,
            include_answer=True,
            include_raw_content=False,
        )
    except Exception as exc:
        return f"❌ Tavily research failed: {type(exc).__name__}: {exc}"

    answer = response.get("answer")
    if answer:
        answer = answer.strip()
    results = response.get("results") or []

    lines = []
    if answer:
        lines.append("📋 Detailed Summary:")
        lines.append(answer)

    if results:
        lines.append("")
        lines.append(f"📚 {len(results)} Sources Found:")
        for index, result in enumerate(results[:15], start=1):
            title = (result.get("title") or "No title").strip()
            url = (result.get("url") or "No URL").strip()
            content = (result.get("content") or "No content").strip()
            lines.append(f"\n{index}. {title}")
            lines.append(f"   URL: {url}")
            lines.append(f"   Summary: {content[:350]}")

    if not lines:
        return "❌ Tavily research returned no results."

    return "\n".join(lines)


def crawl_page(url: str) -> str:
    """Tavily SDK crawl/extract — page crawling, links, and content.
    Note: Crawl may be invite-only; falls back to extract.
    """
    clean_url = url.strip()
    if not clean_url:
        return "❌ URL cannot be empty."

    if not TAVILY_API_KEY:
        return "❌ TAVILY_API_KEY is not set."

    if TavilyClient is None:
        return (
            "❌ Tavily SDK is not installed.\n"
            "Install it with: pip install tavily-python"
        )

    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        
        try:
            response = client.crawl(
                url=clean_url,
                max_depth=2,
                limit=20,
            )
            results = response.get("results") or []
        except Exception:
            response = client.extract(
                urls=[clean_url],
                include_images=False,
            )
            results = response.get("results") or []

        if not results:
            return "❌ Page crawl failed."

        first = results[0]
        title = (first.get("title") or clean_url).strip()
        raw_content = (first.get("raw_content") or first.get("content") or "").strip()
        links = first.get("links") or []

        lines = [f"📄 Title: {title}", f"🔗 URL: {clean_url}", ""]

        if raw_content:
            lines.append(f"📝 Content ({len(raw_content)} characters):")
            lines.append(raw_content[:8000])

        if links:
            lines.append("")
            lines.append(f"🔗 Links on Page ({len(links)} total):")
            for link in links[:15]:
                lines.append(f"  - {link}")

        return "\n".join(lines)
    except Exception as exc:
        return f"❌ Tavily crawl failed: {type(exc).__name__}: {exc}"
