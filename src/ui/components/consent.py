"""개인정보 수집·이용 동의 팝업.

새 채팅 시작 시 동의하지 않으면 채팅 입력을 비활성화한다.
「개인정보 보호법」 제30조 기반 개인정보 처리방침 연동.
"""

from __future__ import annotations

import streamlit as st

_CONSENT_TEXT = """
### 개인정보 수집·이용 동의

「개인정보 보호법」 제15조제1항제1호에 따라 아래와 같이 개인정보를 수집·이용하고자 합니다.

| 항목 | 내용 |
|------|------|
| **수집 항목** | 업로드된 임대차계약서 텍스트, 채팅 질문 내용, 직접 작성한 특약 텍스트 |
| **수집 목적** | 부동산 특약 추천, 관련 법령·판례 정보 제공, AI 기반 답변 생성 |
| **보유 기간** | **세션 종료 시 즉시 삭제** (별도 서버 저장 없음) |

- 위 동의를 거부할 권리가 있으며, 거부 시 서비스 이용이 제한됩니다.
- 자세한 사항은 아래 **개인정보 처리방침**을 확인해 주세요.
""".strip()

_PRIVACY_POLICY_PATH = "docs/privacy_policy.md"


def _load_privacy_policy() -> str:
  """개인정보 처리방침 전문을 로드한다."""
  from pathlib import Path
  policy_path = Path(_PRIVACY_POLICY_PATH)
  if policy_path.exists():
    return policy_path.read_text(encoding="utf-8")
  return "(개인정보 처리방침 파일을 찾을 수 없습니다.)"


@st.dialog("개인정보 수집·이용 동의", width="large")
def show_consent_dialog() -> None:
  """개인정보 동의 다이얼로그를 표시한다."""
  st.markdown(_CONSENT_TEXT)

  with st.expander("개인정보 처리방침 전문 보기"):
    st.markdown(_load_privacy_policy())

  st.divider()

  col_agree, col_disagree = st.columns(2)

  with col_agree:
    if st.button("동의합니다", use_container_width=True, type="primary"):
      st.session_state.consent_given = True
      st.rerun()

  with col_disagree:
    if st.button("동의하지 않습니다", use_container_width=True):
      st.session_state.consent_given = False
      st.session_state.current_chat_id = None
      # 방금 만든 빈 채팅 제거
      st.session_state.conversations = [
        c for c in st.session_state.conversations
        if c["messages"]
      ]
      st.rerun()
