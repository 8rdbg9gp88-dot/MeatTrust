import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv
import plotly.express as px

load_dotenv()

# 1. 페이지 기본 설정
st.set_page_config(page_title="MeatTrust 도축 정보 시스템", layout="wide")

# 2. 테마 커스터마이징
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { color: #1B2A47; font-weight: bold; }
    .stTabs [aria-selected="true"] { border-bottom-color: #1B2A47 !important; color: #1B2A47 !important; }
</style>
""", unsafe_allow_html=True)

# 3. 인트로 화면
if "intro_done" not in st.session_state:
    st.markdown("""
        <div style="
            background-image: linear-gradient(rgba(27, 42, 71, 0.7), rgba(27, 42, 71, 0.7)), url('https://images.unsplash.com/photo-1607623814075-e51df1bd682f?q=80&w=2000&auto=format&fit=crop');
            background-size: cover; height: 80vh; border-radius: 20px;
            display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; text-align: center; margin-bottom: 20px;">
            <h1 style='font-size: 4rem; margin-bottom: 10px; color: white;'>🥩 도축 정보 시스템</h1>
            <p style='font-size: 1.5rem; color: #E0E0E0;'>안전하고 투명한 전국 축산물 매칭 플랫폼</p>
        </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 시스템 입장하기", use_container_width=True):
            st.session_state.intro_done = True
            st.rerun()
    st.stop()

# 4. 공공데이터 가져오기
@st.cache_data
def fetch_api_data():
    api_key = os.environ.get("MAFRA_API_KEY")
    if not api_key: return pd.DataFrame()
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
            if 'THSMON' in df.columns:
                df['THSMON'] = pd.to_numeric(df['THSMON'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

df_api = fetch_api_data()

# 5. 메인 화면 UI
st.title("🥩 MeatTrust - 전국 축산물 AI 매칭 플랫폼")
st.markdown("---")

tab1, tab2 = st.tabs(["🏢 기업용(B2B) 맞춤 매칭", "🛒 소비자(B2C) 안심 조회"])

# --- 기업용(B2B) 탭 ---
with tab1:
    
    # ✅ 새로 추가된 통계 그래프 구역 (상단에 예쁘게 배치!)
    st.subheader("📊 실시간 시장 통계 대시보드")
    g_col1, g_col2 = st.columns(2)

    if not df_api.empty:
        with g_col1:
            region_data = df_api.groupby('CTRD_NM')['THSMON'].sum().reset_index()
            fig_pie = px.pie(region_data, values='THSMON', names='CTRD_NM', 
                             title='📍 지역별 총 도축 물량 비중',
                             color_discrete_sequence=px.colors.sequential.RdBu)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        with g_col2:
            meat_data = df_api.groupby('LVSTCKSPC_NM')['THSMON'].sum().reset_index().sort_values(by='THSMON', ascending=False)
            fig_bar = px.bar(meat_data, x='LVSTCKSPC_NM', y='THSMON', 
                             title='🥩 육종별 도축 규모 (단위: 두)',
                             labels={'LVSTCKSPC_NM': '육종', 'THSMON': '도축량'},
                             color='THSMON', color_continuous_scale='Blues')
            st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # ✅ 네가 원했던 기존 완벽한 필터링 & 순위표 구역 복구!
    col1, col2 = st.columns([1, 3]) 
    
    with col1:
        st.subheader("🔍 조건 검색")
        region_filter = st.selectbox("지역 선택", ["전국", "서울/경기/인천", "강원", "충청/대전/세종", "전라/광주", "경상/부산/대구/울산", "제주"])
        meat_type_filter = st.multiselect("육종 선택", ["돼지", "소", "닭", "오리"], default=["돼지", "소"])
        sort_by = st.radio("정렬 기준", ["도축 물량순(규모)", "업체명 가나다순"])
        
    with col2:
        st.subheader("🏆 조건별 실시간 우수 업체 TOP 3")
        
        if not df_api.empty:
            filtered_df = df_api.copy()
            
            # 지역 및 육종 필터링 로직
            if region_filter != "전국":
                region_keywords = region_filter.replace("/", "|")
                filtered_df = filtered_df[filtered_df['CTRD_NM'].str.contains(region_keywords, na=False)]
            if meat_type_filter:
                filtered_df = filtered_df[filtered_df['LVSTCKSPC_NM'].isin(meat_type_filter)]
                
            # 정렬
            if sort_by == "도축 물량순(규모)":
                filtered_df = filtered_df.sort_values(by='THSMON', ascending=False)
            else:
                filtered_df = filtered_df.sort_values(by='SLAU_PLACE_NM', ascending=True)

            if filtered_df.empty:
                st.info("조건에 맞는 업체가 없습니다. 필터를 변경해 보세요.")
            else:
                top_3 = filtered_df.head(3)
                medals = ["🥇 1위", "🥈 2위", "🥉 3위"]
                
                for i, (index, row) in enumerate(top_3.iterrows()):
                    with st.container(border=True):
                        st.markdown(f"<h3 style='color: #1B2A47;'>{medals[i]}: {row['SLAU_PLACE_NM']}</h3>", unsafe_allow_html=True)
                        st.write(f"📍 지역: {row['CTRD_NM']} | 🥩 주요 취급: {row['LVSTCKSPC_NM']} | 📦 당월 도축량: {int(row['THSMON']):,}두")
                        st.link_button("📞 이 업체에 전화/문자 문의하기", "tel:010-0000-0000")
        else:
            st.warning("데이터를 불러오는 중 문제가 발생했습니다.")

    st.divider()
    
    st.subheader("📈 실시간 도축 업체 전체 순위표")
    if not df_api.empty:
        clean_df = df_api[['CTRD_NM', 'SLAU_PLACE_NM', 'LVSTCKSPC_NM', 'THSMON']].copy()
        clean_df.columns = ['지역', '업체명', '취급 육종', '당월 도축량(두)']
        clean_df = clean_df.sort_values(by='당월 도축량(두)', ascending=False).reset_index(drop=True)
        clean_df.index = clean_df.index + 1
        st.dataframe(clean_df, use_container_width=True)

# --- 소비자(B2C) 탭 ---
with tab2:
    st.markdown("<h3 style='text-align: center; color: #1B2A47;'>내가 먹는 고기 출처 및 위생 점수 조회</h3>", unsafe_allow_html=True)
    
    with st.form("search_form"):
        search_query = st.text_input("", placeholder="업체명을 정확히 입력하세요 (예: 삼정산업, 우성식품)")
        submit_button = st.form_submit_button("🔍 안심 데이터 조회하기", use_container_width=True)
        
    if submit_button:
        if search_query and not df_api.empty:
            result_df = df_api[df_api['SLAU_PLACE_NM'].str.contains(search_query, na=False)]
            if not result_df.empty:
                st.success(f"'{search_query}'(으)로 검색된 결과입니다.")
                for _, row in result_df.iterrows():
                    with st.container(border=True):
                        st.markdown(f"#### 🏭 {row['SLAU_PLACE_NM']}")
                        st.write(f"**위치:** {row['CTRD_NM']}")
                        st.write(f"**취급 육류:** {row['LVSTCKSPC_NM']}")
                        st.write("**안심 식별 코드:** 정상 등록 업체 ✅")
            else:
                st.error("일치하는 업체 정보가 없습니다. 다시 확인해 주세요.")
        else:
            st.warning("검색어를 입력해 주세요.")
