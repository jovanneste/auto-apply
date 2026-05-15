import json
from typing import AsyncGenerator


def sse_event(event_type: str, **kwargs) -> str:
    payload = {"type": event_type, **kwargs}
    return f"data: {json.dumps(payload)}\n\n"


async def sse_stream(generator: AsyncGenerator[str, None]):
    """Wrap an async generator of SSE strings for StreamingResponse."""
    async for chunk in generator:
        yield chunk
