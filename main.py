import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv
import plotly.express as px  # 그래프를 그리기 위한 강력한 도구!

load_dotenv()

# 1. 페이지 설정
st.set_page_config(page_title="MeatTrust - 데이터 시각화", layout="wide")

# 2. 테마 커스터마이징 (네이비 포인트 강조)
st.markdown("""
<style>
    .main { background-color: #FFFFFF; }
    .stMetric { background-color: #F4F6F9; padding: 20px; border-radius: 10px; border-left: 5px solid #1B2A47; }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 로드 함수 (기존과 동일하되 캐싱 유지)
@st.cache_data
def fetch_api_data():
    api_key = os.environ.get("MAFRA_API_KEY")
    url = f"http://211.237.50.150:7080/openapi/{api_key}/xml/Grid_20161216000000000428_1/1/1000"
    try:
        response = requests.get(url)
        root = ET.fromstring(response.content)
        data = []
        for row in root.findall('.//row'):
            item = {child.tag: child.text for child in row}
            data.append(item)
        df = pd.DataFrame(data)
        if not df.empty:
            df['THSMON'] = pd.to_numeric(df['THSMON'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

# 인트로 화면 제어
if "intro_done" not in st.session_state:
    st.markdown("""
        <div style="background-image: linear-gradient(rgba(27, 42, 71, 0.7), rgba(27, 42, 71, 0.7)), url('https://images.unsplash.com/photo-1607623814075-e51df1bd682f?q=80&w=2000');
            background-size: cover; height: 80vh; border-radius: 20px; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; text-align: center;">
            <h1 style='font-size: 4rem; color: white;'>🥩 도축 정보 시스템</h1>
            <p style='font-size: 1.5rem; color: #E0E0E0;'>AI 기반 전국 축산물 데이터 분석 플랫폼</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 시스템 입장하기", use_container_width=True):
        st.session_state.intro_done = True
        st.rerun()
    st.stop()

df_api = fetch_api_data()

# 메인 헤더
st.title("📊 MeatTrust 실시간 데이터 대시보드")

tab1, tab2 = st.tabs(["🏢 기업용(B2B) 데이터 분석", "🛒 소비자(B2C) 안심 조회"])

with tab1:
    # --- 상단 요약 지표 (Metrics) ---
    st.subheader("📌 오늘자 핵심 데이터 요약")
    m_col1, m_col2, m_col3 = st.columns(3)
    if not df_api.empty:
        m_col1.metric("총 등록 업체 수", f"{len(df_api['SLAU_PLACE_NM'].unique())}개")
        m_col2.metric("전국 총 도축량", f"{int(df_api['THSMON'].sum()):,}두")
        m_col3.metric("최대 생산 육종", df_api.groupby('LVSTCKSPC_NM')['THSMON'].sum().idxmax())

    st.divider()

    # --- 데이터 시각화 구역 (그래프!) ---
    st.subheader("💡 실시간 시장 통계 그래프")
    g_col1, g_col2 = st.columns(2)

    if not df_api.empty:
        with g_col1:
            # 1. 지역별 도축 비중 (파이 차트)
            region_data = df_api.groupby('CTRD_NM')['THSMON'].sum().reset_index()
            fig_pie = px.pie(region_data, values='THSMON', names='CTRD_NM', 
                             title='📍 지역별 도축 물량 비중',
                             color_discrete_sequence=px.colors.sequential.RdBu)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        with g_col2:
            # 2. 육종별 도축 규모 (막대 그래프)
            meat_data = df_api.groupby('LVSTCKSPC_NM')['THSMON'].sum().reset_index().sort_values(by='THSMON', ascending=False)
            fig_bar = px.bar(meat_data, x='LVSTCKSPC_NM', y='THSMON', 
                             title='🥩 육종별 도축 규모 (두)',
                             labels={'LVSTCKSPC_NM': '육성 종류', 'THSMON': '도축량'},
                             color='THSMON', color_continuous_scale='Blues')
            st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # --- 기존 조건 검색 및 리스트 ---
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("🔍 업체 필터링")
        region_filter = st.selectbox("지역 선택", ["전국"] + list(df_api['CTRD_NM'].unique()))
        meat_type_filter = st.multiselect("육종 선택", list(df_api['LVSTCKSPC_NM'].unique()), default=list(df_api['LVSTCKSPC_NM'].unique())[:2])
        
    with col2:
        st.subheader("🏆 필터링 결과")
        filtered_df = df_api.copy()
        if region_filter != "전국":
            filtered_df = filtered_df[filtered_df['CTRD_NM'] == region_filter]
        if meat_type_filter:
            filtered_df = filtered_df[filtered_df['LVSTCKSPC_NM'].isin(meat_type_filter)]
        
        for i, row in filtered_df.head(3).iterrows():
            with st.container(border=True):
                st.markdown(f"**{row['SLAU_PLACE_NM']}** ({row['CTRD_NM']})")
                st.caption(f"취급: {row['LVSTCKSPC_NM']} | 당월 도축: {int(row['THSMON']):,}두")
                st.link_button("📞 문의하기", "tel:010-0000-0000")

# 소비자 탭은 기존 검색 기능 유지
with tab2:
    st.markdown("<h3 style='text-align: center;'>🏭 우리 동네 도축 업체 위생 정보 조회</h3>", unsafe_allow_html=True)
    with st.form("search_form"):
        search_query = st.text_input("", placeholder="조회하고 싶은 업체명을 입력하세요.")
        if st.form_submit_button("🔍 데이터 조회하기", use_container_width=True):
            if search_query:
                res = df_api[df_api['SLAU_PLACE_NM'].str.contains(search_query, na=False)]
                if not res.empty:
                    for _, r in res.iterrows():
                        st.info(f"**{r['SLAU_PLACE_NM']}**는 현재 정상 운영 중인 업체입니다. (지역: {r['CTRD_NM']})")
                else:
                    st.error("일치하는 업체 정보가 없거나 비등록 업체입니다.")
