import json
from typing import Any


def format_sse_event(event: str, data: dict[str, Any]) -> str:
    """SSE 이벤트 문자열 생성

    Args:
      event: 이벤트 종류 (예: "token", "title", "citation", "done", "error").
      data: 이벤트 페이로드. JSON 직렬화 가능해야 함

    Returns:
      'event: <name>\\ndata: <json>\\n\\n' 형식의 문자열
    """
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"
