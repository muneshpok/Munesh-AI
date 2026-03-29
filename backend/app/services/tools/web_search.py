from typing import Any

import httpx

from app.services.tools.base import Tool


class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web for lightweight instant answers."

    async def run(self, **kwargs: Any) -> Any:
        query = kwargs.get("query", "")
        if not query:
            return {"results": []}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
            )
            data = response.json()
        return {
            "abstract": data.get("AbstractText", ""),
            "related_topics": data.get("RelatedTopics", [])[:5],
        }
