"""Streamlit 메인 앱.

모든 UI 컴포넌트를 조립하고 파이프라인과 연결한다.
실행: `streamlit run src/ui/app.py`
"""

from __future__ import annotations

import streamlit as st

import logging

from src.graph import run_preformat, stream_formatter
from src.ui.components.chat import render_chat_history, render_chat_input
from src.ui.components.consent import show_consent_dialog
from src.ui.components.sidebar import render_sidebar
from src.ui.session import add_message, get_current_chat, init_session
from src.ui.styles import dot_loading_html, get_global_css, welcome_html

_DISCLAIMER = "저희는 직접적인 법적 자문을 제공하지 않습니다. 제공된 정보는 일반적인 안내를 위한 것이며, 구체적인 상황에 따라 다르게 적용될 수 있습니다. 중요한 결정 전에 반드시 전문가와 상담하시기 바랍니다."
_ERROR_MSG = "죄송합니다, 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

logger = logging.getLogger(__name__)


def _run_with_loading(query: str, placeholder) -> dict:
  """dot loading을 표시하면서 pre-format 파이프라인을 실행한다."""
  placeholder.markdown(dot_loading_html(), unsafe_allow_html=True)
  try:
    return run_preformat(query)
  except Exception:
    logger.exception("파이프라인 실행 중 오류 발생")
    return {"fallback_message": _ERROR_MSG}


# ── 메시지 처리 ──────────────────────────────────────────


def handle_user_message(prompt: str) -> None:
  """사용자 메시지를 처리하고 스트리밍으로 응답을 생성한다."""
  add_message("user", prompt)

  with st.chat_message("user"):
    st.markdown(prompt)

  with st.chat_message("assistant"):
    placeholder = st.empty()

    # 1) dot loading 표시 + pre-format 파이프라인 실행
    state = _run_with_loading(prompt, placeholder)

    # 2) fallback 경로 (민감 정보, 관련성 부족 등)
    fallback = state.get("fallback_message")
    if fallback:
      placeholder.markdown(fallback)
      response = fallback
    elif not state.get("final_answer"):
      placeholder.markdown(_ERROR_MSG)
      response = _ERROR_MSG
    else:
      # 3) dot loading 제거 후 formatter 스트리밍
      placeholder.empty()
      response = st.write_stream(stream_formatter(state))

    st.caption(f"_{_DISCLAIMER}_")

  add_message("assistant", response)
  st.rerun()


def handle_pdf_input(text: str) -> None:
  """PDF에서 추출된 텍스트를 스트리밍으로 파이프라인에 전달한다."""
  summary = f"[계약서 업로드됨] ({len(text)}자 추출)\n\n> {text[:200]}..."
  add_message("user", summary)

  with st.chat_message("user"):
    st.markdown(summary)

  with st.chat_message("assistant"):
    placeholder = st.empty()

    state = _run_with_loading(text, placeholder)

    fallback = state.get("fallback_message")
    if fallback:
      placeholder.markdown(fallback)
      response = fallback
    elif not state.get("final_answer"):
      placeholder.markdown(_ERROR_MSG)
      response = _ERROR_MSG
    else:
      placeholder.empty()
      response = st.write_stream(stream_formatter(state))

    st.caption(f"_{_DISCLAIMER}_")

  add_message("assistant", response)


# ── 메인 ─────────────────────────────────────────────────


def main() -> None:
  """Streamlit 앱 진입점."""
  st.set_page_config(
    page_title="아이고 청년",
    page_icon="📋",
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

  # 채팅 이력
  render_chat_history()

  # 입력창 (+ 버튼으로 PDF 첨부 포함)
  render_chat_input(
    on_submit=handle_user_message,
    on_pdf_submit=handle_pdf_input,
  )


if __name__ == "__main__":
  main()
