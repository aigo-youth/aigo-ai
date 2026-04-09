"""채팅 UI 컴포넌트.

대화 이력 렌더링, 사용자 입력, 웰컴 화면을 담당한다.
"""

from __future__ import annotations

import re

import streamlit as st

from src.ui.components.uploader import extract_text_from_pdf
from src.ui.session import get_current_chat
from src.ui.styles import welcome_html


def _linkify(text: str) -> str:
  """마크다운 링크가 아닌 bare URL을 클릭 가능한 마크다운 링크로 변환한다."""
  return re.sub(
    r'(?<!\]\()(?<!\()(https?://[^\s\)>\]]+)',
    r'[\1](\1)',
    text,
  )

_DISCLAIMER = "저희는 직접적인 법적 자문을 제공하지 않습니다. 제공된 정보는 일반적인 안내를 위한 것이며, 구체적인 상황에 따라 다르게 적용될 수 있습니다. 중요한 결정 전에 반드시 전문가와 상담하시기 바랍니다."

_EXAMPLE_QUESTIONS = [
  "보증금 반환 조항을 검토해 주세요",
  "집주인이 수리를 안 해줘요",
  "전세 계약 중도 해지 시 권리가 궁금해요",
  "계약서에 원상복구 조항이 있는데 문제없어?",
]


def _inject_chat_input(text: str) -> None:
  """JavaScript로 st.chat_input textarea에 텍스트를 주입한다."""
  escaped = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
  js = f"""
  <script>
  (function() {{
    function fill() {{
      const ta = parent.document.querySelector(
        '[data-testid="stChatInput"] textarea'
      );
      if (!ta) {{ setTimeout(fill, 100); return; }}
      const nativeSet = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      ).set;
      nativeSet.call(ta, `{escaped}`);
      ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
      ta.focus();
    }}
    fill();
  }})();
  </script>
  """
  st.components.v1.html(js, height=0, width=0)


@st.dialog("📄 계약서 PDF 업로드")
def _pdf_upload_dialog() -> None:
  """PDF 업로드 다이얼로그."""
  st.markdown(
    '<p style="font-size:0.85rem;color:#64748B;">'
    "임대차계약서 PDF를 업로드하세요.</p>",
    unsafe_allow_html=True,
  )
  uploaded = st.file_uploader(
    "PDF 파일 선택",
    type=["pdf"],
    key="_dialog_pdf_uploader",
    label_visibility="collapsed",
  )
  if uploaded is None:
    return

  with st.spinner("PDF에서 텍스트를 추출하고 있습니다..."):
    text = extract_text_from_pdf(uploaded)

  if not text:
    st.warning(
      "PDF에서 텍스트를 추출할 수 없습니다. "
      "스캔된 이미지 PDF는 아직 지원하지 않습니다.",
    )
    return

  with st.expander("추출된 내용 미리보기", expanded=False):
    preview = text[:2000] + ("..." if len(text) > 2000 else "")
    st.text(preview)

  if st.button("분석 시작", type="primary", use_container_width=True):
    st.session_state["_pdf_extracted_text"] = text
    st.rerun()


