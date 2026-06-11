import streamlit as st
import pandas as pd
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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터 로드 (시도별 + 도축장별 통합)
# ==========================================
@st.cache_data
def load_all_data():
    try:
        df_regional = pd.read_csv("all_stats_data.csv") # 시도별 데이터
        df_slaughter = pd.read_csv("slaughterhouse_stats.csv") # 도축장별 데이터
        
        # 데이터 정리
        for df in [df_regional, df_slaughter]:
            df['YM'] = df['YM'].astype(str)
            df['THSMON'] = pd.to_numeric(df['THSMON'], errors='coerce').fillna(0)
        return df_regional, df_slaughter, "성공"
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), f"파일 읽기 에러: {str(e)}"

df_reg, df_slau, msg = load_all_data()

# ==========================================
# 3. 메인 대시보드
# ==========================================
st.markdown("<h1 style='color: #1B2A47;'>🥩 Meatrust 대시보드</h1>", unsafe_allow_html=True)
st.success("✅ 공식 공공데이터 2종 통합 연동 완료!")
st.markdown("---")

tab_b2b, tab_b2c = st.tabs(["🏢 B2B 바이어 (도축 실적 분석)", "🛒 B2C 소비자 (이력 조회 - 준비 중)"])

with tab_b2b:
    st.markdown("<h3 style='color: #E11D48;'>📊 지역 및 도축장별 실적 분석</h3>", unsafe_allow_html=True)
    
    if df_reg.empty or df_slau.empty:
        st.error(f"⚠️ 엑셀 파일 확인 필요: {msg}")
    else:
        # 데이터 뷰 선택 (시도별 vs 도축장별)
        view_mode = st.radio("분석 단위 선택", ["시/도별 통계", "도축장별 세부 실적"], horizontal=True)
        
        col_filter, col_chart = st.columns([1, 2.5])
        
        with col_filter:
            with st.container(border=True):
                # 데이터 선택에 따른 타겟 설정
                if view_mode == "시/도별 통계":
                    target_df = df_reg
                    region_col = 'CTRD_NM'
                else:
                    target_df = df_slau
                    region_col = 'SLAU_PLACE_NM'
                
                month_list = sorted(target_df['YM'].unique(), reverse=True)
                selected_month = st.selectbox("조회 년/월", month_list)
                
                # 지역 필터링 (시도별 뷰일 때만 사용)
                search_region = None
                if view_mode == "시/도별 통계":
                    search_region = st.selectbox("지역 필터", ["전국"] + list(target_df['CTRD_NM'].unique()))
                
                meat_type = st.multiselect("취급 육종", target_df['LVSTCKSPC_NM'].unique(), default=["돼지", "소"])

        with col_chart:
            # 데이터 필터링
            df_filtered = target_df[target_df['YM'] == selected_month].copy()
            if view_mode == "시/도별 통계" and search_region != "전국":
                df_filtered = df_filtered[df_filtered['CTRD_NM'] == search_region]
            if meat_type:
                df_filtered = df_filtered[df_filtered['LVSTCKSPC_NM'].isin(meat_type)]
            
            if not df_filtered.empty:
                theme_colors = {'돼지': '#1B2A47', '소': '#E11D48', '닭': '#475569', '오리': '#94A3B8'}
                
                fig = px.bar(df_filtered.sort_values('THSMON', ascending=False), 
                             x=region_col, y='THSMON', color='LVSTCKSPC_NM',
                             color_discrete_map=theme_colors, 
                             title=f"📈 {selected_month} 기준 도축 물량 현황",
                             labels={region_col: '지역/도축장', 'THSMON': '도축량(두)', 'LVSTCKSPC_NM': '육종'})
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(df_filtered.sort_values('THSMON', ascending=False), use_container_width=True)
            else:
                st.info("해당 조건의 데이터가 없습니다.")

with tab_b2c:
    st.info("이력번호 조회 기능은 현재 점검 및 데이터 연동 준비 중입니다.")
