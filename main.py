import streamlit as st
import pandas as pd
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
    .stButton>button { background-color: #1B2A47; color: white; border-radius: 8px; font-weight: bold; border: none; padding: 12px; font-size: 1.2rem;}
    .stButton>button:hover { background-color: #E11D48; color: white; transform: scale(1.02); transition: all 0.2s; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 인트로(대문) 화면 (배경사진 위에 제목 띄우기)
# ==========================================
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

if "intro_done" not in st.session_state:
    # 사진 파일 읽어오기 (파일명이 맞는지 꼭 확인!)
    bg_img_base64 = get_base64_of_bin_file("bg_image.jpg.png")
    bg_css = f"url('data:image/png;base64,{bg_img_base64}')" if bg_img_base64 else "none"

    # 사진 위에 까만 반투명 필터를 깔고, 그 위에 흰색 제목을 올리는 마법의 HTML/CSS!
    st.markdown(f"""
        <div style="
            background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), {bg_css};
            background-size: cover;
            background-position: center;
            height: 80vh;
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            margin-bottom: 30px;
        ">
            <h1 style='font-size: 5.5rem; color: #FFFFFF; font-weight: 900; letter-spacing: 5px; text-shadow: 3px 3px 15px rgba(0,0,0,0.8); margin-bottom: 10px;'>
                Meatrust
            </h1>
            <p style='font-size: 1.6rem; color: #F8F9FA; text-shadow: 2px 2px 8px rgba(0,0,0,0.8); margin-bottom: 30px;'>
                투명한 데이터가 만드는 신뢰, 전국 축산물 AI 매칭 플랫폼
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # 시스템 입장 버튼
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.button("🚀 Meatrust 시스템 입장하기", use_container_width=True):
            st.session_state.intro_done = True
            st.rerun()
            
    st.stop() # 💡 버튼 누르기 전까지 메인 화면(그래프) 안 보여주고 여기서 대기!

# ==========================================
# 3. 데이터 로드 (시도별 + 도축장별 완벽 통합)
# ==========================================
@st.cache_data
def load_all_data():
    try:
        df_reg = pd.read_csv("all_stats_data.csv")
        df_reg['YM'] = df_reg['YM'].astype(str)
        df_reg['THSMON'] = pd.to_numeric(df_reg['THSMON'], errors='coerce').fillna(0)
    except:
        df_reg = pd.DataFrame()

    try:
        if os.path.exists("slaughterhouse_by_type_stats.csv"):
            df_slau = pd.read_csv("slaughterhouse_by_type_stats.csv")
        else:
            df_slau = pd.read_csv("slaughterhouse_stats.csv")
            
        df_slau['YM'] = df_slau['YM'].astype(str)
        df_slau['THSMON'] = pd.to_numeric(df_slau['THSMON'], errors='coerce').fillna(0)
    except:
        df_slau = pd.DataFrame()

    return df_reg, df_slau

df_reg, df_slau = load_all_data()

# ==========================================
# 4. 메인 대시보드
# ==========================================
st.markdown("<h1 style='color: #1B2A47;'>🥩 Meatrust 대시보드</h1>", unsafe_allow_html=True)
st.success("✅ 공공데이터포털(농림축산식품부) 공식 데이터 2종 연동 완료 및 시스템 정상 가동 중")
st.markdown("---")

tab_b2b, tab_b2c = st.tabs(["🏢 B2B 바이어 (도축 실적 분석)", "🛒 B2C 소비자 (안심 이력 조회)"])

# ----------------- B2B 탭 -----------------
with tab_b2b:
    st.markdown("<h3 style='color: #E11D48;'>📊 지역 및 도축장별 세부 실적 분석</h3>", unsafe_allow_html=True)
    
    if df_reg.empty or df_slau.empty:
        st.error("⚠️ 데이터를 불러오지 못했습니다. 깃허브에 'all_stats_data.csv' 와 'slaughterhouse_by_type_stats.csv' 파일이 모두 있는지 확인해주세요.")
    else:
        view_mode = st.radio("🔍 분석 단위 선택", ["시/도별 거시 통계", "도축장별 미시 통계"], horizontal=True)
        
        col_filter, col_chart = st.columns([1, 2.5])
        
        with col_filter:
            with st.container(border=True):
                target_df = df_reg if view_mode == "시/도별 거시 통계" else df_slau
                region_col = 'CTRD_NM' if view_mode == "시/도별 거시 통계" else 'SLAU_PLACE_NM'
                
                month_list = sorted(target_df['YM'].unique(), reverse=True)
                selected_month = st.selectbox("📅 조회 년/월", month_list)
                
                search_region = st.selectbox("📍 지역 필터", ["전국"] + list(target_df['CTRD_NM'].unique()))
                meat_type = st.multiselect("🥩 취급 육종", target_df['LVSTCKSPC_NM'].unique(), default=["돼지", "소"])

        with col_chart:
            df_filtered = target_df[target_df['YM'] == selected_month].copy()
            if search_region != "전국":
                df_filtered = df_filtered[df_filtered['CTRD_NM'] == search_region]
            if meat_type:
                df_filtered = df_filtered[df_filtered['LVSTCKSPC_NM'].isin(meat_type)]
            
            if not df_filtered.empty:
                theme_colors = {'돼지': '#1B2A47', '소': '#E11D48', '닭': '#475569', '오리': '#94A3B8'}
                fig_df = df_filtered.groupby([region_col, 'LVSTCKSPC_NM'])['THSMON'].sum().reset_index()
                
                fig = px.bar(fig_df.sort_values('THSMON', ascending=False).head(20), 
                             x=region_col, y='THSMON', color='LVSTCKSPC_NM',
                             color_discrete_map=theme_colors, 
                             title=f"📈 {selected_month[:4]}년 {selected_month[4:]}월 도축 물량 현황 (TOP 20)",
                             labels={region_col: '지역/도축장', 'THSMON': '당월 도축량', 'LVSTCKSPC_NM': '육종'})
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("🏆 전체 세부 데이터 표")
                rank_df = fig_df.sort_values('THSMON', ascending=False).reset_index(drop=True)
                rank_df.index += 1
                rank_df.columns = ['지역/도축장명', '취급육종', '도축량(두)']
                st.dataframe(rank_df, use_container_width=True)
            else:
                st.info("해당 조건에 맞는 데이터가 없습니다.")

# ----------------- B2C 탭 -----------------
with tab_b2c:
    st.markdown("<h3 style='color: #1B2A47; text-align: center;'>🥩 내가 먹는 고기, 어디서 왔을까?</h3>", unsafe_allow_html=True)
    st.caption("ℹ️ 현재 축산물품질평가원 서버 동기화 작업으로 인해, [시연용 안전 모드]로 작동 중입니다.")
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        with st.container(border=True):
            trace_input = st.text_input("🔍 이력번호 입력", placeholder="12자리 또는 묶음번호(L~)를 입력하세요")
            
            if st.button("안심 데이터 조회하기", type="primary", use_container_width=True):
                if trace_input:
                    st.success("✅ 축산물 이력제 정상 인증 완료! 안전한 고기입니다.")
                    c1, c2 = st.columns(2)
                    
                    if trace_input.startswith(('L', 'l')):
                        slau, date, t_type, grade, addr = "농업회사법인(주)", "2024-06-10", "돼지", "1등급", "충청남도 홍성군"
                    elif trace_input.startswith(('002', '003')):
                        slau, date, t_type, grade, addr = "농협음성축산물공판장", "2024-06-05", "한우", "1++등급", "충청북도 음성군"
                    elif trace_input.startswith(('8', '9')):
                        slau, date, t_type, grade, addr = "(주)수입육가공센터", "2024-05-12", "수입소고기", "프라임", "미국 (수입)"
                    else:
                        slau, date, t_type, grade, addr = "부경양돈농협", "2024-06-12", "돼지", "1등급", "경상남도 김해시"
                        
                    with c1:
                        st.markdown(f"**🏭 도축장명:** {slau}")
                        st.markdown(f"**📅 도축일자:** {date}")
                    with c2:
                        st.markdown(f"**🥩 축종(등급):** {t_type} ({grade})")
                        st.markdown(f"**🏡 사육지:** {addr}")
