from app.pdf_graph.state import PDF_State
from app.llm import llm
from langchain_core.messages import HumanMessage, SystemMessage

EXTRACTOR_PROMPT = """
당신은 부동산 계약 서류 분석 전문가입니다.
사용자가 계약서 string을 입력하면, 특약 사항만 추출하여 출력해주세요.

추출 대상: 특약(special_term)
- 주어진 Content 내에서 특약 부분만을 남김
- 특약 내용 중에 띄어쓰기 혹은 맞춤법 오류가 있는 경우 수정.
- 동일한 번호의 특약 조항인 경우에는 사이의 줄바꿈(\n)을 공백(" ")으로 변경한다.
- 마지막 조항을 제외한 각 조항 끝에는 줄바꿈(\n)을 꼭 달아줄 것. (마지막 조항 끝에는 줄바꿈을 달지 않는다.)

*주의 사항*
부동산 특약 내용이 없는 경우, "특약 내용을 확인할 수 없습니다. 직접 입력해주세요."를 출력합니다.

응답 형식 (str 형식):
1. 1번조항내용.\n2. 2번조항내용.\n(이하 생략)
"""

def extracting_special_terms(state: PDF_State) -> dict:
    '''
    <소개>
    계약서 내용을 마스킹처리한 string 데이터를 받아, 특약 사항을 추출해내는 LLM 연계 함수입니다.
    
    <args>
    - masked_text: 마스킹 에이전트가 전달해준 마스킹된 string을 받습니다.

    <output>
    - State의 요소를 다음과 같이 업데이트합니다.
        - 'special_term': masked_text에서 추출한 내용을 하나의 string으로 이어 담습니다.
                        결과값은 다음과 같이 하나의 string으로 생성되어야 합니다: "1. 1번조항내용.\n2. 2번조항내용.\n..."
    '''
    
    masked_texts = state['masked_text']

    response = llm.invoke([
        SystemMessage(content=EXTRACTOR_PROMPT),
        HumanMessage(content=masked_texts)
    ])

    texts = response.content.strip()
    # 혹시 모를 코드블록 제거
    if texts.startswith("```"):
        texts = texts.split("```")[1].strip()

    return {'special_term': texts}