"""사이드바 컴포넌트.

새 채팅 생성 버튼과 기존 대화 목록을 렌더링한다.
"""

from __future__ import annotations

import streamlit as st

from src.ui.session import create_chat, switch_chat


def render_sidebar() -> bool:
  """사이드바를 렌더링한다.

  Returns:
    True이면 새 채팅이 생성되어 동의 팝업이 필요함을 의미한다.
  """
  needs_consent = False

  with st.sidebar:
    st.title("부동산 특약 도우미")
    st.caption("임대차계약 특약 추천 챗봇")

    st.divider()

    if st.button("+ 새 채팅", use_container_width=True, type="primary"):
      create_chat()
      if not st.session_state.consent_given:
        needs_consent = True

    st.divider()

    conversations = st.session_state.get("conversations", [])
    if conversations:
      st.markdown("##### 대화 목록")
      for conv in conversations:
        is_active = conv["id"] == st.session_state.get("current_chat_id")
        label = conv["title"]
        if st.button(
          label,
          key=f"chat_{conv['id']}",
          use_container_width=True,
          type="primary" if is_active else "secondary",
        ):
          switch_chat(conv["id"])
          st.rerun()

  return needs_consent
