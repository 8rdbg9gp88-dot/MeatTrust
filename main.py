
import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv

# 비밀 금고에서 키 불러오기
load_dotenv()

# 1. 페이지 기본 설정 (가장 먼저 와야 함)
st.set_page_config(page_title="MeatTrust 도축 정보 시스템", layout="wide")

# 2. 네이비 & 화이트 테마 및 인트로 화면 CSS 주입
st.markdown("""
<style>
	/* 상단 헤더 숨기기 및 네이비 톤 포인트 */
	.stTabs [data-baseweb="tab-list"] { gap: 24px; }
	.stTabs [data-baseweb="tab"] { color: #1B2A47; font-weight: bold; }
	.stTabs [aria-selected="true"] { border-bottom-color: #1B2A47 !important; color: #1B2A47 !important; }
</style>
""", unsafe_allow_html=True)

# 3. 인트로(스플래시) 화면 제어 (처음 접속했을 때만 보임)
if "intro_done" not in st.session_state:
	st.markdown("""
		<div style="
			background-image: linear-gradient(rgba(27, 42, 71, 0.7), rgba(27, 42, 71, 0.7)), url('https://images.unsplash.com/photo-1607623814075-e51df1bd682f?q=80&w=2000&auto=format&fit=crop');
			background-size: cover;
			height: 80vh;
			border-radius: 20px;
			display: flex;
			flex-direction: column;
			justify-content: center;
			align-items: center;
			color: white;
			text-align: center;
			margin-bottom: 20px;
		">
			<h1 style='font-size: 4rem; margin-bottom: 10px; color: white;'>🥩 도축 정보 시스템</h1>
			<p style='font-size: 1.5rem; color: #E0E0E0;'>안전하고 투명한 전국 축산물 매칭 플랫폼</p>
		</div>
	""", unsafe_allow_html=True)
    
	col1, col2, col3 = st.columns([1, 1, 1])
	with col2:
		if st.button("🚀 시스템 입장하기", use_container_width=True):
			st.session_state.intro_done = True
			st.rerun()
	st.stop() # 입장 버튼을 누르기 전까지는 아래 코드를 실행하지 않음

# 4. 공공데이터 가져오기 및 전처리 함수
@st.cache_data
def fetch_api_data():
	api_key = os.environ.get("MAFRA_API_KEY")
	if not api_key:
		return pd.DataFrame()
    
	url = f"http://211.237.50.150:7080/openapi/{api_key}/xml/Grid_20161216000000000428_1/1/1000"
    
	try:
		response = requests.get(url)
		response.raise_for_status()
		root = ET.fromstring(response.content)
		data = []
		for row in root.findall('.//row'):
			item = {child.tag: child.text for child in row}
			data.append(item)
            
		df = pd.DataFrame(data)
		if df.empty: return df
        
		# 텍스트로 된 도축량 데이터를 숫자로 변환 (순위 정렬을 위해 필수!)
		if 'THSMON' in df.columns:
			df['THSMON'] = pd.to_numeric(df['THSMON'], errors='coerce').fillna(0)
            
		return df
	except:
		return pd.DataFrame()

# 데이터 불러오기
df_api = fetch_api_data()

# 5. 메인 화면 UI
st.title("🥩 MeatTrust - 전국 축산물 AI 매칭 플랫폼")
st.markdown("---")

tab1, tab2 = st.tabs(["🏢 기업용(B2B) 맞춤 매칭", "🛒 소비자(B2C) 안심 조회"])

# --- 기업용(B2B) 탭 ---
with tab1:
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
            
			# 지역 필터링 로직 (단어 포함 여부로 검색)
			if region_filter != "전국":
				region_keywords = region_filter.replace("/", "|") # "서울|경기|인천" 형태로 변환
				filtered_df = filtered_df[filtered_df['CTRD_NM'].str.contains(region_keywords, na=False)]
                
			# 육종 필터링 로직
			if meat_type_filter:
				filtered_df = filtered_df[filtered_df['LVSTCKSPC_NM'].isin(meat_type_filter)]
                
			# 정렬 로직
			if sort_by == "도축 물량순(규모)":
				filtered_df = filtered_df.sort_values(by='THSMON', ascending=False)
			else:
				filtered_df = filtered_df.sort_values(by='SLAU_PLACE_NM', ascending=True)

			# 필터링된 결과 화면에 뿌리기
			if filtered_df.empty:
				st.info("조건에 맞는 업체가 없습니다. 필터를 변경해 보세요.")
			else:
				top_3 = filtered_df.head(3)
				medals = ["🥇 1위", "🥈 2위", "🥉 3위"]
                
				for i, (index, row) in enumerate(top_3.iterrows()):
					with st.container(border=True):
						st.markdown(f"<h3 style='color: #1B2A47;'>{medals[i]}: {row['SLAU_PLACE_NM']}</h3>", unsafe_allow_html=True)
						st.write(f"📍 지역: {row['CTRD_NM']} | 🥩 주요 취급: {row['LVSTCKSPC_NM']} | 📦 당월 도축량: {int(row['THSMON']):,}두")
						# 전화 걸기 기능 (모바일에서 클릭 시 다이얼 앱으로 연결됨)
						st.link_button("📞 이 업체에 전화/문자 문의하기", "tel:010-0000-0000")
		else:
			st.warning("데이터를 불러오는 중 문제가 발생했습니다.")

	st.divider()
    
	# 더러운 원본 데이터 대신, 깔끔하게 정리된 순위표 제공
	st.subheader("📈 실시간 도축 업체 전체 순위표")
	if not df_api.empty:
		clean_df = df_api[['CTRD_NM', 'SLAU_PLACE_NM', 'LVSTCKSPC_NM', 'THSMON']].copy()
		clean_df.columns = ['지역', '업체명', '취급 육종', '당월 도축량(두)']
		clean_df = clean_df.sort_values(by='당월 도축량(두)', ascending=False).reset_index(drop=True)
		clean_df.index = clean_df.index + 1 # 1위부터 시작하도록 인덱스 조정
		st.dataframe(clean_df, use_container_width=True)

# --- 소비자(B2C) 탭 ---
with tab2:
	st.markdown("<h3 style='text-align: center; color: #1B2A47;'>내가 먹는 고기 출처 및 위생 점수 조회</h3>", unsafe_allow_html=True)
    
	# 폼(Form)을 사용해서 엔터를 치거나 버튼을 눌렀을 때만 작동하게 함
	with st.form("search_form"):
		search_query = st.text_input("", placeholder="업체명을 정확히 입력하세요 (예: 삼정산업, 우성식품)")
		submit_button = st.form_submit_button("🔍 안심 데이터 조회하기", use_container_width=True)
        
	if submit_button:
		if search_query and not df_api.empty:
			# 검색어와 업체명이 일치하는 데이터 찾기
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
