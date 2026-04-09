"""사이드바 컴포넌트.

글래스모피즘 스타일의 사이드바. 네비게이션, 새 채팅, 대화 목록을 표시한다.
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
    # 로고 + 타이틀
    st.markdown(
      '<div style="padding: 0.5rem 0 0.25rem;">'
      '<span style="font-size: 1.5rem; '
      'filter: drop-shadow(0 2px 4px rgba(0,154,204,0.2));">📋</span> '
      '<span style="font-size: 1.15rem; font-weight: 600; '
      'color: #009ACC; letter-spacing: -0.02em;">'
      "아이고 청년</span></div>",
      unsafe_allow_html=True,
    )
    st.caption("AI 기반 부동산 계약 조항 검토 서비스")

    st.divider()

    # 네비게이션 항목 (레퍼런스 스타일)
    st.markdown(
      '<div class="nav-item"><span class="nav-icon">✏️</span> 새 채팅</div>',
      unsafe_allow_html=True,
    )

    st.markdown(
      '<div style="height: 0.25rem;"></div>',
      unsafe_allow_html=True,
    )

    if st.button("＋ 새 채팅", use_container_width=True, type="primary"):
      create_chat()
      st.session_state.consent_given = False
      needs_consent = True

    conversations = st.session_state.get("conversations", [])

    if conversations:
      st.markdown(
        '<p style="font-size: 0.75rem; color: #8A9BAD; '
        'font-weight: 600; text-transform: uppercase; '
        'letter-spacing: 0.05em; margin: 1rem 0 0.5rem;">'
        "이전 대화</p>",
        unsafe_allow_html=True,
      )
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

    # 하단 정보
    st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)
    st.divider()
    st.caption("저희 서비스는 직접적인 법적 자문이 아닌 단순 조언을 위한 정보 제공을 목적으로 합니다. 중요한 결정 전에 반드시 전문가와 상담하시기 바랍니다.")

  return needs_consent
