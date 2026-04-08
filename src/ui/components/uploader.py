"""PDF 업로드 컴포넌트.

임대차계약서 PDF를 업로드하면 텍스트를 추출하여 반환한다.
"""

from __future__ import annotations

import streamlit as st
from pypdf import PdfReader


def extract_text_from_pdf(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> str:
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


def render_uploader() -> str | None:
  """PDF 업로드 위젯을 렌더링한다.

  Returns:
    추출된 텍스트. 업로드가 없거나 실패 시 None.
  """
  uploaded = st.file_uploader(
    "임대차계약서 PDF 업로드",
    type=["pdf"],
    help="계약서 PDF를 업로드하면 내용을 분석합니다.",
    key="pdf_uploader",
  )
  if uploaded is None:
    return None

  with st.spinner("PDF에서 텍스트를 추출하고 있습니다..."):
    text = extract_text_from_pdf(uploaded)

  if not text:
    st.warning("PDF에서 텍스트를 추출할 수 없습니다. 스캔된 이미지 PDF는 아직 지원하지 않습니다.")
    return None

  with st.expander("추출된 계약서 내용 미리보기", expanded=False):
    st.text(text[:2000] + ("..." if len(text) > 2000 else ""))

  return text
