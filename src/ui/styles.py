"""글로벌 CSS 스타일 모듈.

Liquid Glass 디자인 시스템 — #009ACC 기반 미니멀 글래스.
"""

from __future__ import annotations


def get_global_css() -> str:
  """앱 전체에 적용할 CSS를 반환한다."""
  return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── 리셋 & 기본 ─────────────────────────── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* 배경 — 연한 뉴트럴 그레이 */
[data-testid="stApp"] {
  background: #F2F4F6;
  background-attachment: fixed;
}

[data-testid="stAppViewContainer"] {
  background: transparent;
}

/* ── 메인 콘텐츠 글래스 카드 ─────────────── */
.main .block-container {
  max-width: 960px;
  margin: 1.5rem auto;
  padding: 2rem 2.5rem 6rem;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(40px) saturate(1.4);
  -webkit-backdrop-filter: blur(40px) saturate(1.4);
  border: 1px solid rgba(255, 255, 255, 0.85);
  border-radius: 20px;
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.04),
    0 8px 24px rgba(0, 0, 0, 0.06);
  min-height: calc(100vh - 6rem);
}

.main [data-testid="stVerticalBlock"] {
  background: transparent;
}

/* ── 사이드바 (Liquid Glass) ───────────────── */
section[data-testid="stSidebar"] {
  background: rgba(255, 255, 255, 0.78) !important;
  backdrop-filter: blur(40px) saturate(1.4) !important;
  -webkit-backdrop-filter: blur(40px) saturate(1.4) !important;
  border-right: 1px solid rgba(0, 0, 0, 0.06) !important;
  display: flex !important;
  opacity: 1 !important;
  width: 280px !important;
  min-width: 280px !important;
  transform: none !important;
}

section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
  background: transparent !important;
}

/* 사이드바 닫기 버튼 숨김 */
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
button[kind="headerNoPadding"] {
  display: none !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdown"] h1 {
  font-size: 1.2rem;
  font-weight: 600;
  color: #1B2838;
  letter-spacing: -0.02em;
}

[data-testid="stSidebar"] .stCaption {
  color: #8A9BAD;
  font-size: 0.78rem;
}

/* 사이드바 새 채팅 버튼 */
[data-testid="stSidebar"] button[kind="primary"] {
  background: #009ACC;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.88rem;
  transition: all 0.2s ease;
  box-shadow: 0 1px 4px rgba(0, 154, 204, 0.2);
}
[data-testid="stSidebar"] button[kind="primary"]:hover {
  background: #008ABB;
  box-shadow: 0 2px 8px rgba(0, 154, 204, 0.3);
  transform: translateY(-0.5px);
}

/* 사이드바 대화 목록 버튼 */
[data-testid="stSidebar"] button[kind="secondary"] {
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  color: #3A4F5F;
  font-weight: 400;
  font-size: 0.85rem;
  text-align: left;
  transition: all 0.2s ease;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
  background: rgba(0, 154, 204, 0.05);
  border-color: rgba(0, 154, 204, 0.15);
}

/* 사이드바 네비게이션 아이템 */
.nav-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 0.7rem;
  border-radius: 8px;
  color: #3A4F5F;
  font-size: 0.88rem;
  font-weight: 500;
  cursor: default;
  transition: background 0.15s ease;
  margin-bottom: 0.1rem;
}
.nav-item:hover {
  background: rgba(0, 154, 204, 0.05);
}
.nav-icon {
  font-size: 1rem;
  width: 1.2rem;
  text-align: center;
  opacity: 0.7;
}

/* ── 채팅 메시지 ─────────────────────────── */
[data-testid="stChatMessage"] {
  padding: 1rem 1.25rem;
  border-radius: 14px;
  margin-bottom: 0.4rem;
  border: none;
}

/* 어시스턴트 메시지 — 글래스 */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
}

/* 사용자 메시지 */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
  background: #009ACC;
  border: none;
  box-shadow: 0 1px 6px rgba(0, 154, 204, 0.2);
}

/* 사용자 메시지 텍스트 흰색 */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p {
  color: #FFFFFF !important;
}

/* 아바타 스타일 */
[data-testid="chatAvatarIcon-assistant"] {
  background: #009ACC !important;
}

[data-testid="chatAvatarIcon-user"] {
  background: rgba(255, 255, 255, 0.3) !important;
}

/* 메시지 텍스트 */
[data-testid="stChatMessage"] p {
  font-size: 0.93rem;
  line-height: 1.65;
  color: #1B2838;
}

/* 어시스턴트 메시지 내 링크 */
[data-testid="stChatMessage"] a {
  color: #007AB8;
  text-decoration: none;
  border-bottom: 1px solid rgba(0, 122, 184, 0.3);
  transition: all 0.15s ease;
}
[data-testid="stChatMessage"] a:hover {
  color: #009ACC;
  border-bottom-color: #009ACC;
}

/* ── 채팅 입력 ───────────────────────────── */
[data-testid="stChatInput"] {
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.7) !important;
  backdrop-filter: blur(20px);
  transition: all 0.2s ease;
}
[data-testid="stChatInput"]:focus-within {
  border-color: #009ACC;
  box-shadow: 0 0 0 3px rgba(0, 154, 204, 0.1);
}

[data-testid="stChatInput"] textarea {
  font-size: 0.93rem;
  background: transparent !important;
}

/* ── 면책 문구 ───────────────────────────── */
[data-testid="stChatMessage"] .stCaption p {
  font-size: 0.72rem !important;
  color: #8A9BAD !important;
}

