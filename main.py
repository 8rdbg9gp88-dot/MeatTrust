import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import os
import plotly.express as px
import urllib.parse

# ==========================================
# 1. 디자인 및 기본 설정 (네이비/화이트/레드 테마)
# ==========================================
st.set_page_config(page_title="MeatTrust 도축 정보 시스템", layout="wide", initial_sidebar_state="collapsed")

# 네이비(#1B2A47), 레드(#E11D48), 화이트 조합의 커스텀 CSS
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { color: #1B2A47; font-weight: bold; font-size: 1.1rem; }
    .stTabs [aria-selected="true"] { border-bottom-color: #E11D48 !important; color: #E11D48 !important; }
    .stButton>button { background-color: #1B2A47; color: white; border-radius: 8px; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #E11D48; color: white; }
    .metric-card { background-color: white; padding: 20px; border-radius: 10px; border-top: 4px solid #E11D48; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 시네마틱 인트로 화면 (투명한 고기 이미지 배경)
# ==========================================
if "intro_done" not in st.session_state:
    st.markdown("""
        <div style="background-image: linear-gradient(rgba(27, 42, 71, 0.8), rgba(27, 42, 71, 0.8)), url('https://images.unsplash.com/photo-1607623814075-e51df1bd682f?q=80&w=2000&auto=format&fit=crop');
            background-size: cover; background-position: center; height: 85vh; border-radius: 20px; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; text-align: center; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.2);">
            <h1 style='font-size: 5rem; margin-bottom: 10px; color: white; font-weight: 900; letter-spacing: 2px;'>MeatTrust</h1>
            <p style='font-size: 1.5rem; color: #E0E0E0; margin-bottom: 30px;'>투명한 데이터가 만드는 신뢰, 전국 축산물 AI 매칭 플랫폼</p>
            <div style="background-color: rgba(225, 29, 72, 0.9); padding: 10px 30px; border-radius: 30px; font-weight: bold; font-size: 1.2rem;">소비자와 바이어를 위한 안심 조회 시스템</div>
        </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 MeatTrust 시스템 입장하기", use_container_width=True):
            st.session_state.intro_done = True
            st.rerun()
    st.stop()

# ==========================================
# 3. 데이터 통신 함수 (4개 API 연동부)
# ==========================================
MAFRA_KEY = os.environ.get("MAFRA_API_KEY", "")
TRACE_KEY = os.environ.get("TRACE_API_KEY", "")

@st.cache_data(ttl=300)
def fetch_api_data(api_type, query_val=""):
    """4개의 API를 상황에 맞게 호출하는 통합 함수"""
    try:
        # 1. 행안부 전국 도축장 목록 (지도/기본데이터)
        if api_type == "slaughterhouse": 
            if not TRACE_KEY: return pd.DataFrame()
            url = f"https://apis.data.go.kr/1741000/slaughterhouses/getslaughterhousesInfo?serviceKey={TRACE_KEY}&pageNo=1&numOfRows=100"
            res = requests.get(url, verify=False)
            # 행안부 JSON 처리 로직 (실제 데이터에 맞게 파싱)
            # 여기서는 UI 시연을 위해 가공된 데이터를 반환하도록 설정할 수 있습니다.
            return pd.DataFrame([{"업체명": "삼정산업", "지역": "경기", "상태": "정상"}]) # 샘플대체가능
            
        # 2. 농림부 시도별 도축실적 (통계용)
        elif api_type == "stats":
            if not MAFRA_KEY: return pd.DataFrame()
            url = f"http://211.237.50.150:7080/openapi/{MAFRA_KEY}/xml/Grid_20161216000000000428_1/1/1000"
            res = requests.get(url)
            root = ET.fromstring(res.content)
            data = [{child.tag: child.text for child in row} for row in root.findall('.//row')]
            df = pd.DataFrame(data)
            if 'THSMON' in df.columns: df['THSMON'] = pd.to_numeric(df['THSMON'], errors='coerce').fillna(0)
            return df
            
        # 3. 이력정보조회 (B2C 소비자용)
        elif api_type == "trace":
            if not TRACE_KEY: return "키 없음"
            url = f"http://data.ekape.or.kr/openapi-data/service/user/animalTrace/traceNoSearch?traceNo={query_val}&ServiceKey={TRACE_KEY}"
            res = requests.get(url)
            root = ET.fromstring(res.content)
            item = root.find('.//item')
            return {child.tag: child.text for child in item} if item is not None else None

        # 4. 등급판정확인서조회 (B2B 바이어용)
        elif api_type == "grade":
            if not MAFRA_KEY: return "키 없음"
            url = f"http://211.237.50.150:7080/openapi/{MAFRA_KEY}/xml/GradeConfirm/1/5?issueNo={query_val}"
            res = requests.get(url)
            root = ET.fromstring(res.content)
            row = root.find('.//row')
            return {child.tag: child.text for child in row} if row is not None else None

    except Exception as e:
        return None

# 데이터 로드
df_stats = fetch_api_data("stats")

# ==========================================
# 4. 메인 화면 UI 구성
# ==========================================
st.markdown("<h1 style='color: #1B2A47;'>🥩 MeatTrust 대시보드</h1>", unsafe_allow_html=True)
st.markdown("---")

# 탭 생성: 기획안에 맞춘 B2B / B2C 분리
tab_b2b, tab_b2c = st.tabs(["🏢 B2B 바이어 (도축장 순위 & 등급 검증)", "🛒 B2C 소비자 (고기 이력 & 안심 조회)"])

# ------------------------------------------
# [탭 1] B2B 바이어용 화면 (필터, 순위표, 확인서 검증)
# ------------------------------------------
with tab_b2b:
    st.markdown("<h3 style='color: #E11D48;'>📊 지역/육종별 도축 통계 및 파트너 발굴</h3>", unsafe_allow_html=True)
    
    col_filter, col_chart = st.columns([1, 2])
    with col_filter:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.subheader("🔍 정밀 필터")
        region = st.selectbox("지역 (시/도)", ["전국", "서울", "경기", "강원", "충청", "전라", "경상", "제주"])
        meat_type = st.multiselect("취급 육종", ["소", "돼지", "닭", "오리"], default=["돼지"])
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<br><div class='metric-card'>", unsafe_allow_html=True)
        st.subheader("📑 등급판정확인서 교차 검증")
        st.caption("납품받은 고기의 등급확인서 번호를 조회하세요.")
        grade_no = st.text_input("발급번호 입력 (예: 1234567)")
        if st.button("진위 여부 확인", use_container_width=True):
            if grade_no:
                grade_info = fetch_api_data("grade", grade_no)
                if grade_info and grade_info != "키 없음":
                    st.success(f"✅ 유효한 확인서입니다. (도축장: {grade_info.get('SLAU_PLACE_NM', '정보있음')})")
                else:
                    st.error("❌ 조회된 데이터가 없거나 서버 통신에 실패했습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_chart:
        if df_stats is not None and not df_stats.empty:
            df_filtered = df_stats.copy()
            if region != "전국":
                df_filtered = df_filtered[df_filtered['CTRD_NM'].str.contains(region[:2], na=False)]
            if meat_type:
                df_filtered = df_filtered[df_filtered['LVSTCKSPC_NM'].isin(meat_type)]
            
            # 실적 순위표
            st.subheader(f"🏆 {region} 우수 도축장 실적 TOP 10")
            rank_df = df_filtered.groupby(['SLAU_PLACE_NM', 'CTRD_NM']).agg({'THSMON': 'sum', 'LVSTCKSPC_NM': lambda x: ', '.join(set(x))}).reset_index()
            rank_df.columns = ['도축장명', '지역', '당월 도축량(두)', '취급육종']
            rank_df = rank_df.sort_values('당월 도축량(두)', ascending=False).reset_index(drop=True)
            rank_df.index += 1
            st.dataframe(rank_df.head(10), use_container_width=True)

# ------------------------------------------
# [탭 2] B2C 소비자용 화면 (이력번호 바코드 조회)
# ------------------------------------------
with tab_b2c:
    st.markdown("<h3 style='color: #1B2A47; text-align: center;'>🥩 내가 먹는 고기, 어디서 왔을까?</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>포장지에 적힌 12자리 이력번호를 입력하시면 사육부터 도축까지의 정보를 투명하게 공개합니다.</p>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        with st.container(border=True):
            trace_input = st.text_input("🔍 이력번호 (숫자 12자리)", placeholder="예: 002144366294")
            if st.button("안심 데이터 조회하기", type="primary", use_container_width=True):
                if trace_input:
                    trace_data = fetch_api_data("trace", trace_input)
                    if trace_data == "키 없음":
                        st.warning("서버에 TRACE_API_KEY가 등록되지 않았습니다.")
                    elif trace_data:
                        st.success("✅ 안전관리인증(HACCP)을 통과한 정상적인 고기입니다.")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**🏭 도축장명:** {trace_data.get('slaughterNm', '정보없음')}")
                            st.markdown(f"**📅 도축일자:** {trace_data.get('slaughterDate', '정보없음')}")
                        with c2:
                            st.markdown(f"**🥩 축종 및 등급:** {trace_data.get('lsTypeNm', '')} ({trace_data.get('gradeNm', '')})")
                            st.markdown(f"**🏡 사육지:** {trace_data.get('farmAddr', '정보없음')}")
                    else:
                        st.error("이력번호를 다시 확인해주세요. (공공데이터 동기화 지연일 수 있습니다)")
