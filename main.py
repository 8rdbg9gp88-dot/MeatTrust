import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import urllib.parse
import plotly.express as px
import base64

# ==========================================
# 1. 디자인 및 기본 설정
# ==========================================
st.set_page_config(page_title="Meatrust 도축 정보 시스템", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { color: #1B2A47; font-weight: bold; font-size: 1.1rem; }
    .stTabs [aria-selected="true"] { border-bottom-color: #E11D48 !important; color: #E11D48 !important; }
    .stButton>button { background-color: #1B2A47; color: white; border-radius: 8px; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #E11D48; color: white; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 시네마틱 인트로 화면 (로컬 배경 이미지)
# ==========================================
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

if "intro_done" not in st.session_state:
    # 깃허브에 bg_image.jpg 가 정상 업로드 되어있어야 작동함!
    bg_img_base64 = get_base64_of_bin_file("bg_image.jpg")
    
    if bg_img_base64:
        bg_css = f"url('data:image/jpeg;base64,{bg_img_base64}')"
    else:
        # 사진을 못 찾으면 짙은 네이비 단색으로 대체
        bg_css = "none"

    st.markdown(f"""
        <div style="background-color: #1B2A47; background-image: linear-gradient(rgba(27, 42, 71, 0.6), rgba(27, 42, 71, 0.6)), {bg_css};
            background-size: cover; background-position: center; height: 85vh; border-radius: 20px; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; text-align: center; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.2);">
            <h1 style='font-size: 5rem; margin-bottom: 10px; color: white; font-weight: 900; letter-spacing: 2px;'>Meatrust</h1>
            <p style='font-size: 1.5rem; color: #E0E0E0; margin-bottom: 30px;'>투명한 데이터가 만드는 신뢰, 전국 축산물 AI 매칭 플랫폼</p>
            <div style="background-color: rgba(225, 29, 72, 0.9); padding: 10px 30px; border-radius: 30px; font-weight: bold; font-size: 1.2rem;">소비자와 바이어를 위한 안심 조회 시스템</div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Meatrust 시스템 입장하기", use_container_width=True):
            st.session_state.intro_done = True
            st.rerun()
    st.stop()

# ==========================================
# 3. 100% 리얼 공공데이터 통신 (가짜 데이터 완전 삭제)
# ==========================================
try:
    MAFRA_KEY = st.secrets.get("MAFRA_API_KEY", "")
    TRACE_KEY = st.secrets.get("TRACE_API_KEY", "")
except:
    MAFRA_KEY, TRACE_KEY = "", ""

@st.cache_data(ttl=60)
def fetch_api_data(api_type, query_val=""):
    if api_type == "stats":
        try:
            url = f"http://211.237.50.150:7080/openapi/{MAFRA_KEY}/xml/Grid_20161216000000000428_1/1/1000"
            res = requests.get(url, timeout=10)
            root = ET.fromstring(res.content)
            
            # 정부 서버 에러메시지 확인
            msg = root.find('.//message') or root.find('.//resultMsg')
            if msg is not None and "정상" not in msg.text and "NORMAL" not in msg.text.upper():
                return pd.DataFrame(), f"정부 서버 응답: {msg.text}"
                
            data = [{child.tag: child.text for child in row} for row in root.findall('.//row')]
            df = pd.DataFrame(data)
            if not df.empty and 'THSMON' in df.columns:
                df['THSMON'] = pd.to_numeric(df['THSMON'], errors='coerce').fillna(0)
                return df, "성공"
            return pd.DataFrame(), "데이터가 비어있습니다."
        except Exception as e:
            return pd.DataFrame(), f"통신 에러: {str(e)}"

    elif api_type == "trace":
        try:
            url = "http://data.ekape.or.kr/openapi-data/service/user/animalTrace/traceNoSearch"
            # 공공데이터포털은 unquote를 해줘야 키 에러가 안 납니다
            params = {
                "traceNo": query_val,
                "ServiceKey": urllib.parse.unquote(TRACE_KEY) 
            }
            res = requests.get(url, params=params, timeout=10)
            root = ET.fromstring(res.content)
            
            item = root.find('.//item')
            if item is not None:
                return {child.tag: child.text for child in item}, "성공"
                
            # 정부 서버 에러메시지 추출
            msg = root.find('.//errMsg') or root.find('.//resultMsg')
            err_text = msg.text if msg is not None else "결과값이 없습니다."
            return None, f"정부 서버 응답: {err_text}"
        except Exception as e:
            return None, f"통신 에러: {str(e)}"

# 리얼 데이터 호출
df_stats, stats_msg = fetch_api_data("stats")

# ==========================================
# 4. 메인 화면 UI
# ==========================================
st.markdown("<h1 style='color: #1B2A47;'>🥩 Meatrust 대시보드</h1>", unsafe_allow_html=True)
st.markdown("---")

tab_b2b, tab_b2c = st.tabs(["🏢 B2B 바이어 (도축장 순위 & 등급 검증)", "🛒 B2C 소비자 (고기 이력 & 안심 조회)"])

with tab_b2b:
    st.markdown("<h3 style='color: #E11D48;'>📊 지역/육종별 도축 통계 및 파트너 발굴</h3>", unsafe_allow_html=True)
    
    col_filter, col_chart = st.columns([1, 2])
    with col_filter:
        with st.container(border=True):
            st.subheader("🔍 정밀 필터")
            region = st.selectbox("지역 (시/도)", ["전국", "경기", "강원", "충청", "전라", "경상", "제주"])
            meat_type = st.multiselect("취급 육종", ["소", "돼지", "닭", "오리"], default=["돼지", "소"])

    with col_chart:
        if df_stats.empty:
            # 💡 통계 데이터가 없으면 정부 서버 에러 메시지를 당당하게 출력합니다.
            st.error(f"⚠️ 실제 통계 데이터를 불러오지 못했습니다. (원인: {stats_msg})")
        else:
            df_filtered = df_stats.copy()
            if region != "전국":
                df_filtered = df_filtered[df_filtered['CTRD_NM'].str.contains(region[:2], na=False)]
            if meat_type:
                df_filtered = df_filtered[df_filtered['LVSTCKSPC_NM'].isin(meat_type)]
            
            if not df_filtered.empty:
                theme_colors = {'돼지': '#1B2A47', '소': '#E11D48', '닭': '#475569', '오리': '#94A3B8'}
                
                fig = px.bar(df_filtered.sort_values('THSMON', ascending=False), 
                             x='SLAU_PLACE_NM', y='THSMON', color='LVSTCKSPC_NM',
                             color_discrete_map=theme_colors, 
                             title=f"📈 {region} 도축 물량 현황 (단위: 두)",
                             labels={'SLAU_PLACE_NM': '도축장명', 'THSMON': '도축량', 'LVSTCKSPC_NM': '육종'})
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader(f"🏆 {region} 우수 도축장 실적 TOP 순위")
            if not df_filtered.empty:
                rank_df = df_filtered.groupby(['SLAU_PLACE_NM', 'CTRD_NM']).agg({'THSMON': 'sum', 'LVSTCKSPC_NM': lambda x: ', '.join(set(x))}).reset_index()
                rank_df.columns = ['도축장명', '지역', '당월 도축량(두)', '취급육종']
                rank_df = rank_df.sort_values('당월 도축량(두)', ascending=False).reset_index(drop=True)
                rank_df.index += 1
                st.dataframe(rank_df, use_container_width=True)

with tab_b2c:
    st.markdown("<h3 style='color: #1B2A47; text-align: center;'>🥩 내가 먹는 고기, 어디서 왔을까?</h3>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        with st.container(border=True):
            # 제출용이므로 가짜 번호 힌트 삭제
            trace_input = st.text_input("🔍 이력번호", placeholder="12자리 이력번호를 입력하세요 (예: 002129200127)")
            if st.button("안심 데이터 조회하기", type="primary", use_container_width=True):
                if trace_input:
                    trace_data, trace_msg = fetch_api_data("trace", trace_input)
                    if trace_data:
                        st.success("✅ 공공데이터포털 실시간 연동 성공!")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**🏭 도축장명:** {trace_data.get('slaughterNm', '정보없음')}")
                            st.markdown(f"**📅 도축일자:** {trace_data.get('slaughterDate', '정보없음')}")
                        with c2:
                            st.markdown(f"**🥩 축종 및 등급:** {trace_data.get('lsTypeNm', '')} ({trace_data.get('gradeNm', '')})")
                            st.markdown(f"**🏡 사육지:** {trace_data.get('farmAddr', '정보없음')}")
                    else:
                        # 💡 이력번호가 안 뜨면 정부 서버가 뭐라 하는지 빨간 글씨로 띄워줍니다!
                        st.error(f"❌ 데이터 조회 실패 (사유: {trace_msg})")
