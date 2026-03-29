from pathlib import Path
from typing import Any

from app.services.tools.base import Tool


class FileReaderTool(Tool):
    name = "file_reader"
    description = "Read local file content from an explicit path."

    async def run(self, **kwargs: Any) -> Any:
        path = kwargs.get("path")
        if not path:
            raise ValueError("path is required")
        data = Path(path).read_text(encoding="utf-8")
        return {"path": path, "content": data[:4000]}
