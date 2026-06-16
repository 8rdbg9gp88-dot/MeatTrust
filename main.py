import requests
import xml.etree.ElementTree as ET
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
# 2. 인트로(대문) 화면 (bg_image.jpg 완벽 적용)
# ==========================================
import base64

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

if "intro_done" not in st.session_state:
    # 💡 네가 정해둔 파일명 그대로 딱 고정!
    bg_img_base64 = get_base64_of_bin_file("bg_image.jpg")
    
    # 💡 jpg 전용 코드로 수정 (image/jpeg)
    if bg_img_base64:
        bg_css = f"url('data:image/jpeg;base64,{bg_img_base64}')"
    else:
        bg_css = "none"

    st.markdown(f"""
        <div style="
            background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), {bg_css};
            background-color: #1B2A47;
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
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.button("🚀 Meatrust 시스템 입장하기", use_container_width=True):
            st.session_state.intro_done = True
            st.rerun()
            
    st.stop()

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
                # 타겟 데이터 설정 및 연도/월 컬럼 분리
                target_df = df_reg if view_mode == "시/도별 거시 통계" else df_slau
                target_df = target_df.copy() # 원본 데이터 보호
                target_df['Year'] = target_df['YM'].str[:4]
                target_df['Month'] = target_df['YM'].str[4:]
                region_col = 'CTRD_NM' if view_mode == "시/도별 거시 통계" else 'SLAU_PLACE_NM'
                
                # 💡 1. 연도 선택 (깔끔하게 연도만 보여줌)
                year_list = sorted(target_df['Year'].unique(), reverse=True)
                selected_year = st.selectbox("📅 연도 선택", year_list)
                
                # 💡 2. 월 선택 (해당 연도의 월만 보여주되, '전체 합산' 기능 추가!)
                available_months = sorted(target_df[target_df['Year'] == selected_year]['Month'].unique())
                month_list = ["전체 (1년치 합산)"] + available_months
                selected_month = st.selectbox("🗓️ 월 선택", month_list)
                
                # 3. 지역 및 육종 필터
                search_region = st.selectbox("📍 지역 필터", ["전국"] + list(target_df['CTRD_NM'].unique()))
                meat_type = st.multiselect("🥩 취급 육종", target_df['LVSTCKSPC_NM'].unique(), default=["돼지", "소"])

        with col_chart:
            # 💡 연도 먼저 필터링
            df_filtered = target_df[target_df['Year'] == selected_year].copy()
            
            # 💡 '전체'를 고르면 해당 연도의 모든 데이터를 합산하고, 특정 월을 고르면 그 달만 필터링!
            if selected_month != "전체 (1년치 합산)":
                df_filtered = df_filtered[df_filtered['Month'] == selected_month]
                chart_title_date = f"{selected_year}년 {selected_month}월"
            else:
                chart_title_date = f"{selected_year}년 전체 누적"
                
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
                             title=f"📈 {chart_title_date} 도축 물량 현황 (TOP 20)",
                             labels={region_col: '지역/도축장', 'THSMON': '도축량(두)', 'LVSTCKSPC_NM': '육종'})
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader(f"🏆 {chart_title_date} 세부 데이터 표")
                rank_df = fig_df.sort_values('THSMON', ascending=False).reset_index(drop=True)
                rank_df.index += 1
                rank_df.columns = ['지역/도축장명', '취급육종', '도축량(두)']
                st.dataframe(rank_df, use_container_width=True)
            else:
                st.info("해당 조건에 맞는 데이터가 없습니다.")

# ----------------- B2C 탭 (실시간 연동 버전) -----------------
with tab_b2c:
    st.markdown("<h3 style='color: #1B2A47; text-align: center;'>🥩 내가 먹는 고기, 어디서 왔을까?</h3>", unsafe_allow_html=True)
    st.caption("⚡ 공공데이터포털(축산물품질평가원) 실시간 API 연동 중")
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        with st.container(border=True):
            trace_input = st.text_input("🔍 이력번호 입력", placeholder="12자리 또는 묶음번호(L~)를 입력하세요")
            
            if st.button("실시간 안심 데이터 조회하기", type="primary", use_container_width=True):
                if trace_input:
                    # ⏳ 서버 통신 중 로딩 애니메이션
                    with st.spinner('축평원 서버에서 실시간으로 데이터를 불러오는 중입니다...'):
                        try:
                            api_url = "http://data.ekape.or.kr/openapi-data/service/user/animalTrace/traceNoSearch"
                            
                            # 🔑 반드시 마이페이지의 '디코딩(Decoding)' 인증키를 넣어주세요!
                            api_key = "67a4fb7c6588efb629a2e9bb65590194497e3bf7e392f0f531f7b5337b91b2e2"
                            
                            params = {
                                "ServiceKey": api_key,
                                "traceNo": trace_input
                            }
                            
                            res = requests.get(api_url, params=params)
                            
                            if "SERVICE KEY IS NOT REGISTERED ERROR" in res.text:
                                st.error("❌ 서버 오류: 인증키가 아직 인식되지 않았습니다.")
                            else:
                                root = ET.fromstring(res.text)
                                items = root.findall('.//item')
                                
                                if items:
                                    st.success("✅ 축산물 이력제 정상 인증 완료! 안전한 고기입니다.")
                                    
                                    # 여러 <item>에 흩어진 정보를 하나의 딕셔너리로 합치기
                                    extracted = {}
                                    for item in items:
                                        for child in item:
                                            if child.text and child.text.strip():
                                                extracted[child.tag] = child.text
                                                
                                    # 화면에 보여줄 핵심 정보 추출
                                    slau = extracted.get('butcheryPlaceNm', '정보 없음')
                                    date = extracted.get('butcheryYmd', '정보 없음')
                                    t_type = extracted.get('lsTypeNm', '정보 없음')
                                    grade = extracted.get('gradeNm', '정보 없음')
                                    addr = extracted.get('farmAddr', '정보 없음')
                                    
                                    # 날짜 포맷팅 (20240616 -> 2024-06-16)
                                    if len(date) == 8 and date.isdigit():
                                        date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                                    
                                    # 결과 출력
                                    c1, c2 = st.columns(2)
                                    with c1:
                                        st.markdown(f"**🏭 도축장명:** {slau}")
                                        st.markdown(f"**📅 도축일자:** {date}")
                                    with c2:
                                        st.markdown(f"**🥩 축종(등급):** {t_type} ({grade})")
                                        st.markdown(f"**🏡 사육지:** {addr}")
                                        
                                    # 전문가용 전체 데이터 토글
                                    with st.expander("🔍 전문가용 상세 이력 정보 전체 보기"):
                                        # ==========================================
                                    # 💡 [여기서부터 교체/추가] 한글 번역 사전 적용
                                    # ==========================================
                                    with st.expander("🔍 전문가용 상세 이력 정보 전체 보기"):
                                        # 정부 API의 영어 키값을 한글로 매핑해주는 사전
                                        kor_mapping = {
                                            "butcheryPlaceNm": "도축장명",
                                            "butcheryPlaceAddr": "도축장 주소",
                                            "butcheryYmd": "도축일자",
                                            "lsTypeNm": "축종 (소의 종류)",
                                            "gradeNm": "등급",
                                            "farmAddr": "사육지/농장 주소",
                                            "corpNo": "사업자번호",
                                            "lotNo": "묶음번호",
                                            "cattleNo": "소 개체번호",
                                            "pigNo": "돼지 이력번호",
                                            "histNo": "가금류(닭/오리) 이력번호",
                                            "birthYmd": "출생일자",
                                            "sexNm": "성별",
                                            "farmerNm": "농장주/소유주명",
                                            "processPlaceNm": "포장처리업소명",
                                            "processPlaceAddr": "포장처리업소 주소",
                                            "inspectPassYn": "위생검사 결과",
                                            "farmUniqueNo": "농장식별번호",
                                            "traceNoType": "이력/묶음 구분",
                                            "infoType": "정보 분류코드",
                                            "regType": "신고구분",
                                            "regYmd": "등록일자"
                                        }
                                        
                                        # 기존 영어 키에 한글 설명을 덧붙인 새로운 딕셔너리 만들기
                                        translated_data = {}
                                        for key, value in extracted.items():
                                            # 사전에 있으면 한글 뜻을 가져오고, 없으면 '기타 정보'로 표시
                                            kor_name = kor_mapping.get(key, "기타 정보")
                                            new_key = f"{key} ({kor_name})"
                                            translated_data[new_key] = value
                                            
                                        # 한글이 포함된 예쁜 데이터로 화면에 출력!
                                        st.json(translated_data)
                                    # ==========================================
                                    # 💡 [여기까지]
                                    # ==========================================
                                        
                                else:
                                    st.warning("⚠️ 입력하신 이력번호에 해당하는 정보가 없습니다. 번호를 다시 확인해주세요.")
                                    
                        except Exception as e:
                            st.error(f"통신 중 에러가 발생했습니다: {e}")