/* ── 웰컴 화면 ───────────────────────────── */
.welcome-card {
  text-align: center;
  padding: 3rem 2rem 2rem;
  max-width: 700px;
  margin: 0 auto;
}
.welcome-mascot {
  font-size: 5rem;
  line-height: 1.2;
  margin-bottom: 0.75rem;
  filter: drop-shadow(0 4px 12px rgba(0, 154, 204, 0.15));
}
.welcome-card h2 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1B2838;
  margin-bottom: 0.4rem;
  letter-spacing: -0.03em;
}
.welcome-card .welcome-sub {
  color: #5C7080;
  font-size: 0.95rem;
  line-height: 1.6;
  margin-bottom: 0;
  font-weight: 400;
}

/* 카테고리 pill */
.category-grid {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 2.5rem;
}
.category-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 20px;
  padding: 0.5rem 1rem;
  font-size: 0.82rem;
  font-weight: 500;
  color: #3A4F5F;
  cursor: default;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}
.category-pill:hover {
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transform: translateY(-0.5px);
}
.category-icon {
  font-size: 0.9rem;
}

/* ── PDF 업로더 ──────────────────────────── */
[data-testid="stExpander"] {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 12px;
  overflow: hidden;
}
[data-testid="stExpander"] summary {
  font-size: 0.88rem;
  font-weight: 500;
  color: #3A4F5F;
}

[data-testid="stFileUploader"] {
  border-radius: 10px;
}
[data-testid="stFileUploader"] section {
  border: 1.5px dashed rgba(0, 154, 204, 0.2);
  border-radius: 10px;
  padding: 1.5rem;
  transition: border-color 0.2s ease;
}
[data-testid="stFileUploader"] section:hover {
  border-color: #009ACC;
}

/* ── 동의 다이얼로그 ────────────────────── */
[data-testid="stDialog"] {
  border-radius: 18px;
  backdrop-filter: blur(24px);
}
[data-testid="stDialog"] [data-testid="stTable"] {
  font-size: 0.85rem;
}

/* ── 로딩 애니메이션 ────────────────────── */
.dot-loading-wrap {
  padding: 12px 0;
}
.dot-loading {
  display: inline-flex;
  gap: 5px;
  align-items: center;
}
.dot-loading span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #009ACC;
  animation: dot-bounce 1.4s infinite ease-in-out both;
}
.dot-loading span:nth-child(1) { animation-delay: -0.32s; }
.dot-loading span:nth-child(2) { animation-delay: -0.16s; }
@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.4); opacity: 0.3; }
  40% { transform: scale(1); opacity: 1; }
}
.dot-disclaimer {
  font-size: 0.72rem;
  color: #8A9BAD;
  margin-top: 8px;
}

/* ── 유틸리티 ────────────────────────────── */
.divider-subtle {
  border: none;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  margin: 1rem 0;
}

/* Streamlit 기본 요소 정리 */
#MainMenu { visibility: hidden; }
header[data-testid="stHeader"] {
  background: transparent !important;
}
footer { visibility: hidden; }

/* info 배너 */
[data-testid="stAlert"] {
  border-radius: 12px;
  font-size: 0.88rem;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

/* 버튼 기본 스타일 */
.stButton > button {
  border-radius: 10px;
  font-weight: 500;
  transition: all 0.2s ease;
}

/* 사이드바 내 divider */
[data-testid="stSidebar"] hr {
  border-color: rgba(0, 0, 0, 0.06);
}

/* ── 첨부 + 버튼 (채팅 입력 왼쪽) ────────── */
/* 마커 span 숨기기 */
[data-testid="stElementContainer"]:has(.attach-trigger-marker) {
  position: absolute !important;
  width: 0 !important;
  height: 0 !important;
  overflow: hidden !important;
}
/* 마커 바로 다음의 Streamlit 버튼 컨테이너 숨기기 */
[data-testid="stElementContainer"]:has(.attach-trigger-marker)
  + [data-testid="stElementContainer"] {
  position: absolute !important;
  width: 0 !important;
  height: 0 !important;
  overflow: hidden !important;
  opacity: 0 !important;
}
/* iframe (JS 주입용) 컨테이너도 숨기기 */
[data-testid="stElementContainer"]:has(.attach-trigger-marker)
  + [data-testid="stElementContainer"]
  + [data-testid="stElementContainer"] {
  position: absolute !important;
  width: 0 !important;
  height: 0 !important;
  overflow: hidden !important;
}

[data-testid="stBottom"] [data-testid="stChatInput"] {
  margin-left: 58px;
}
</style>
"""


def dot_loading_html() -> str:
  """3-dot 로딩 애니메이션 HTML을 반환한다."""
  return """
<div class="dot-loading-wrap">
  <div class="dot-loading"><span></span><span></span><span></span></div>
  <div class="dot-disclaimer">답변을 생성하고 있습니다...</div>
</div>
"""


def welcome_html() -> str:
  """웰컴 화면 HTML을 반환한다."""
  return """
<div class="welcome-card">
  <div class="welcome-mascot">📋</div>
  <h2>무엇을 도와드릴까요?</h2>
  <p class="welcome-sub">
    임대차계약서를 분석하고, 관련 법령과 판례를 기반으로<br>
    계약 조항을 검토해 드립니다.
  </p>
  <div class="category-grid">
    <div class="category-pill">
      <span class="category-icon">📋</span> 조항 검토
    </div>
    <div class="category-pill">
      <span class="category-icon">⚖️</span> 분쟁 대응
    </div>
    <div class="category-pill">
      <span class="category-icon">📄</span> 계약서 검토
    </div>
    <div class="category-pill">
      <span class="category-icon">🔍</span> 법령 조회
    </div>
  </div>
</div>
"""
