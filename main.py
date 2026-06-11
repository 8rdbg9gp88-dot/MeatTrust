import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import os
import plotly.express as px
import urllib.parse

# 페이지 기본 설정
st.set_page_config(page_title="MeatTrust 도축 정보 시스템", layout="wide")
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { color: #1B2A47; font-weight: bold; }
    .stTabs [aria-selected="true"] { border-bottom-color: #1B2A47 !important; color: #1B2A47 !important; }
</style>
""", unsafe_allow_html=True)

# 인트로 화면
if "intro_done" not in st.session_state:
    st.markdown("""
        <div style="background-image: linear-gradient(rgba(27, 42, 71, 0.7), rgba(27, 42, 71, 0.7)), url('https://images.unsplash.com/photo-1607623814075-e51df1bd682f?q=80&w=2000&auto=format&fit=crop');
            background-size: cover; height: 80vh; border-radius: 20px; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; text-align: center; margin-bottom: 20px;">
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

# 🟢 1번 API: 농림부 통계 데이터 (MAFRA_API_KEY 사용)
@st.cache_data
def fetch_api_data():
    api_key = os.environ.get("MAFRA_API_KEY")
    if not api_key: return pd.DataFrame()
    url = f"http://211.237.50.150:7080/openapi/{api_key}/xml/Grid_20161216000000000428_1/1/1000"
    try:
        response = requests.get(url)
        root = ET.fromstring(response.content)
        data = [{child.tag: child.text for child in row} for row in root.findall('.//row')]
        df = pd.DataFrame(data)
        if not df.empty and 'THSMON' in df.columns:
            df['THSMON'] = pd.to_numeric(df['THSMON'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

# 🟢 2번 API: 공공데이터포털 이력제 데이터 (TRACE_API_KEY 사용)
@st.cache_data(ttl=60) # 에러나도 60초 뒤에 다시 시도하도록 설정
def fetch_trace_data(trace_no):
    api_key = os.environ.get("TRACE_API_KEY")
    if not api_key: return "NO_KEY"
    
    url = "http://data.ekape.or.kr/openapi-data/service/user/animalTrace/traceNoSearch"
    params = {
        "traceNo": trace_no,
        "ServiceKey": urllib.parse.unquote(api_key) 
    }
    
    try:
        response = requests.get(url, params=params)
        root = ET.fromstring(response.content)
        
        result_code = root.find('.//resultCode')
        if result_code is not None and result_code.text == '00':
            item = root.find('.//item')
            if item is not None:
                return {child.tag: child.text for child in item}
        
        msg = root.find('.//resultMsg')
        error_msg = msg.text if msg is not None else "알 수 없는 응답 형식"
        code = result_code.text if result_code is not None else "XX"
        return f"API_ERROR: [{code}] {error_msg}"
    except Exception as e:
        return f"API_ERROR: 통신 실패 ({str(e)})"

# 메인 화면 그리기
df_api = fetch_api_data()

st.title("🥩 MeatTrust - 전국 축산물 AI 매칭 플랫폼")
st.markdown("---")

tab1, tab2 = st.tabs(["🏢 기업용(B2B) 맞춤 매칭", "🛒 소비자(B2C) 안심 조회"])

with tab1:
    st.subheader("📊 실시간 시장 통계 대시보드")
    g_col1, g_col2 = st.columns(2)
    if not df_api.empty:
        with g_col1:
            fig_pie = px.pie(df_api.groupby('CTRD_NM')['THSMON'].sum().reset_index(), values='THSMON', names='CTRD_NM', title='📍 지역별 총 도축 물량 비중', color_discrete_sequence=px.colors.sequential.RdBu)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        with g_col2:
            fig_bar = px.bar(df_api.groupby('LVSTCKSPC_NM')['THSMON'].sum().reset_index().sort_values(by='THSMON', ascending=False), x='LVSTCKSPC_NM', y='THSMON', title='🥩 육종별 도축 규모 (단위: 두)', color='THSMON', color_continuous_scale='Blues')
            st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

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
            if region_filter != "전국":
                filtered_df = filtered_df[filtered_df['CTRD_NM'].str.contains(region_filter.replace("/", "|"), na=False)]
            if meat_type_filter:
                filtered_df = filtered_df[filtered_df['LVSTCKSPC_NM'].isin(meat_type_filter)]
                
            if not filtered_df.empty:
                filtered_df = filtered_df.groupby(['SLAU_PLACE_NM', 'CTRD_NM']).agg({'LVSTCKSPC_NM': lambda x: ', '.join(sorted(set(x))), 'THSMON': 'sum'}).reset_index()
                filtered_df = filtered_df.sort_values(by='THSMON' if sort_by == "도축 물량순(규모)" else 'SLAU_PLACE_NM', ascending=(sort_by != "도축 물량순(규모)"))

                medals = ["🥇 1위", "🥈 2위", "🥉 3위"]
                for i, (index, row) in enumerate(filtered_df.head(3).iterrows()):
                    with st.container(border=True):
                        st.markdown(f"<h3 style='color: #1B2A47;'>{medals[i]}: {row['SLAU_PLACE_NM']}</h3>", unsafe_allow_html=True)
                        st.write(f"📍 지역: {row['CTRD_NM']} | 🥩 취급: {row['LVSTCKSPC_NM']} | 📦 당월 도축량: {int(row['THSMON']):,}두")
                        
                        with st.popover("📞 이 업체에 견적/주문 문의하기"):
                            st.markdown(f"**[{row['SLAU_PLACE_NM']}] 문의 방식 선택**")
                            st.link_button("📱 바로 전화 걸기", "tel:010-0000-0000", use_container_width=True)
                            st.divider()
                            st.markdown("💬 **문자 견적서 자동 완성**")
                            q_type = st.selectbox("문의 육종", row['LVSTCKSPC_NM'].split(', '), key=f"q_type_{i}")
                            q_amount = st.text_input("필요 수량", placeholder="예: 돼지 반마리, 100kg", key=f"q_amt_{i}")
                            q_memo = st.text_input("추가 요청사항", placeholder="예: 구이용으로 손질 부탁드립니다.", key=f"q_memo_{i}")
                            sms_text = f"[MeatTrust 견적문의]\n- 업체명: {row['SLAU_PLACE_NM']}\n- 육종: {q_type}\n- 수량: {q_amount}\n- 요청사항: {q_memo}"
                            sms_link = f"sms:010-0000-0000?body={urllib.parse.quote(sms_text)}"
                            st.link_button("✉️ 서식대로 문자 보내기", sms_link, use_container_width=True)
            else:
                st.info("조건에 맞는 업체가 없습니다.")

with tab2:
    st.markdown("<h3 style='text-align: center; color: #1B2A47;'>내가 먹는 고기 출처 및 위생 점수 조회</h3>", unsafe_allow_html=True)
    search_type = st.radio("검색 기준을 선택하세요", ["🏭 업체명으로 검색", "🥩 고기 이력번호(바코드)로 검색"], horizontal=True)
    
    with st.form("search_form"):
        if search_type == "🏭 업체명으로 검색":
            search_query = st.text_input("", placeholder="예: 삼정산업, 우성식품")
        else:
            search_query = st.text_input("", placeholder="포장지에 적힌 12자리 이력번호를 숫자만 입력하세요 (예: 002144366294)")
            
        submit_button = st.form_submit_button("🔍 안심 데이터 조회하기", use_container_width=True)
        
    if submit_button:
        if search_type == "🥩 고기 이력번호(바코드)로 검색":
            if search_query:
                trace_info = fetch_trace_data(search_query)
                if trace_info == "NO_KEY":
                    st.warning("🚧 서버 설정에 'TRACE_API_KEY'가 등록되지 않았습니다.")
                elif isinstance(trace_info, str) and trace_info.startswith("API_ERROR:"):
                    st.error(f"⚠️ 에러 발생! 아래 메시지를 확인하세요.\n{trace_info}")
                elif isinstance(trace_info, dict):
                    st.success("✅ 고기 이력 정보 조회가 완료되었습니다!")
                    with st.container(border=True):
                        st.markdown(f"#### 🥩 이력번호: {search_query}")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**도축장명:** {trace_info.get('slaughterNm', '정보 없음')}")
                            st.write(f"**도축일자:** {trace_info.get('slaughterDate', '정보 없음')}")
                        with col_b:
                            st.write(f"**축종:** {trace_info.get('lsTypeNm', '정보 없음')}")
                            st.write(f"**등급:** {trace_info.get('gradeNm', '정보 없음')}")
                else:
                    st.error("입력하신 이력번호에 해당하는 정보를 찾을 수 없습니다.")
            else:
                st.warning("이력번호를 입력해 주세요.")
