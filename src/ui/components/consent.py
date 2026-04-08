"""개인정보 수집·이용 동의 팝업.

새 채팅 시작 시 동의하지 않으면 채팅 입력을 비활성화한다.
"""

from __future__ import annotations

import streamlit as st

_CONSENT_TEXT = """
### 개인정보 수집·이용 동의

본 서비스는 입력하신 임대차계약서 및 질문 내용을 AI 분석 목적으로만 사용합니다.

**수집 항목**: 업로드된 계약서 텍스트, 채팅 질문 내용
**이용 목적**: 부동산 특약 추천 및 법령 정보 제공
**보유 기간**: 세션 종료 시 즉시 삭제 (별도 저장하지 않음)

> 본 서비스는 법적 조언을 제공하지 않으며,
> 정보 제공 목적으로만 운영됩니다.
""".strip()


@st.dialog("개인정보 수집·이용 동의", width="large")
def show_consent_dialog() -> None:
  """개인정보 동의 다이얼로그를 표시한다."""
  st.markdown(_CONSENT_TEXT)
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
