import json

from langgraph.graph import END
from langchain_core.messages import HumanMessage, SystemMessage
from src.graph.state import State
from src.llm import llm


# source가 꼭 필요할까...? 어떤 출력값이길 원하는거지???
MODERATOR_2_SYSTEM_PROMPT = """
사용자의 질문을 분석해서 아래 JSON만 반환하세요. 설명 없이.

분석 항목:
1. intent_metadata: 벡터 DB 검색에 사용할 필터
   - doc_type: 질문에 대한 답변 래퍼런스 카테고리 (다음 중 선택: "법령", "법령해석례", "판례")
   - source: 참고할 출처 (파악 가능할 때만)
2. is_definitive: 확답을 요구하는 질문인지 여부
   - True 예시: "~이 맞나요?", "반드시 ~해야 하나요?", "~가 100% 맞죠?" "답변에 대해 책임을 질 수 있어요?", # fewshot prompting
   - False 예시: "~에 대해 알려주세요", "~는 어떻게 하나요?"
3. needs_link: 사용자가 링크/출처/참고자료를 요청했는지 여부

응답 형식 (JSON만):
{
  "intent_metadata": {"doc_type": "법령"},
  "is_definitive": False,
  "needs_link": False
}
"""

_FALLBACK_MSG_M2 = (
    "해당 질문은 명확한 확답을 드리기 어렵습니다.\n"
    "상황과 조건에 따라 답변이 달라질 수 있어요.\n"
    "더 구체적인 상황을 설명해주시면 더 도움이 될 수 있습니다."
)

def intent_understanding(state: State) -> dict:
    '''
    <소개>
    LLM으로 사용자의 질문 의도 및 확답을 요구하는 질문을 차단하기 위한 moderator2 노드의 함수입니다.
    (1) 확답 질문 차단
    (2) 메타데이터 추출
    
    <args>
    - State

    <output>
    - State의 요소를 다음과 같이 업데이트합니다.
        - 'is_definitive' : 확답을 요구하는 경우가 존재한다면 
        'messages' : 민감한 정보가 있는 경우, 어떤 류의 민감정보가 포함되어 있는지를 출력하고, 이를 포함하지 않도록 안내하는 str을 저장
    '''
    
    user_input = state['user_input']

    response = llm.invoke([
        SystemMessage(content=MODERATOR_2_SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ])

    # LLM이 코드블록으로 감쌀 경우를 대비한 전처리
    raw = response.content.strip().strip('```json').strip('```').strip()
    
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # 파싱 실패 시 안전한 기본값 사용
        result = {"intent_metadata": {'doc_type' : None}, "is_definitive": False, "needs_link": False}

    # PDF 2-C: 확답 질문 → Fallback END
    if result.get('is_definitive', False):  # >>> 이 조건문 변경해야할 수도 있음... (캥기는 부분이 있는데..) >>> result['is_definitive']로 하면되는..?
        return {
            'is_definitive': True,
            'fallback_message': _FALLBACK_MSG_M2
        }

    return {
        'is_definitive': False,
        'intent_metadata': result.get('intent_metadata', {}),  # PDF 2-B: Retrieval 메타데이터
        'needs_link': result.get('needs_link', False)
    }

### 2. 조건부 엣지 함수
def route_after_intent_understanding(state: State) -> str:
    '''
    <소개>
    moderator_2 노드의 조건부 엣지 함수
    
    <기능>
    - is_definitive 값에 따라 다음 노드 결정
        - True : 확답을 요구하고 있음 -> 경고 메시지 출력 및 END 노드 이동 (fall back)
        - False : 확답을 요구하고 있지 않음 -> retrieval로 이동
    '''

    if state['is_definitive']:
        print(state['fallback_message'])

    return END if state['is_definitive'] else 'query_summary'
