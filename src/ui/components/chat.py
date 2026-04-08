"""채팅 UI 컴포넌트.

대화 이력 렌더링, 사용자 입력, 로딩 상태, 면책 문구를 담당한다.
"""

from __future__ import annotations

import streamlit as st

from src.ui.session import add_message, get_current_chat

_DISCLAIMER = "이 내용은 법적 조언이 아닌 정보 제공 목적입니다."

_WELCOME_MESSAGE = (
  "안녕하세요! 부동산 특약 도우미입니다.\n\n"
  "임대차계약서를 업로드하거나 질문을 입력해주세요.\n\n"
  "예시:\n"
  '- "보증금 반환 특약을 추가하고 싶어요"\n'
  '- "집주인이 수리를 안 해줘요"\n'
  '- 계약서 PDF를 업로드하여 검토 요청'
)


def render_chat_history() -> None:
  """현재 채팅의 메시지 이력을 렌더링한다."""
  chat = get_current_chat()
  if chat is None:
    return

  messages = chat.get("messages", [])

  if not messages:
    with st.chat_message("assistant"):
      st.markdown(_WELCOME_MESSAGE)
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

  if prompt := st.chat_input("질문을 입력하세요..."):
    on_submit(prompt)
