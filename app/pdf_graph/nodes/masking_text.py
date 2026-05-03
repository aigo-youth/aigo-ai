import ast
import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import llm
from app.pdf_graph.state import PDF_State

MASKING_PROMPT = '''계약서 텍스트에서 민감한 개인 정보(이름, 주민등록번호, 전화번호, 계좌번호, 서명 등)를 모두 찾으세요.
이 텍스트는 OCR 처리된 것으로 띄어쓰기 오류, 문자 오인식 등이 있을 수 있습니다.
value는 반드시 원본 텍스트에 등장하는 형태 그대로 추출하세요.
예를 들어 원본에 "홍길 동"으로 되어 있으면 "홍길 동"으로 반환하세요.

다른 설명이나 주석, 코드펜스 없이 반드시 아래 JSON 배열 형식으로만 답하세요.
키와 문자열 값은 모두 반드시 큰따옴표(")로 감싸야 합니다.
민감 정보가 없으면 빈 배열 []만 반환하세요.

[
  {"type": "이름", "value": "홍길동"},
  {"type": "전화번호", "value": "010-1234-5678"}
]
'''


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    inner = text[3:]
    if inner.lower().startswith("json"):
        inner = inner[4:]
    closing = inner.rfind("```")
    if closing != -1:
        inner = inner[:closing]
    return inner.strip()


def _extract_array(text: str) -> str:
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return text
    return text[start : end + 1]


def _parse_sensitive_items(content: str) -> list[dict]:
    body = _extract_array(_strip_code_fence(content))

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(body)
        except (ValueError, SyntaxError) as exc:
            raise ValueError(f"LLM 응답을 JSON 으로 파싱하지 못했습니다: {content!r}") from exc

    if not isinstance(parsed, list):
        raise ValueError(f"LLM 응답이 배열이 아닙니다: {parsed!r}")

    items: list[dict] = []
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        value = entry.get("value")
        if isinstance(value, str) and value:
            items.append({"type": entry.get("type", ""), "value": value})
    return items


def masking_text(state: PDF_State) -> dict:
    response = llm.invoke([
        SystemMessage(content=MASKING_PROMPT),
        HumanMessage(content=state['extracted_text']),
    ])

    sensitive_items = _parse_sensitive_items(response.content)

    masked_texts = state['extracted_text']
    seen: set[str] = set()
    for item in sorted(sensitive_items, key=lambda i: len(i['value']), reverse=True):
        value = item['value']
        if value in seen:
            continue
        seen.add(value)
        masked_texts = masked_texts.replace(value, '*' * len(value))

    return {'masked_text': masked_texts}
