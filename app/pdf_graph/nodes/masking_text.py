from app.pdf_graph.state import PDF_State
from app.llm import llm
from langchain_core.messages import HumanMessage, SystemMessage
import json

# 세부주소(구까지만 나오게)도 마스킹을 할까???
MASKING_PROMPT = '''
계약서 텍스트에서 민감한 개인 정보(이름, 주민등록번호, 전화번호, 계좌번호, 서명 등)를 모두 찾으세요.
이 텍스트는 OCR 처리된 것으로 띄어쓰기 오류, 문자 오인식 등이 있을 수 있습니다.
value는 반드시 원본 텍스트에 등장하는 형태 그대로 추출하세요.
예를 들어 원본에 "홍길 동"으로 되어 있으면 "홍길 동"으로 반환하세요.

다른 설명은 포함하지 말고 반드시 아래 JSON 형식으로만 답하세요.
[
  {'type': '이름', 'value': '홍길동'},
  {'type': '전화번호', 'value': '010-1234-5678'}
]
'''

def masking_text(state: PDF_State) -> dict:

    response = llm.invoke([
        SystemMessage(content=MASKING_PROMPT),
        HumanMessage(content=state['extracted_text'])
    ])

    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1].strip().lstrip("json").strip()

    sensitive_items = json.loads(content)

    masked_texts = state['extracted_text']
    for item in sensitive_items:
        masked_texts = masked_texts.replace(item['value'], '*' * len(item['value']))

    return {'masked_text': masked_texts}