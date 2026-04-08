"""Streamlit 메인 앱.

모든 UI 컴포넌트를 조립하고 파이프라인과 연결한다.
실행: `streamlit run src/ui/app.py`
"""

from __future__ import annotations

import streamlit as st

from src.ui.components.chat import render_chat_history, render_chat_input
from src.ui.components.consent import show_consent_dialog
from src.ui.components.sidebar import render_sidebar
from src.ui.components.uploader import render_uploader
from src.ui.session import add_message, get_current_chat, init_session

_DISCLAIMER = "이 내용은 법적 조언이 아닌 정보 제공 목적입니다."


# ── 로딩 애니메이션 ──────────────────────────────────────


def dot_loading_html() -> str:
  """3-dot 로딩 애니메이션 HTML을 반환한다."""
  return """
<style>
.dot-loading-wrap { padding: 8px 0; }
.dot-loading { display: inline-flex; gap: 4px; align-items: center; }
.dot-loading span {
  width: 8px; height: 8px; border-radius: 50%;
  background-color: #888; animation: dot-bounce 1.4s infinite ease-in-out both;
}
.dot-loading span:nth-child(1) { animation-delay: -0.32s; }
.dot-loading span:nth-child(2) { animation-delay: -0.16s; }
@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.4); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}
.dot-disclaimer { font-size: 0.75rem; color: #999; margin-top: 8px; }
</style>
<div class="dot-loading-wrap">
  <div class="dot-loading"><span></span><span></span><span></span></div>
  <div class="dot-disclaimer">저희는 직접적인 법적 자문을 제공하지 않습니다</div>
</div>
"""


# ── 파이프라인 stub ──────────────────────────────────────


def run_pipeline(query: str, input_type: str = "text") -> str:
  """파이프라인을 실행하여 응답을 생성한다.

  TODO: 실제 LangGraph 파이프라인이 완성되면 교체.

  Args:
    query: 사용자 질의 또는 추출된 계약서 텍스트.
    input_type: "text" 또는 "pdf".

  Returns:
    생성된 응답 텍스트.
  """
  import time
  time.sleep(2)  # TODO: 파이프라인 완성 후 제거
  # stub 응답 — 파이프라인 완성 전까지 사용
  if input_type == "pdf":
    return (
      "계약서 내용을 확인했습니다. "
      "아직 파이프라인이 구현 중이라 상세 분석은 준비 중입니다.\n\n"
      "궁금한 점이 있으시면 질문해주세요!"
    )
  return (
    f'"{query}"에 대해 분석 중입니다.\n\n'
    "아직 파이프라인이 구현 중이라 답변 생성이 준비 중입니다.\n\n"
    "곧 법령 근거와 특약 추천을 제공할 예정입니다."
  )


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
  )

  init_session()

  # 사이드바
  needs_consent = render_sidebar()

  # 동의 팝업 트리거
  if needs_consent:
    show_consent_dialog()

  # 메인 영역
  chat = get_current_chat()

  if chat is None:
    # 채팅이 없을 때 안내
    st.markdown("## 부동산 특약 도우미")
    st.markdown("왼쪽 사이드바에서 **+ 새 채팅**을 눌러 시작하세요.")
    return

  if not st.session_state.consent_given:
    st.info("개인정보 수집·이용에 동의해야 서비스를 이용할 수 있습니다.")
    return

  # PDF 업로드 (확장 가능 영역)
  with st.expander("계약서 PDF 업로드", expanded=False):
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
