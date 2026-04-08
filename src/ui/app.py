"""Streamlit 메인 앱.

모든 UI 컴포넌트를 조립하고 파이프라인과 연결한다.
실행: `streamlit run src/ui/app.py`
"""

from __future__ import annotations

import streamlit as st

import logging

from src.graph import run as run_graph
from src.ui.components.chat import render_chat_history, render_chat_input
from src.ui.components.consent import show_consent_dialog
from src.ui.components.sidebar import render_sidebar
from src.ui.components.uploader import render_uploader
from src.ui.session import add_message, get_current_chat, init_session
from src.ui.styles import dot_loading_html, get_global_css, welcome_html

_DISCLAIMER = "이 내용은 법적 조언이 아닌 정보 제공 목적입니다."
_ERROR_MSG = "죄송합니다, 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

logger = logging.getLogger(__name__)


def run_pipeline(query: str, input_type: str = "text") -> str:
  """LangGraph 파이프라인을 실행하여 응답을 생성한다.

  Args:
    query: 사용자 질의 또는 추출된 계약서 텍스트.
    input_type: "text" 또는 "pdf".

  Returns:
    생성된 응답 텍스트.
  """
  try:
    result = run_graph(query)
    return (
      result.get("fallback_message")
      or result.get("final_answer")
      or _ERROR_MSG
    )
  except Exception:
    logger.exception("파이프라인 실행 중 오류 발생")
    return _ERROR_MSG


# ── 메시지 처리 ──────────────────────────────────────────


def handle_user_message(prompt: str) -> None:
  """사용자 메시지를 처리하고 응답을 생성한다."""
  add_message("user", prompt)

  with st.chat_message("user"):
    st.markdown(prompt)

  with st.chat_message("assistant"):
    placeholder = st.empty()
    placeholder.markdown(dot_loading_html(), unsafe_allow_html=True)
    response = run_pipeline(prompt, input_type="text")
    placeholder.markdown(response)
    st.caption(f"_{_DISCLAIMER}_")

  add_message("assistant", response)


def handle_pdf_input(text: str) -> None:
  """PDF에서 추출된 텍스트를 파이프라인에 전달한다."""
  summary = f"[계약서 업로드됨] ({len(text)}자 추출)\n\n> {text[:200]}..."
  add_message("user", summary)

  with st.chat_message("user"):
    st.markdown(summary)

  with st.chat_message("assistant"):
    placeholder = st.empty()
    placeholder.markdown(dot_loading_html(), unsafe_allow_html=True)
    response = run_pipeline(text, input_type="pdf")
    placeholder.markdown(response)
    st.caption(f"_{_DISCLAIMER}_")

  add_message("assistant", response)


# ── 메인 ─────────────────────────────────────────────────


def main() -> None:
  """Streamlit 앱 진입점."""
  st.set_page_config(
    page_title="부동산 특약 도우미",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
  )

  # 글로벌 CSS 적용
  st.markdown(get_global_css(), unsafe_allow_html=True)

  init_session()

  # 사이드바
  needs_consent = render_sidebar()

  # 동의 팝업 트리거
  if needs_consent:
    show_consent_dialog()

  # 메인 영역
  chat = get_current_chat()

  if chat is None:
    # 채팅이 없을 때 — 풀 웰컴 화면
    st.markdown(welcome_html(), unsafe_allow_html=True)
    return

  if not st.session_state.consent_given:
    st.info("개인정보 수집·이용에 동의해야 서비스를 이용할 수 있습니다.")
    return

  # PDF 업로드
  with st.expander("📄 계약서 PDF 업로드", expanded=False):
    pdf_text = render_uploader()
    if pdf_text and f"pdf_processed_{chat['id']}" not in st.session_state:
      st.session_state[f"pdf_processed_{chat['id']}"] = True
      handle_pdf_input(pdf_text)
      st.rerun()

  # 채팅 이력
  render_chat_history()

  # 입력창
  render_chat_input(on_submit=handle_user_message)


if __name__ == "__main__":
  main()
