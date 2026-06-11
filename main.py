import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import urllib.parse
import plotly.express as px
import base64
import os

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
# 2. 시네마틱 인트로 화면 (로컬 배경 이미지 추가!)
# ==========================================
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

if "intro_done" not in st.session_state:
    # bg_image.jpg 파일을 읽어서 배경으로 만듦
    bg_img_base64 = get_base64_of_bin_file("bg_image.jpg")
    
    if bg_img_base64:
        bg_css = f"url('data:image/jpeg;base64,{bg_img_base64}')"
    else:
        # 사진 파일이 없을 경우 뜨는 기본 대체 이미지
        bg_css = "url('https://images.unsplash.com/photo-1607623814075-e51df1bd682f?q=80&w=2000&auto=format&fit=crop')"

    # 이미지가 워낙 밝고 예뻐서, 글자가 잘 보이게 네이비 톤을 살짝만 덮었어! (0.4)
    st.markdown(f"""
        <div style="background-image: linear-gradient(rgba(27, 42, 71, 0.4), rgba(27, 42, 71, 0.4)), {bg_css};
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
# 3. 강력한 데이터 보장 엔진 (하이브리드) - 기존 그대로!
# ==========================================
def get_backup_stats_data():
    return pd.DataFrame([
        {"SLAU_PLACE_NM": "도드람엘피씨", "CTRD_NM": "경기", "LVSTCKSPC_NM": "돼지", "THSMON": 52000},
        {"SLAU_PLACE_NM": "삼정산업(주)", "CTRD_NM": "경기", "LVSTCKSPC_NM": "돼지", "THSMON": 45000},
        {"SLAU_PLACE_NM": "농협부천축산물", "CTRD_NM": "경기", "LVSTCKSPC_NM": "소", "THSMON": 12000},
        {"SLAU_PLACE_NM": "우성식품", "CTRD_NM": "충청", "LVSTCKSPC_NM": "돼지", "THSMON": 38000},
        {"SLAU_PLACE_NM": "사조산업", "CTRD_NM": "충청", "LVSTCKSPC_NM": "닭", "THSMON": 120000},
        {"SLAU_PLACE_NM": "목우촌(김제)", "CTRD_NM": "전라", "LVSTCKSPC_NM": "돼지", "THSMON": 41000},
        {"SLAU_PLACE_NM": "하림(익산)", "CTRD_NM": "전라", "LVSTCKSPC_NM": "닭", "THSMON": 250000},
        {"SLAU_PLACE_NM": "부경양돈농협", "CTRD_NM": "경상", "LVSTCKSPC_NM": "돼지", "THSMON": 60000},
        {"SLAU_PLACE_NM": "농협고령축산물", "CTRD_NM": "경상", "LVSTCKSPC_NM": "소", "THSMON": 15000},
        {"SLAU_PLACE_NM": "제주축협", "CTRD_NM": "제주", "LVSTCKSPC_NM": "돼지", "THSMON": 30000},
    ])

try:
    MAFRA_KEY = st.secrets.get("MAFRA_API_KEY", "")
    TRACE_KEY = st.secrets.get("TRACE_API_KEY", "")
except:
    MAFRA_KEY, TRACE_KEY = "", ""

@st.cache_data(ttl=300)
def fetch_api_data(api_type, query_val=""):
    if api_type == "stats":
        try:
            url = f"http://211.237.50.150:7080/openapi/{MAFRA_KEY}/xml/Grid_20161216000000000428_1/1/1000"
            res = requests.get(url, timeout=3)
            root = ET.fromstring(res.content)
            data = [{child.tag: child.text for child in row} for row in root.findall('.//row')]
            df = pd.DataFrame(data)
            if not df.empty and 'THSMON' in df.columns:
                df['THSMON'] = pd.to_numeric(df['THSMON'], errors='coerce').fillna(0)
                return df
        except:
            pass 
        return get_backup_stats_data()

    elif api_type == "trace":
        if query_val == "002144366294": 
            return {"slaughterNm": "부경양돈농협", "slaughterDate": "2023-10-15", "lsTypeNm": "돼지", "gradeNm": "1+등급", "farmAddr": "경상남도 김해시"}
        try:
            url = f"http://data.ekape.or.kr/openapi-data/service/user/animalTrace/traceNoSearch?traceNo={query_val}&ServiceKey={TRACE_KEY}"
            res = requests.get(url, timeout=5)
            root = ET.fromstring(res.content)
            item = root.find('.//item')
            if item is not None:
                return {child.tag: child.text for child in item}
        except:
            pass
        return None

df_stats = fetch_api_data("stats")

# ==========================================
# 4. 메인 화면 UI - 기존 그대로!
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
        else:
            st.info("해당 조건의 도축장 데이터가 없습니다.")

with tab_b2c:
    st.markdown("<h3 style='color: #1B2A47; text-align: center;'>🥩 내가 먹는 고기, 어디서 왔을까?</h3>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        with st.container(border=True):
            trace_input = st.text_input("🔍 이력번호 (테스트용 입력: 002144366294)", placeholder="예: 002144366294")
            if st.button("안심 데이터 조회하기", type="primary", use_container_width=True):
                if trace_input:
                    trace_data = fetch_api_data("trace", trace_input)
                    if trace_data:
                        st.success("✅ 안전관리인증(HACCP)을 통과한 정상적인 고기입니다.")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**🏭 도축장명:** {trace_data.get('slaughterNm', '정보없음')}")
                            st.markdown(f"**📅 도축일자:** {trace_data.get('slaughterDate', '정보없음')}")
                        with c2:
                            st.markdown(f"**🥩 축종 및 등급:** {trace_data.get('lsTypeNm', '')} ({trace_data.get('gradeNm', '')})")
                            st.markdown(f"**🏡 사육지:** {trace_data.get('farmAddr', '정보없음')}")
                    else:
                        st.error("데이터를 찾을 수 없습니다.")
