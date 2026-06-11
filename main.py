import streamlit as st
import pandas as pd
import plotly.express as px
import base64

# ==========================================
# 1. 기본 웹사이트 설정
# ==========================================
st.set_page_config(page_title="Meatrust 도축 정보 시스템", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { color: #1B2A47; font-weight: bold; font-size: 1.1rem; }
    .stTabs [aria-selected="true"] { border-bottom-color: #E11D48 !important; color: #E11D48 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터 불러오기 (핵심 파트!)
# ==========================================
@st.cache_data
def load_excel_data():
    """깃허브에 올린 all_stats_data.csv 파일을 읽어옵니다."""
    try:
        # 엑셀 파일 읽기!
        df = pd.read_csv("all_stats_data.csv")
        
        # YM(년월) 데이터를 보기 좋게 문자로 바꾸기
        df['YM'] = df['YM'].astype(str) 
        # 도축량(THSMON)을 숫자로 확실히 인식시키기
        df['THSMON'] = pd.to_numeric(df['THSMON'], errors='coerce').fillna(0)
        
        return df, "성공"
    except Exception as e:
        return pd.DataFrame(), f"파일 읽기 에러: {str(e)}"

# 데이터 로딩 실행
df_stats, msg = load_excel_data()

# ==========================================
# 3. 메인 화면 UI (그래프 그리기)
# ==========================================
st.markdown("<h1 style='color: #1B2A47;'>🥩 Meatrust 대시보드</h1>", unsafe_allow_html=True)
st.markdown("---")

tab_b2b, tab_b2c = st.tabs(["🏢 B2B 바이어 (시도별 도축 실적)", "🛒 B2C 소비자 (이력 조회 - 준비 중)"])

with tab_b2b:
    st.markdown("<h3 style='color: #E11D48;'>📊 지역/육종별 실적 분석</h3>", unsafe_allow_html=True)
    
    if df_stats.empty:
        st.error(f"⚠️ 데이터를 불러오지 못했습니다. (원인: {msg}) \n깃허브에 'all_stats_data.csv' 파일이 잘 올라갔는지 확인해주세요!")
    else:
        # 데이터가 10년 치나 되니까, 날짜(년/월)를 선택하는 필터를 만들자!
        month_list = sorted(df_stats['YM'].unique(), reverse=True)
        
        col_filter, col_chart = st.columns([1, 2.5])
        
        with col_filter:
            with st.container(border=True):
                st.subheader("🔍 정밀 필터")
                # 년/월 선택 (기본값은 가장 최신 날짜)
                selected_month = st.selectbox("조회 년/월", month_list)
                # 지역 및 육종 선택
                region = st.selectbox("지역 (시/도)", ["전국"] + list(df_stats['CTRD_NM'].unique()))
                meat_type = st.multiselect("취급 육종", df_stats['LVSTCKSPC_NM'].unique(), default=["돼지", "소"])

        with col_chart:
            # 사용자가 선택한 필터대로 데이터 걸러내기
            df_filtered = df_stats[df_stats['YM'] == selected_month].copy()
            if region != "전국":
                df_filtered = df_filtered[df_filtered['CTRD_NM'] == region]
            if meat_type:
                df_filtered = df_filtered[df_filtered['LVSTCKSPC_NM'].isin(meat_type)]
            
            # 그래프 그리기
            if not df_filtered.empty:
                theme_colors = {'돼지': '#1B2A47', '소': '#E11D48', '닭': '#475569', '오리': '#94A3B8'}
                
                # 지역과 육종별로 도축량 합치기
                fig_df = df_filtered.groupby(['CTRD_NM', 'LVSTCKSPC_NM'])['THSMON'].sum().reset_index()
                
                fig = px.bar(fig_df.sort_values('THSMON', ascending=False), 
                             x='CTRD_NM', y='THSMON', color='LVSTCKSPC_NM',
                             color_discrete_map=theme_colors, 
                             title=f"📈 {selected_month[:4]}년 {selected_month[4:]}월 도축 물량 현황 (단위: 두)",
                             labels={'CTRD_NM': '지역명', 'THSMON': '도축량', 'LVSTCKSPC_NM': '육종'})
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("🏆 세부 실적 표")
                rank_df = fig_df.sort_values('THSMON', ascending=False).reset_index(drop=True)
                rank_df.index += 1
                st.dataframe(rank_df, use_container_width=True)
            else:
                st.info("해당 조건의 데이터가 없습니다.")

with tab_b2c:
    st.info("이력번호 조회 기능은 현재 점검 및 데이터 연동 준비 중입니다.")
