from firecrawl import FirecrawlApp
from src.utils.config import Settings
from src.utils.logging import logger
from typing import List, Dict, Any, Optional
import asyncio
import time

def extract_search_results(result: Any) -> List[Dict[str, Any]]:
    """Robustly extract web search result items from any Firecrawl SDK or REST response format.
    Handles v2 ('web'), v1 ('data'), direct lists, and SDK object attributes.
    """
    if not result:
        return []

    raw_data = result
    if hasattr(result, "model_dump"):
        try:
            raw_data = result.model_dump()
        except Exception:
            pass
    elif hasattr(result, "to_dict"):
        try:
            raw_data = result.to_dict()
        except Exception:
            pass

    items = []

    if isinstance(raw_data, list):
        items = raw_data
    elif isinstance(raw_data, dict):
        if "web" in raw_data and isinstance(raw_data["web"], list):
            items = raw_data["web"]
        elif "data" in raw_data:
            data = raw_data["data"]
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                if "web" in data and isinstance(data["web"], list):
                    items = data["web"]
                elif "results" in data and isinstance(data["results"], list):
                    items = data["results"]
        elif "results" in raw_data and isinstance(raw_data["results"], list):
            items = raw_data["results"]
    elif hasattr(raw_data, "web") and isinstance(getattr(raw_data, "web"), list):
        items = getattr(raw_data, "web")
    elif hasattr(raw_data, "data"):
        data = getattr(raw_data, "data")
        if isinstance(data, list):
            items = data
        elif hasattr(data, "web") and isinstance(getattr(data, "web"), list):
            items = getattr(data, "web")
        elif isinstance(data, dict) and "web" in data and isinstance(data["web"], list):
            items = data["web"]

    normalized = []
    for item in items:
        if hasattr(item, "model_dump"):
            try:
                item = item.model_dump()
            except Exception:
                pass
        elif hasattr(item, "to_dict"):
            try:
                item = item.to_dict()
            except Exception:
                pass

        if isinstance(item, dict):
            url = item.get("url") or item.get("link") or item.get("target")
            if url:
                title = item.get("title") or item.get("name") or ""
                description = item.get("description") or item.get("snippet") or item.get("markdown") or item.get("content") or ""
                normalized.append({
                    "url": str(url),
                    "title": str(title),
                    "description": str(description),
                    "markdown": item.get("markdown"),
                    "position": item.get("position")
                })
        elif hasattr(item, "url") or hasattr(item, "link"):
            url = getattr(item, "url", None) or getattr(item, "link", None)
            if url:
                title = getattr(item, "title", "") or getattr(item, "name", "") or ""
                description = getattr(item, "description", "") or getattr(item, "snippet", "") or getattr(item, "markdown", "") or ""
                normalized.append({
                    "url": str(url),
                    "title": str(title),
                    "description": str(description),
                    "markdown": getattr(item, "markdown", None),
                    "position": getattr(item, "position", None)
                })

    return normalized

def extract_scrape_content(result: Any) -> str:
    """Extract markdown text from any Firecrawl scrape response format."""
    if not result:
        return ""
    if isinstance(result, str):
        return result

    raw_data = result
    if hasattr(result, "model_dump"):
        try:
            raw_data = result.model_dump()
        except Exception:
            pass
    elif hasattr(result, "to_dict"):
        try:
            raw_data = result.to_dict()
        except Exception:
            pass

    if isinstance(raw_data, dict):
        if "markdown" in raw_data and raw_data["markdown"]:
            return str(raw_data["markdown"])
        if "data" in raw_data:
            data = raw_data["data"]
            if isinstance(data, str):
                return data
            if isinstance(data, dict):
                if data.get("markdown"):
                    return str(data["markdown"])
                if data.get("content"):
                    return str(data["content"])
        if "content" in raw_data and raw_data["content"]:
            return str(raw_data["content"])

    if hasattr(raw_data, "markdown") and getattr(raw_data, "markdown"):
        return str(getattr(raw_data, "markdown"))
    if hasattr(raw_data, "data"):
        data = getattr(raw_data, "data")
        if isinstance(data, str):
            return data
        if hasattr(data, "markdown") and getattr(data, "markdown"):
            return str(getattr(data, "markdown"))

    return ""

