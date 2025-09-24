import os
import requests
import streamlit as st

# -----------------------
# 안전한 API 엔드포인트 설정 (환경변수 > secrets > 기본값)
# -----------------------
API = os.getenv("API_URL", "http://127.0.0.1:8000")
try:
    if "API_URL" in st.secrets:  # secrets.toml 있을 때만 사용
        API = st.secrets["API_URL"]
except Exception:
    pass

# -----------------------
# 페이지 & 테마 설정
# -----------------------
st.set_page_config(page_title="MyBank 추천 서비스", page_icon="🏦", layout="wide")

PRIMARY = "#0059b3"     # 은행 톤의 블루
ACCENT  = "#1a73e8"     # 포인트 블루
BG      = "#f7f9fc"     # 밝은 배경

st.markdown(
    f"""
    <style>
      .stApp {{
        background: {BG};
      }}
      .bank-header {{
        display:flex; align-items:center; gap:12px;
        padding: 10px 0 4px 0; 
      }}
      .bank-logo {{
        font-size: 28px; line-height: 1;
      }}
      .bank-title {{
        font-weight: 800; font-size: 26px; color: {PRIMARY};
      }}
      .card {{
        background: white;
        border: 1px solid #e6e9ef;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
      }}
      .product-title {{
        font-weight: 700; font-size: 18px; color: #111827;
      }}
      .subtle {{
        color:#6b7280; font-size: 13px;
      }}
      .pill {{
        display:inline-block; padding: 2px 10px; border-radius: 999px;
        background: {ACCENT}; color:white; font-size: 12px; margin-left:6px;
      }}
      .cta-btn button {{
        background:{PRIMARY} !important; color:white !important; border-radius:10px !important;
        border:0 !important;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# 헤더
# -----------------------
st.markdown(
    """
    <div class="bank-header">
      <div class="bank-logo">🏦</div>
      <div class="bank-title">MyBank 추천 서비스</div>
    </div>
    <div class="subtle">고객님을 위한 맞춤형 금융·콘텐츠 추천</div>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# 사용자 정보 (간단 카드)
# -----------------------
with st.container():
    col1, col2, col3 = st.columns([1.4, 1, 1])
    with col1:
        st.markdown('<div class="card">👤 <b>사용자</b><br><span class="subtle">ID를 입력해 주세요</span></div>', unsafe_allow_html=True)
    with col2:
        user_id = st.text_input(" ", value="u001", label_visibility="collapsed")
    with col3:
        st.write("") ; st.write("")
        fetch = st.button("추천 가져오기", use_container_width=True)

# -----------------------
# 추천 가져오기 → /choose
# -----------------------
if fetch:
    try:
        r = requests.post(f"{API}/choose", json={"user_id": user_id})
        r.raise_for_status()
        data = r.json()
        st.session_state["arm"] = data.get("arm", "A")
        st.session_state["candidates"] = data.get("items", [])
        st.success(f"추천이 도착했어요! (전략: {st.session_state['arm']})")
    except Exception as e:
        st.error(f"API 오류: {e}")

# -----------------------
# 후보(상품) 노출 — 카드 UI
# -----------------------
if "candidates" in st.session_state and st.session_state["candidates"]:
    st.markdown("### 🔎 추천 상품")
    cols = st.columns(3)
    for i, item in enumerate(st.session_state["candidates"]):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="card">
                  <div class="product-title">💡 {item}<span class="pill">추천</span></div>
                  <div class="subtle">맞춤형 혜택을 확인해 보세요.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # 선택 즉시 업데이트 (버튼형)
            key = f"choose_{i}"
            if st.button("이 상품 선택", key=key, use_container_width=True):
                payload = {
                    "user_id": user_id,
                    "arm": st.session_state.get("arm", "A"),
                    "reward": 1.0,
                    "meta": {"choice": item},
                }
                try:
                    resp = requests.post(f"{API}/update", json=payload, timeout=10)
                    resp.raise_for_status()
                    st.session_state["last_choice"] = item
                    st.success(f"선택이 기록됐어요. 감사합니다 🙏")
                except Exception as e:
                    st.error(f"업데이트 실패: {e}")

# -----------------------
# 최근 선택 알림
# -----------------------
if st.session_state.get("last_choice"):
    st.info(f"최근 선택: **{st.session_state['last_choice']}**  | 전략: **{st.session_state.get('arm','A')}**")
