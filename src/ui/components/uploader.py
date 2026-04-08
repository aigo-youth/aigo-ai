"""PDF 업로드 컴포넌트.

임대차계약서 PDF를 업로드하면 텍스트를 추출하여 반환한다.
"""

from __future__ import annotations

import streamlit as st
from pypdf import PdfReader


def extract_text_from_pdf(
  uploaded_file: st.runtime.uploaded_file_manager.UploadedFile,
) -> str:
  """업로드된 PDF에서 텍스트를 추출한다.

  Args:
    uploaded_file: Streamlit file_uploader가 반환한 파일 객체.

  Returns:
    추출된 텍스트. 실패 시 빈 문자열.
  """
  try:
    reader = PdfReader(uploaded_file)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()
  except Exception as e:
    st.error(f"PDF 텍스트 추출 실패: {e}")
    return ""


def _file_identity(
  uploaded: st.runtime.uploaded_file_manager.UploadedFile,
) -> str:
  """업로드된 파일의 고유 식별자를 생성한다.

  Args:
    uploaded: Streamlit file_uploader가 반환한 파일 객체.

  Returns:
    파일명과 크기를 조합한 식별 문자열.
  """
  return f"{uploaded.name}_{uploaded.size}"


def render_uploader() -> str | None:
  """PDF 업로드 위젯을 렌더링한다.

  새 PDF가 업로드되면 이전 파일의 처리 상태를 자동으로 리셋한다.

  Returns:
    추출된 텍스트. 업로드가 없거나 실패 시 None.
  """
  st.markdown(
    '<p style="font-size: 0.85rem; color: #64748B; margin-bottom: 0.5rem;">'
    "임대차계약서 PDF를 드래그하거나 클릭하여 업로드하세요.</p>",
    unsafe_allow_html=True,
  )

  uploaded = st.file_uploader(
    "임대차계약서 PDF 업로드",
    type=["pdf"],
    help="계약서 PDF를 업로드하면 내용을 분석합니다.",
    key="pdf_uploader",
    label_visibility="collapsed",
  )
  if uploaded is None:
    # 파일이 제거되면 추적 상태도 초기화
    st.session_state.pop("_last_pdf_identity", None)
    return None

  # 새 파일 감지 시 이전 처리 플래그 리셋
  identity = _file_identity(uploaded)
  prev_identity = st.session_state.get("_last_pdf_identity")
  if prev_identity is not None and prev_identity != identity:
    chat_id = st.session_state.get("current_chat_id")
    if chat_id:
      st.session_state.pop(f"pdf_processed_{chat_id}", None)
      st.toast("새 계약서가 감지되어 이전 분석을 대체합니다.", icon="🔄")
  st.session_state["_last_pdf_identity"] = identity

  with st.spinner("PDF에서 텍스트를 추출하고 있습니다..."):
    text = extract_text_from_pdf(uploaded)

  if not text:
    st.warning(
      "PDF에서 텍스트를 추출할 수 없습니다. "
      "스캔된 이미지 PDF는 아직 지원하지 않습니다."
    )
    return None

  with st.expander("추출된 계약서 내용 미리보기", expanded=False):
    preview = text[:2000] + ("..." if len(text) > 2000 else "")
    st.text(preview)

  return text
