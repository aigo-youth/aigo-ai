"""Streamlit session_state 관리 모듈.

채팅 목록, 현재 대화, 개인정보 동의 상태 등
앱 전체에서 공유하는 상태를 초기화·조작한다.
"""

from __future__ import annotations

import uuid
from datetime import datetime

import streamlit as st


def init_session() -> None:
  """session_state 초기값을 설정한다. 이미 존재하면 건너뛴다."""
  defaults: dict = {
    "conversations": [],      # list[dict]: 전체 채팅 목록
    "current_chat_id": None,  # str | None: 활성 채팅 ID
    "consent_given": False,   # bool: 개인정보 동의 여부
    "is_loading": False,      # bool: 응답 대기 중
  }
  for key, value in defaults.items():
    if key not in st.session_state:
      st.session_state[key] = value


def create_chat() -> str:
  """새 채팅을 생성하고 current_chat_id를 갱신한다.

  Returns:
    생성된 채팅의 ID.
  """
  chat_id = uuid.uuid4().hex[:12]
  chat = {
    "id": chat_id,
    "title": "새 대화",
    "messages": [],
    "created_at": datetime.now().isoformat(),
  }
  st.session_state.conversations = [
    chat,
    *st.session_state.conversations,
  ]
  st.session_state.current_chat_id = chat_id
  return chat_id


def get_current_chat() -> dict | None:
  """현재 활성 채팅을 반환한다. 없으면 None."""
  chat_id = st.session_state.get("current_chat_id")
  if chat_id is None:
    return None
  for conv in st.session_state.conversations:
    if conv["id"] == chat_id:
      return conv
  return None


def add_message(role: str, content: str) -> None:
  """현재 채팅에 메시지를 추가한다.

  Args:
    role: "user" 또는 "assistant".
    content: 메시지 본문.
  """
  chat = get_current_chat()
  if chat is None:
    return
  chat["messages"] = [
    *chat["messages"],
    {"role": role, "content": content},
  ]
  # 첫 사용자 메시지로 채팅 제목 갱신
  if role == "user" and chat["title"] == "새 대화":
    chat["title"] = content[:30] + ("..." if len(content) > 30 else "")


def switch_chat(chat_id: str) -> None:
  """활성 채팅을 전환한다."""
  st.session_state.current_chat_id = chat_id
