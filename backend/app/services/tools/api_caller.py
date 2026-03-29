from typing import Any

import httpx

from app.services.tools.base import Tool


class APICallerTool(Tool):
    name = "api_caller"
    description = "Call arbitrary HTTP APIs with a method/url payload."

    async def run(self, **kwargs: Any) -> Any:
        method = kwargs.get("method", "GET").upper()
        url = kwargs.get("url")
        payload = kwargs.get("payload")
        headers = kwargs.get("headers")
        if not url:
            raise ValueError("url is required")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.request(method, url, json=payload, headers=headers)
        return {"status_code": response.status_code, "data": response.text[:4000]}