def _inject_attach_button_js() -> None:
  """숨겨진 Streamlit 버튼을 트리거하는 HTML + 버튼을 하단 바에 주입한다."""
  js = """
  <script>
  (function() {
    const pd = parent.document;

    function setup() {
      // 1) 본문의 원래 Streamlit ＋ 버튼 — 매번 숨기기
      pd.querySelectorAll('button').forEach(function(b) {
        if (b.textContent.trim() === '＋' && b.id !== 'attach-plus-btn') {
          var c = b.closest('[data-testid="stElementContainer"]');
          if (c && !c.closest('[data-testid="stBottom"]')) {
            c.style.cssText = 'position:absolute!important;width:1px!important;height:1px!important;overflow:hidden!important;opacity:0!important;';
          }
        }
      });

      // 2) 하단 바 버튼은 한 번만 생성
      if (pd.querySelector('#attach-plus-btn')) return;

      var chatInput = pd.querySelector('[data-testid="stChatInput"]');
      if (!chatInput) { setTimeout(setup, 300); return; }

      var inner = chatInput.parentElement;
      if (inner) inner.style.position = 'relative';

      // 채팅 입력 높이에 맞춘 + 버튼
      var inputH = chatInput.offsetHeight || 48;
      var btn = document.createElement('button');
      btn.id = 'attach-plus-btn';
      btn.textContent = '+';
      btn.title = '계약서 PDF 첨부';
      btn.style.cssText = [
        'position:absolute',
        'left:0',
        'top:50%',
        'transform:translateY(-50%)',
        'width:52px',
        'height:' + inputH + 'px',
        'border-radius:10px',
        'border:1.5px solid rgba(0,0,0,0.10)',
        'background:rgba(255,255,255,0.85)',
        'backdrop-filter:blur(12px)',
        'font-size:1.25rem',
        'font-weight:300',
        'color:#009ACC',
        'cursor:pointer',
        'display:flex',
        'align-items:center',
        'justify-content:center',
        'transition:all 0.2s ease',
        'z-index:100',
        'box-shadow:0 1px 4px rgba(0,0,0,0.06)',
        'padding:0',
        'line-height:1'
      ].join(';');

      btn.addEventListener('mouseenter', function() {
        btn.style.background = 'rgba(0,154,204,0.08)';
        btn.style.borderColor = '#009ACC';
        btn.style.transform = 'translateY(-50%) scale(1.03)';
      });
      btn.addEventListener('mouseleave', function() {
        btn.style.background = 'rgba(255,255,255,0.85)';
        btn.style.borderColor = 'rgba(0,0,0,0.10)';
        btn.style.transform = 'translateY(-50%)';
      });

      btn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        pd.querySelectorAll('button').forEach(function(b) {
          if (b.textContent.trim() === '＋' && b.id !== 'attach-plus-btn') {
            b.click();
          }
        });
      });

      inner.appendChild(btn);
    }

    setup();
    new MutationObserver(function() { setup(); }).observe(
      pd.body, { childList: true, subtree: true }
    );
  })();
  </script>
  """
  st.components.v1.html(js, height=0, width=0)


def render_chat_history() -> None:
  """현재 채팅의 메시지 이력을 렌더링한다."""
  chat = get_current_chat()
  if chat is None:
    return

  messages = chat.get("messages", [])

  if not messages:
    st.markdown(welcome_html(), unsafe_allow_html=True)
    return

  for msg in messages:
    with st.chat_message(msg["role"]):
      content = _linkify(msg["content"]) if msg["role"] == "assistant" else msg["content"]
      st.markdown(content)
      if msg["role"] == "assistant":
        st.caption(f"_{_DISCLAIMER}_")


def render_chat_input(
  on_submit: callable,
  on_pdf_submit: callable | None = None,
) -> None:
  """채팅 입력창을 렌더링한다.

  Args:
    on_submit: 사용자 텍스트 입력 콜백.
    on_pdf_submit: PDF 추출 텍스트 콜백. None이면 첨부 버튼 미표시.
  """
  if not st.session_state.get("consent_given", False):
    st.chat_input("개인정보 동의 후 이용할 수 있습니다.", disabled=True)
    return

  chat = get_current_chat()
  if chat is None:
    st.chat_input("새 채팅을 시작해주세요.", disabled=True)
    return

  # PDF 다이얼로그 결과 처리
  pdf_text = st.session_state.pop("_pdf_extracted_text", None)
  if pdf_text and on_pdf_submit:
    on_pdf_submit(pdf_text)
    st.rerun()
    return

  # + 첨부 버튼: 마커 + 숨겨진 Streamlit 버튼 + JS로 하단 바에 HTML 버튼 주입
  if on_pdf_submit:
    st.markdown(
      '<span class="attach-trigger-marker"></span>',
      unsafe_allow_html=True,
    )
    if st.button("＋", key="_attach_btn"):
      _pdf_upload_dialog()
    _inject_attach_button_js()

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
          st.session_state["_prefill_question"] = q
          st.rerun()

  # 예시 질문 클릭 시 chat_input textarea에 텍스트 주입
  prefill = st.session_state.pop("_prefill_question", None)
  if prefill:
    _inject_chat_input(prefill)

  if prompt := st.chat_input("질문을 입력하세요..."):
    on_submit(prompt)
