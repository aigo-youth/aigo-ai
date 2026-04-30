import re
from app.graph.state import State
from langgraph.graph import END



SENSITIVE_PATTERNS = [
    (r'(?<!\d)\d{6}[\s-]?[1-4]\d{6}(?!\d)', "주민등록번호"),
    (r'(?<!\d)\d{6}[\s-]?[5-8]\d{6}(?!\d)', "외국인등록번호"),
    (r'(?<!\d)\d{3}[\s-]?\d{2}[\s-]?\d{5}(?!\d)', "사업자등록번호"),   
    (r'(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b(?!\d)', "카드번호"),
    (r'(?<!\d)\d{3,6}[-\s]?\d{2,6}[-\s]?\d{5,8}(?!\d)', "계좌번호"),                # 계좌번호 범위가 넓어서 오탐의 위험은 존재.
    (r'(?<!\d)(010|011|016|017|018|019)[-\s]?\d{3,4}[-\s]?\d{4}(?!\d)', "전화번호")

    ### 유의사항
    # '-'가 없는 주민등록번호/외국인등록번호와 계좌번호는 상황이 겹칠 수도 있다.
    # 그래서 경고문구를 출력할 때, 중복 태깅하도록 코드를 짤 예정
]

### 1. 함수 설정: 민감정보 유무를 확인 및 State update해주는 함수
# def detecting_private_sensitive_data(state: State) -> dict: # 원래 사용하려던 함수명
def check_sensitive_info(state: State) -> dict:
    '''
    <소개>
    개인정보 혹은 민감한 정보를 찾아내는 check_sensitive_info(moderator1)의 노드 함수입니다.

    <args>
    - State

    <output>
    - State의 요소를 다음과 같이 업데이트합니다.
        - 'is_sensitive' : 민감한 정보가 있으면 True, 없으면 False로 업데이트
        - 'messages' : 민감한 정보가 있는 경우, 어떤 류의 민감정보가 포함되어 있는지를 출력하고, 이를 포함하지 않도록 안내하는 str을 저장
    '''

    user_input = state['user_input']
    detected = []

    for pattern, label in SENSITIVE_PATTERNS:
        if re.search(pattern, user_input):
            detected.append(label)

    if detected:
        types_str = ", ".join(detected)
        warning_msg = (
            "<<주의>>\n"
            f"{types_str}로 보이는 정보가 포함되어 있습니다.\n"
            "민감한 정보가 포함되어있지 않나요? 다시 한 번 확인해주세요!\n\n"
            "예) 주민등록번호, 계좌번호와 같은 개인정보/민감정보는 보안상 입력하지 않도록 권장합니다."
        )

        return {
                'is_sensitive': True,
                'fallback_message': warning_msg 
            }   # detected 된 경우 return값 설정

    return {'is_sensitive': False}  # detected 안 된 경우 == 정상 통과



### 2. moderator_1의 조건부 엣지 함수
def route_after_check_sensitive_info(state: State) -> str:
    '''
    <소개>
    moderator_1 노드의 조건부 엣지 함수
    
    <기능>
    - is_sensitive 값에 따라 다음 노드 결정
        - True : 민감정보를 포함하고 있음 -> 경고 메시지 출력 및 END 노드 이동 (fall back)
        - False : 민감정보를 포함하고 있지 않음 -> moderator2로 이동
    '''

    if state['is_sensitive']:
        print(state['fallback_message'])

    return END if state['is_sensitive'] else 'intent_understanding'