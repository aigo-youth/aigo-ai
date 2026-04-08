"""채팅 UI 컴포넌트.

대화 이력 렌더링, 사용자 입력, 웰컴 화면을 담당한다.
"""

from __future__ import annotations

import streamlit as st

from src.ui.session import get_current_chat
from src.ui.styles import welcome_html

_DISCLAIMER = "이 내용은 법적 조언이 아닌 정보 제공 목적입니다."

# 웰컴 화면에서 클릭 가능한 예시 질문 목록
_EXAMPLE_QUESTIONS = [
  "보증금 반환 특약을 추가하고 싶어요",
  "집주인이 수리를 안 해줘요",
  "전세 계약 중도 해지 시 권리가 궁금해요",
  "계약서에 원상복구 특약이 있는데 문제없어?",
]


def render_chat_history() -> None:
  """현재 채팅의 메시지 이력을 렌더링한다."""
  chat = get_current_chat()
  if chat is None:
    return

  messages = chat.get("messages", [])

  if not messages:
    # 웰컴 화면
    st.markdown(welcome_html(), unsafe_allow_html=True)
    return

  for msg in messages:
    with st.chat_message(msg["role"]):
      st.markdown(msg["content"])
      if msg["role"] == "assistant":
        st.caption(f"_{_DISCLAIMER}_")


def render_chat_input(on_submit: callable) -> None:
  """채팅 입력창을 렌더링한다.

  Args:
    on_submit: 사용자 입력 텍스트를 받는 콜백 함수.
  """
  if not st.session_state.get("consent_given", False):
    st.chat_input("개인정보 동의 후 이용할 수 있습니다.", disabled=True)
    return

  chat = get_current_chat()
  if chat is None:
    st.chat_input("새 채팅을 시작해주세요.", disabled=True)
    return

  # 예시 질문 버튼 (메시지가 없을 때만 표시)
  messages = chat.get("messages", [])
  if not messages:
    cols = st.columns(len(_EXAMPLE_QUESTIONS))
    for i, (col, q) in enumerate(zip(cols, _EXAMPLE_QUESTIONS)):
      with col:
        if st.button(
          q,
          key=f"example_{i}",
          use_container_width=True,
        ):
          on_submit(q)

  if prompt := st.chat_input("질문을 입력하세요..."):
    on_submit(prompt)
