import json
from app.graph.state import State
from app.llm import llm
from langchain_core.messages import HumanMessage, SystemMessage

### 질문 요지 추출(요약) + 질문자 요청 사항 요약 = 질문 전처리

REWRITE_PROMPT = """
당신은 질문을 요약해주는 챗봇입니다.
유사도 검색을 원활히 하기 위해 질문의 핵심을 파악하고,
질문자의 요청을 요약해주세요.

결과 출력은 반드시 json 형식으로 출력해주세요.
<결과 형식>
{
    "user_query" : str,
    "user_request" : str
}
"""

def query_summary(state: State) -> dict:
    user_input = state['user_input']
    last_chat = state.get('messages', [])[-1:]
            # 혹시나 짧은 input을 넣었을 경우,
            # 최소한 AI가 출력한 마지막 메시지가 무엇인지 파악하는 것이 문맥 파악에 좋을 듯.

    response = llm.invoke([
        SystemMessage(content=REWRITE_PROMPT),
        *last_chat,
        HumanMessage(content=user_input)
    ])

    raw = response.content.strip().strip('```json').strip('```').strip()
    
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"user_query": user_input, "user_request": ""}
    
    return {
        'user_query': result.get('user_query', ""),     # user_query는 유사도 검색을 위한 중요한 값
        'user_request': result.get('user_request', "")  # user_request는 generator에서 사용할 수 있을텐데,
                                                        # user_query와 user_request가 하나로 되어있는 것이 user_input이므로 우선 보류.
    }