class WebTools:
    def __init__(self, settings: Settings):
        self.app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)

    async def _execute_with_retry_and_timeout(self, coro_func, deadline: Optional[float] = None, max_retries: int = 2, timeout: float = 20.0):
        attempt = 0
        backoff = 2.0

        while attempt < max_retries:
            if deadline and time.time() >= deadline:
                raise TimeoutError("Overall deadline exceeded before tool execution.")

            attempt += 1
            try:
                return await asyncio.wait_for(coro_func(), timeout=timeout)
            except asyncio.TimeoutError as te:
                logger.warning(f"Tool call timed out on attempt {attempt}/{max_retries}: {te}")
                if attempt >= max_retries:
                    raise TimeoutError(f"Tool call exceeded timeout after {max_retries} attempts.") from te
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "403" in error_msg or "unauthorized" in error_msg.lower():
                    logger.error(f"Non-retryable tool error: {e}")
                    raise

                logger.warning(f"Tool transient error on attempt {attempt}/{max_retries}: {e}")
                if attempt >= max_retries:
                    raise

                if deadline and time.time() >= deadline:
                    raise TimeoutError("Overall deadline exceeded during tool retry backoff.")

                sleep_time = min(backoff, (deadline - time.time()) if deadline else backoff)
                if sleep_time <= 0:
                    raise TimeoutError("Overall deadline exceeded.")

                await asyncio.sleep(sleep_time)
                backoff *= 2.0

    async def search(self, query: str, limit: int = 5, deadline: Optional[float] = None, timeout: float = 20.0) -> List[Dict[str, Any]]:
        """Search the web using Firecrawl with deadline, timeout, and robust multi-format response parsing."""
        async def _call():
            logger.info(f"Searching for: {query}")
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: self.app.search(query, limit=limit))

        try:
            raw_result = await self._execute_with_retry_and_timeout(_call, deadline=deadline, timeout=timeout)

            # Safe logging of response structure
            if raw_result is not None:
                if isinstance(raw_result, dict):
                    keys = list(raw_result.keys())
                    logger.debug(f"Firecrawl raw response type: dict, keys: {keys}")
                elif isinstance(raw_result, list):
                    logger.debug(f"Firecrawl raw response type: list, len: {len(raw_result)}")
                else:
                    logger.debug(f"Firecrawl raw response type: {type(raw_result).__name__}")
            else:
                logger.debug("Firecrawl raw response is None")

            items = extract_search_results(raw_result)

            if raw_result and not items:
                logger.warning(f"Firecrawl returned response structure but 0 items could be extracted. Response type: {type(raw_result).__name__}")
            else:
                logger.info(f"Firecrawl search returned {len(items)} items for query: '{query}'")

            return items
        except Exception as e:
            logger.error(f"Firecrawl search failed: {e}")
            return []

    async def scrape(self, url: str, deadline: Optional[float] = None, timeout: float = 20.0) -> str:
        """Scrape a page using Firecrawl with deadline, timeout, and robust response parsing."""
        async def _call():
            logger.info(f"Scraping URL: {url}")
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: self.app.scrape_url(url, formats=['markdown']))

        try:
            raw_result = await self._execute_with_retry_and_timeout(_call, deadline=deadline, timeout=timeout)
            content = extract_scrape_content(raw_result)
            if not content:
                logger.warning(f"Firecrawl scrape returned empty content for URL: {url}")
            else:
                logger.info(f"Firecrawl scraped {len(content)} characters for URL: {url}")
            return content
        except Exception as e:
            logger.error(f"Firecrawl scrape failed for {url}: {e}")
            return ""

    async def batch_scrape(self, urls: List[str], deadline: Optional[float] = None) -> List[str]:
        """Scrape multiple pages in parallel with deadline."""
        tasks = [self.scrape(url, deadline=deadline) for url in urls]
        return await asyncio.gather(*tasks)
