import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. 설정 및 데이터 로드
# ==========================================
st.set_page_config(page_title="AI Trend Shift Analysis", layout="wide")

st.title("📊 AI 관심도의 구조적 이동: 2023 vs 2025")

st.markdown("""
**Wikipedia Pageviews** 데이터를 기반으로, ChatGPT 등장 초기(2023)와 정착기(2025)의 
사회적 관심사가 어떻게 **기술(Tech)**에서 **사회적 영향(Social Impact)**으로 이동했는지 분석합니다.
""")

@st.cache_data
def load_data():
    # 데이터 로드 (실제 파일명 사용)
    # 제목에 쉼표가 포함된 경우를 처리: 마지막 2개 필드가 조회수와 카테고리
    def parse_csv_with_comma_in_title(filepath):
        rows = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # 마지막 2개 쉼표로만 분리 (제목에 쉼표가 있어도 처리 가능)
                parts = line.rsplit(',', 2)
                if len(parts) == 3:
                    rows.append({'title': parts[0], 'views': parts[1], 'category': parts[2]})
        return pd.DataFrame(rows)
    
    df_23 = parse_csv_with_comma_in_title("data/spark_2023.csv")
    df_25 = parse_csv_with_comma_in_title("data/spark_2025.csv")
    
    # views를 숫자로 변환 (\N 같은 값도 처리)
    df_23['views'] = pd.to_numeric(df_23['views'].replace('\\N', '0'), errors='coerce').fillna(0).astype(int)
    df_25['views'] = pd.to_numeric(df_25['views'].replace('\\N', '0'), errors='coerce').fillna(0).astype(int)
    
    # 컬럼명 통일 (Category 컬럼은 나중에 재할당하므로 여기서는 제외)
    df_23 = df_23[['title', 'views']].copy()
    df_25 = df_25[['title', 'views']].copy()
    df_23.columns = ['title', 'views_2023']
    df_25.columns = ['title', 'views_2025']
    
    # 노이즈 제거 (스포츠, 파일 등)
    # "Playoff"는 제거하지만 "layoff"는 보존 (Social_Impact 카테고리)
    def is_clean(title):
        title_str = str(title).lower()
        
        # "playoff" 체크 (단, "layoff"는 제외)
        if 'playoff' in title_str and 'layoff' not in title_str:
            return False
        
        # 스포츠 관련 키워드 (대폭 확장)
        sports_keywords = [
            'nfl', 'nba', 'nhl', 'mlb', 'mls',  # 리그명
            'championship', 'cup', 'tournament', 'super bowl', 'world cup',
            'college football', 'college basketball', 'college baseball',
            'football', 'basketball', 'baseball', 'soccer', 'hockey',
            'olympics', 'olympic', 'fifa', 'uefa',
            'playoff', 'playoffs', 'ㅃsemifinal', 'final', 'quarterfinal',
            'season', 'game', 'match', 'league', 'team', 'player', 'coach',
            'stadium', 'arena', 'field', 'court', 'pitch'
        ]
        
        # 스포츠 키워드가 포함되어 있는지 체크
        for sport in sports_keywords:
            if sport in title_str:
                # 예외: "layoff"는 Social_Impact 카테고리이므로 제외
                if sport == 'playoff' and 'layoff' in title_str:
                    continue
                return False
        
        # 기타 노이즈 키워드 체크
        noise_keywords = ['file:', 'wikipedia:', 'user:', 'talk:', 'template:', 
                         'category:', 'help:', 'portal:', 'special:', 'dibiase', 'tobias', 'len_bias']
        for noise in noise_keywords:
            if noise in title_str:
                return False
        
        return True
    
    # 원본 총합 저장 (필터링 전)
    original_total_23 = df_23['views_2023'].sum()
    original_total_25 = df_25['views_2025'].sum()
    
    df_23 = df_23[df_23['title'].apply(is_clean)]
    df_25 = df_25[df_25['title'].apply(is_clean)]
    
    # 데이터 병합 (Outer Join)
    df_merged = pd.merge(df_23, df_25, on='title', how='outer').fillna(0)
    
    return df_merged, original_total_23, original_total_25

raw_df, original_total_23, original_total_25 = load_data()

# ==========================================
# 2. 키워드 카테고리 정의 (Config에서 가져옴)
# ==========================================
CATEGORIES = {
    "Technology": [
        "Artificial_intelligence", "Machine_learning", "Deep_learning", "Generative_AI", 
        "ChatGPT", "OpenAI", "GPT-4", "Large_language_model", "Neural_network", "Transformer_(machine_learning_model)",
        "Gemini_(chatbot)", "Grok_(chatbot)"
    ],
    "Application": [
        "Automation", "Prompt_engineering", "Chatbot", "AI_art", "GitHub_Copilot", 
        "Midjourney", "Stable_Diffusion", "Robotics", "Virtual_assistant"
    ],
    "Social_Impact": [
        "Job_loss", "Technological_unemployment", "Labor_market", "Layoff", 
        "Universal_basic_income", "AI_ethics", "Copyright", "Deepfake", "Hallucination", "Bias"
    ]
}

# 카테고리 매핑 함수
def assign_category(title):
    for cat, keywords in CATEGORIES.items():
        for k in keywords:
            if k.lower() in str(title).lower():
                return cat
    return "Other"

raw_df['Category'] = raw_df['title'].apply(assign_category)

# 분석 대상 키워드만 필터링 (Other 제외)
df_analyzed = raw_df[raw_df['Category'] != 'Other'].copy()

# 변화율 계산 (2023 -> 2025)
df_analyzed['change'] = df_analyzed['views_2025'] - df_analyzed['views_2023']
df_analyzed['change_pct'] = ((df_analyzed['views_2025'] - df_analyzed['views_2023']) / 
                              df_analyzed['views_2023'].replace(0, 1) * 100).round(1)
df_analyzed['change_pct'] = df_analyzed['change_pct'].replace([float('inf'), float('-inf')], 0)

# ==========================================
# 3. 대시보드 구성
# ==========================================

# ChatGPT 제외 옵션
st.sidebar.markdown("### ⚙️ 필터 옵션")
exclude_chatgpt = st.sidebar.checkbox("ChatGPT 제외", value=False, 
                                      help="ChatGPT 관련 키워드를 분석에서 제외합니다. 다른 키워드들의 비교가 더 쉬워집니다.")

# ChatGPT 필터링 함수
def filter_chatgpt(df, exclude):
    if exclude:
        # ChatGPT 관련 키워드 제외
        chatgpt_keywords = ['chatgpt', 'chat_gpt', 'chat-gpt']
        mask = df['title'].str.lower().str.contains('|'.join(chatgpt_keywords), na=False)
        return df[~mask].copy()
    return df.copy()

# 필터링된 데이터
df_filtered = filter_chatgpt(df_analyzed, exclude_chatgpt)

# 전체 통계 계산 (원본 데이터 총합 사용)
total_views_23 = original_total_23
total_views_25 = original_total_25
total_change_pct = ((total_views_25 - total_views_23) / total_views_23 * 100) if total_views_23 > 0 else 0

# 카테고리별 점유율 계산 (필터링된 데이터의 카테고리별 합계를 원본 총합으로 나눔)
cat_share_23 = df_filtered.groupby('Category')['views_2023'].sum() / original_total_23 * 100 if original_total_23 > 0 else pd.Series()
cat_share_25 = df_filtered.groupby('Category')['views_2025'].sum() / original_total_25 * 100 if original_total_25 > 0 else pd.Series()

# KPI 카드 표시
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("2023년 총 조회수", f"{total_views_23:,.0f}", delta=None)

with col2:
    st.metric("2025년 총 조회수", f"{total_views_25:,.0f}", 
              delta=f"{total_change_pct:+.1f}%")

with col3:
    tech_share_change = cat_share_25.get('Technology', 0) - cat_share_23.get('Technology', 0)
    st.metric("Technology 점유율", f"{cat_share_25.get('Technology', 0):.1f}%", 
              delta=f"{tech_share_change:+.1f}%p")

with col4:
    social_share_change = cat_share_25.get('Social_Impact', 0) - cat_share_23.get('Social_Impact', 0)
    st.metric("Social Impact 점유율", f"{cat_share_25.get('Social_Impact', 0):.1f}%", 
              delta=f"{social_share_change:+.1f}%p")

st.markdown("---")

# [TAB 1] 핵심 요약
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Trend Overview", "🕸️ Category Shift", "📊 Deep Insights", "🔍 Keyword Search", "📋 Raw Data"])

with tab1:
    st.header("🔥 Top Keywords Ranking Change")
    if exclude_chatgpt:
        st.info("ℹ️ ChatGPT 관련 키워드가 제외된 분석입니다.")
    
    # 카테고리 필터 추가 (체크박스)
    st.markdown("**📂 카테고리 필터**")
    available_categories = sorted(df_filtered['Category'].unique().tolist())
    
    # 체크박스로 각 카테고리 표시
    col_filter = st.columns(len(available_categories))
    selected_categories = []
    
    for idx, cat in enumerate(available_categories):
        with col_filter[idx]:
            if st.checkbox(cat, value=True, key=f"cat_filter_{cat}"):
                selected_categories.append(cat)
    
    # 카테고리 필터링 적용
    if len(selected_categories) == 0:
        # 아무것도 선택하지 않으면 전체 표시
        df_trend = df_filtered.copy()
        filter_info = "전체 카테고리"
    else:
        df_trend = df_filtered[df_filtered['Category'].isin(selected_categories)].copy()
        filter_info = ", ".join(selected_categories)
    
    if len(df_trend) == 0:
        st.warning("선택한 카테고리 조건에 해당하는 키워드가 없습니다.")
    else:
        st.caption(f"📊 현재 표시 중: {filter_info} ({len(df_trend)}개 키워드)")
        
        # 상위 N개 선택
        top_n = st.slider("표시할 상위 키워드 개수", 5, min(30, len(df_trend)), 10)
        
        # 2023년과 2025년 각각의 Top N 추출 (카테고리 필터링된 데이터 사용)
        top_23 = df_trend.nlargest(top_n, 'views_2023')
        top_25 = df_trend.nlargest(top_n, 'views_2025')
    
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("2023년 (도입기) Top Keywords")
            if len(top_23) > 0:
                fig23 = px.bar(top_23, x='views_2023', y='title', orientation='h', 
                               color='Category', title="Feb 2023 Views", 
                               category_orders={"title": top_23['title'].tolist()},
                               color_discrete_map={'Technology': '#1f77b4', 'Application': '#ff7f0e', 'Social_Impact': '#2ca02c'})
                fig23.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
                st.plotly_chart(fig23, use_container_width=True)
            else:
                st.info("2023년 데이터가 없습니다.")
            
        with col2:
            st.subheader("2025년 (정착기) Top Keywords")
            if len(top_25) > 0:
                fig25 = px.bar(top_25, x='views_2025', y='title', orientation='h', 
                               color='Category', title="Sep 2025 Views",
                               color_discrete_map={'Technology': '#1f77b4', 'Application': '#ff7f0e', 'Social_Impact': '#2ca02c'})
                fig25.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
                st.plotly_chart(fig25, use_container_width=True)
            else:
                st.info("2025년 데이터가 없습니다.")
        
        # 변화율이 큰 키워드 표시 (카테고리 필터링된 데이터 사용)
        st.subheader("📊 변화율이 큰 키워드")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("**🚀 급상승 키워드 (2023 → 2025)**")
            rising_df = df_trend[df_trend['views_2023'] > 0]
            if len(rising_df) > 0:
                rising = rising_df.nlargest(5, 'change_pct')[['title', 'Category', 'views_2023', 'views_2025', 'change_pct']]
                rising_display = rising.copy()
                rising_display.columns = ['키워드', '카테고리', '2023 조회수', '2025 조회수', '변화율(%)']
                st.dataframe(rising_display, use_container_width=True, hide_index=True)
            else:
                st.info("급상승 키워드가 없습니다.")
        
        with col_b:
            st.markdown("**📉 급하락 키워드 (2023 → 2025)**")
            falling_df = df_trend[df_trend['views_2023'] > 0]
            if len(falling_df) > 0:
                falling = falling_df.nsmallest(5, 'change_pct')[['title', 'Category', 'views_2023', 'views_2025', 'change_pct']]
                falling_display = falling.copy()
                falling_display.columns = ['키워드', '카테고리', '2023 조회수', '2025 조회수', '변화율(%)']
                st.dataframe(falling_display, use_container_width=True, hide_index=True)
            else:
                st.info("급하락 키워드가 없습니다.")

with tab2:
    st.header("💡 관심의 구조적 이동 (Category Shift)")
    if exclude_chatgpt:
        st.info("ℹ️ ChatGPT 관련 키워드가 제외된 분석입니다.")
    
    # 카테고리별 총 조회수 집계 (필터링된 데이터 사용)
    cat_group = df_filtered.groupby('Category')[['views_2023', 'views_2025']].sum().reset_index()
    cat_group['change'] = cat_group['views_2025'] - cat_group['views_2023']
    cat_group['change_pct'] = ((cat_group['views_2025'] - cat_group['views_2023']) / 
                                cat_group['views_2023'].replace(0, 1) * 100).round(1)
    
    # 점유율 계산
    cat_group['share_2023'] = (cat_group['views_2023'] / total_views_23 * 100).round(1)
    cat_group['share_2025'] = (cat_group['views_2025'] / total_views_25 * 100).round(1)
    cat_group['share_change'] = cat_group['share_2025'] - cat_group['share_2023']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 그룹 막대 그래프
        cat_long = pd.melt(cat_group, id_vars=['Category'], 
                          value_vars=['views_2023', 'views_2025'],
                          var_name='Year', value_name='Views')
        cat_long['Year'] = cat_long['Year'].map({'views_2023': '2023', 'views_2025': '2025'})
        
        fig_cat = px.bar(cat_long, x='Category', y='Views', color='Year', barmode='group',
                         title="카테고리별 조회수 총량 변화",
                         text_auto='.2s',
                         color_discrete_map={'2023': '#1f77b4', '2025': '#ff7f0e'})
        fig_cat.update_layout(height=400)
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        # 점유율 변화
        share_long = pd.melt(cat_group, id_vars=['Category'],
                            value_vars=['share_2023', 'share_2025'],
                            var_name='Year', value_name='Share')
        share_long['Year'] = share_long['Year'].map({'share_2023': '2023', 'share_2025': '2025'})
        
        fig_share = px.bar(share_long, x='Category', y='Share', color='Year', barmode='group',
                          title="카테고리별 점유율 변화 (%)",
                          text_auto='.1f',
                          color_discrete_map={'2023': '#1f77b4', '2025': '#ff7f0e'})
        fig_share.update_layout(yaxis_title="점유율 (%)", height=400)
        st.plotly_chart(fig_share, use_container_width=True)
    
    # 상세 통계 테이블
    st.subheader("📊 카테고리별 상세 통계")
    cat_stats = cat_group[['Category', 'views_2023', 'views_2025', 'change', 'change_pct', 
                          'share_2023', 'share_2025', 'share_change']].copy()
    cat_stats.columns = ['카테고리', '2023 조회수', '2025 조회수', '변화량', '변화율(%)', 
                        '2023 점유율(%)', '2025 점유율(%)', '점유율 변화(p)']
    cat_stats = cat_stats.round(1)
    st.dataframe(cat_stats, use_container_width=True, hide_index=True)
    
    # 인사이트
    tech_change = cat_group[cat_group['Category'] == 'Technology']['change_pct'].values[0] if len(cat_group[cat_group['Category'] == 'Technology']) > 0 else 0
    social_change = cat_group[cat_group['Category'] == 'Social_Impact']['change_pct'].values[0] if len(cat_group[cat_group['Category'] == 'Social_Impact']) > 0 else 0
    
    st.success(f"""
    **🔍 핵심 인사이트:**
    
    - **Technology 카테고리**: {tech_change:+.1f}% 변화 | 점유율 {cat_group[cat_group['Category'] == 'Technology']['share_change'].values[0] if len(cat_group[cat_group['Category'] == 'Technology']) > 0 else 0:+.1f}%p 변화
      → ChatGPT 등장 초기 폭발적 관심 이후, 기술 자체에 대한 관심은 상대적으로 안정화 단계
    
    - **Social_Impact 카테고리**: {social_change:+.1f}% 변화 | 점유율 {cat_group[cat_group['Category'] == 'Social_Impact']['share_change'].values[0] if len(cat_group[cat_group['Category'] == 'Social_Impact']) > 0 else 0:+.1f}%p 변화
      → AI가 사회에 미치는 영향(고용, 윤리, 저작권 등)에 대한 관심이 상대적으로 증가하는 추세
    
    - **Application 카테고리**: {cat_group[cat_group['Category'] == 'Application']['change_pct'].values[0] if len(cat_group[cat_group['Category'] == 'Application']) > 0 else 0:+.1f}% 변화
      → 실제 활용 사례에 대한 관심 변화 추이
    """)

with tab3:
    st.header("📊 Deep Insights: 변화 패턴 분석")
    if exclude_chatgpt:
        st.info("ℹ️ ChatGPT 관련 키워드가 제외된 분석입니다.")
    
    # 산점도: 2023 vs 2025
    st.subheader("🔄 키워드별 변화 패턴 (산점도)")
    # size는 0 이상의 값만 허용하므로 절댓값 사용 (필터링된 데이터 사용)
    df_scatter = df_filtered.copy()
    df_scatter['abs_change'] = df_scatter['change'].abs()
    
    fig_scatter = px.scatter(df_scatter, x='views_2023', y='views_2025', 
                            color='Category', size='abs_change',
                            hover_data=['title', 'change_pct', 'change'],
                            title="2023년 조회수 vs 2025년 조회수 (점 크기 = 변화량의 절댓값)",
                            labels={'views_2023': '2023년 조회수', 'views_2025': '2025년 조회수'},
                            color_discrete_map={'Technology': '#1f77b4', 'Application': '#ff7f0e', 'Social_Impact': '#2ca02c'})
    
    # 대각선 추가 (변화 없음 기준선)
    max_val = max(df_filtered['views_2023'].max(), df_filtered['views_2025'].max())
    fig_scatter.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], 
                                   mode='lines', name='변화 없음',
                                   line=dict(color='gray', dash='dash')))
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.caption("💡 대각선 위쪽: 증가한 키워드 | 아래쪽: 감소한 키워드")
    
    # 카테고리별 평균 변화율
    st.subheader("📈 카테고리별 평균 변화율")
    cat_avg_change = df_filtered.groupby('Category').agg({
        'change_pct': 'mean',
        'change': 'mean',
        'views_2023': 'mean',
        'views_2025': 'mean'
    }).reset_index()
    cat_avg_change.columns = ['카테고리', '평균 변화율(%)', '평균 변화량', '평균 2023 조회수', '평균 2025 조회수']
    cat_avg_change = cat_avg_change.round(1)
    st.dataframe(cat_avg_change, use_container_width=True, hide_index=True)
    
    # 새로운 키워드 (2023에는 없었지만 2025에 등장)
    st.subheader("✨ 신규 등장 키워드 (2023년 0건 → 2025년 등장)")
    new_keywords = df_filtered[(df_filtered['views_2023'] == 0) & (df_filtered['views_2025'] > 0)].nlargest(10, 'views_2025')
    if len(new_keywords) > 0:
        new_display = new_keywords[['title', 'Category', 'views_2025']].copy()
        new_display.columns = ['키워드', '카테고리', '2025 조회수']
        st.dataframe(new_display, use_container_width=True, hide_index=True)
    else:
        st.info("신규 등장 키워드가 없습니다.")
    
    # 사라진 키워드 (2023에는 있었지만 2025에 사라짐)
    st.subheader("📉 사라진 키워드 (2023년 존재 → 2025년 0건)")
    disappeared = df_filtered[(df_filtered['views_2023'] > 0) & (df_filtered['views_2025'] == 0)].nlargest(10, 'views_2023')
    if len(disappeared) > 0:
        dis_display = disappeared[['title', 'Category', 'views_2023']].copy()
        dis_display.columns = ['키워드', '카테고리', '2023 조회수']
        st.dataframe(dis_display, use_container_width=True, hide_index=True)
    else:
        st.info("사라진 키워드가 없습니다.")

with tab4:
    st.header("🔍 키워드 검색 및 조회수 변화 분석")
    if exclude_chatgpt:
        st.info("ℹ️ ChatGPT 관련 키워드가 제외된 분석입니다.")
    
    # 검색 옵션
    col_search1, col_search2 = st.columns([3, 1])
    with col_search1:
        search_query = st.text_input("🔎 키워드 검색", 
                                     placeholder="예: ChatGPT, AI_ethics, Layoff 등 (부분 일치 검색 가능)",
                                     help="키워드의 일부만 입력해도 검색됩니다.")
    with col_search2:
        search_mode = st.selectbox("검색 모드", ["부분 일치", "정확히 일치"], index=0)
    
    if search_query:
        search_query_lower = search_query.lower()
        
        # 검색 모드에 따라 필터링
        if search_mode == "정확히 일치":
            search_results = df_filtered[df_filtered['title'].str.lower() == search_query_lower]
        else:
            search_results = df_filtered[df_filtered['title'].str.lower().str.contains(search_query_lower, na=False)]
        
        if len(search_results) > 0:
            st.success(f"✅ {len(search_results)}개의 키워드를 찾았습니다.")
            
            # 검색 결과 요약
            col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
            
            total_views_23_search = search_results['views_2023'].sum()
            total_views_25_search = search_results['views_2025'].sum()
            total_change_search = total_views_25_search - total_views_23_search
            total_change_pct_search = ((total_views_25_search - total_views_23_search) / total_views_23_search * 100) if total_views_23_search > 0 else 0
            
            with col_sum1:
                st.metric("2023년 총 조회수", f"{total_views_23_search:,.0f}")
            with col_sum2:
                st.metric("2025년 총 조회수", f"{total_views_25_search:,.0f}", 
                         delta=f"{total_change_pct_search:+.1f}%")
            with col_sum3:
                st.metric("변화량", f"{total_change_search:+,.0f}")
            with col_sum4:
                # 평균 변화율 계산 시 무한대 값 제외
                valid_changes = search_results['change_pct'].replace([float('inf'), float('-inf')], pd.NA)
                avg_change_pct = valid_changes.mean()
                if pd.isna(avg_change_pct):
                    st.metric("평균 변화율", "N/A")
                else:
                    # 너무 큰 값은 제한하여 표시
                    display_avg = min(avg_change_pct, 1000) if avg_change_pct > 1000 else avg_change_pct
                    st.metric("평균 변화율", f"{display_avg:+.1f}%")
            
            # 시각화
            st.subheader("📊 조회수 변화 시각화")
            
            # 표시할 키워드 수 결정
            max_display = min(15, len(search_results))
            search_viz = search_results.sort_values('views_2025', ascending=False).head(max_display)
            
            if len(search_results) > max_display:
                st.info(f"💡 검색 결과가 {len(search_results)}개로 많아 상위 {max_display}개만 시각화합니다.")
            
            # 키워드명이 너무 길면 축약
            search_viz_display = search_viz.copy()
            search_viz_display['title_short'] = search_viz_display['title'].apply(
                lambda x: x[:30] + '...' if len(x) > 30 else x
            )
            
            # 1. 조회수 비교 차트 (가로 막대 그래프로 변경)
            st.markdown("#### 📈 키워드별 조회수 비교 (2023 vs 2025)")
            search_long = pd.melt(search_viz, id_vars=['title', 'Category'],
                                 value_vars=['views_2023', 'views_2025'],
                                 var_name='Year', value_name='Views')
            search_long['Year'] = search_long['Year'].map({'views_2023': '2023', 'views_2025': '2025'})
            
            # 가로 막대 그래프로 변경 (키워드명이 더 잘 보임)
            fig_search = px.bar(search_long, y='title', x='Views', color='Year', barmode='group',
                               orientation='h',
                               labels={'title': '키워드', 'Views': '조회수'},
                               color_discrete_map={'2023': '#3498db', '2025': '#e67e22'},
                               text='Views')
            fig_search.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_search.update_layout(
                height=max(400, len(search_viz) * 40),
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title="조회수",
                yaxis_title="",
                showlegend=True,
                margin=dict(l=200, r=50, t=20, b=50)
            )
            st.plotly_chart(fig_search, use_container_width=True)
            
            # 2. 변화율 차트 (변화율이 너무 큰 경우 처리)
            st.markdown("#### 📊 키워드별 변화율")
            
            # 변화율이 너무 큰 경우 제한 (표시용)
            search_change = search_viz.copy()
            search_change['change_pct_display'] = search_change['change_pct'].apply(
                lambda x: min(x, 1000) if x > 1000 else (max(x, -100) if x < -100 else x)
            )
            search_change['change_label'] = search_change.apply(
                lambda row: f"{row['change_pct']:.1f}%" if abs(row['change_pct']) <= 1000 
                else ("신규" if row['change_pct'] > 1000 else "사라짐"),
                axis=1
            )
            
            # 가로 막대 그래프
            fig_change = px.bar(search_change, y='title', x='change_pct_display',
                               color='change_pct',
                               orientation='h',
                               labels={'title': '키워드', 'change_pct_display': '변화율 (%)'},
                               color_continuous_scale='RdYlGn',
                               text='change_label')
            fig_change.update_traces(textposition='outside')
            fig_change.update_layout(
                height=max(400, len(search_viz) * 40),
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title="변화율 (%)",
                yaxis_title="",
                xaxis_range=[-100, 1000],
                showlegend=False,
                margin=dict(l=200, r=50, t=20, b=50)
            )
            fig_change.add_vline(x=0, line_dash="dash", line_color="gray", line_width=1)
            st.plotly_chart(fig_change, use_container_width=True)
            
            # 변화율이 1000%를 넘는 키워드에 대한 안내
            extreme_changes = search_change[abs(search_change['change_pct']) > 1000]
            if len(extreme_changes) > 0:
                st.caption(f"💡 변화율이 ±1000%를 넘는 키워드는 '신규' 또는 '사라짐'으로 표시됩니다. (총 {len(extreme_changes)}개)")
            
            # 상세 데이터 테이블
            st.subheader("📋 검색 결과 상세 데이터")
            
            # 정렬 옵션
            sort_option = st.selectbox("정렬 기준", 
                                      ['2025 조회수 (내림차순)', '2023 조회수 (내림차순)', 
                                       '변화율 (내림차순)', '변화율 (오름차순)', '키워드명 (가나다순)'],
                                      key="search_sort")
            
            search_display = search_results.copy()
            if sort_option == '2025 조회수 (내림차순)':
                search_display = search_display.sort_values('views_2025', ascending=False)
            elif sort_option == '2023 조회수 (내림차순)':
                search_display = search_display.sort_values('views_2023', ascending=False)
            elif sort_option == '변화율 (내림차순)':
                search_display = search_display.sort_values('change_pct', ascending=False)
            elif sort_option == '변화율 (오름차순)':
                search_display = search_display.sort_values('change_pct', ascending=True)
            else:
                search_display = search_display.sort_values('title', ascending=True)
            
            display_cols = ['title', 'Category', 'views_2023', 'views_2025', 'change', 'change_pct']
            search_table = search_display[display_cols].copy()
            search_table.columns = ['키워드', '카테고리', '2023 조회수', '2025 조회수', '변화량', '변화율(%)']
            search_table = search_table.round(1)
            
            st.dataframe(search_table, use_container_width=True, hide_index=True)
            
            # CSV 다운로드
            csv_search = search_results.to_csv(index=False).encode('utf-8')
            st.download_button("📥 검색 결과 CSV 다운로드", 
                             data=csv_search, 
                             file_name=f"keyword_search_{search_query.replace(' ', '_')}.csv", 
                             mime="text/csv")
        else:
            st.warning(f"❌ '{search_query}'와 일치하는 키워드를 찾을 수 없습니다.")
            st.info("💡 팁: 부분 일치 모드에서는 키워드의 일부만 입력해도 검색됩니다. 예: 'AI'를 입력하면 'AI_ethics', 'AI_art' 등이 검색됩니다.")
    else:
        st.info("👆 위 검색창에 키워드를 입력하세요. 예: 'ChatGPT', 'AI_ethics', 'Layoff' 등")
        
        # 인기 검색어 추천
        st.subheader("💡 인기 키워드 추천")
        popular_keywords = df_filtered.nlargest(10, 'views_2025')[['title', 'Category', 'views_2025']].copy()
        popular_keywords.columns = ['키워드', '카테고리', '2025 조회수']
        st.dataframe(popular_keywords, use_container_width=True, hide_index=True)

with tab5:
    st.header("🔍 원본 데이터 탐색")
    if exclude_chatgpt:
        st.info("ℹ️ ChatGPT 관련 키워드가 제외된 분석입니다.")
    
    # 필터 옵션
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        selected_category = st.multiselect("카테고리 필터", 
                                          options=['All'] + list(df_filtered['Category'].unique()),
                                          default=['All'])
    with col_filter2:
        min_views = st.number_input("최소 조회수 (2025)", min_value=0, value=0)
    
    # 필터링 (이미 ChatGPT 필터링된 df_filtered 사용)
    df_display_filtered = df_filtered.copy()
    if 'All' not in selected_category:
        df_display_filtered = df_display_filtered[df_display_filtered['Category'].isin(selected_category)]
    df_display_filtered = df_display_filtered[df_display_filtered['views_2025'] >= min_views]
    
    # 정렬 옵션
    sort_by = st.selectbox("정렬 기준", 
                          ['2025 조회수 (내림차순)', '2023 조회수 (내림차순)', 
                           '변화율 (내림차순)', '변화율 (오름차순)'])
    
    if sort_by == '2025 조회수 (내림차순)':
        df_display = df_display_filtered.sort_values(by='views_2025', ascending=False)
    elif sort_by == '2023 조회수 (내림차순)':
        df_display = df_display_filtered.sort_values(by='views_2023', ascending=False)
    elif sort_by == '변화율 (내림차순)':
        df_display = df_display_filtered.sort_values(by='change_pct', ascending=False)
    else:
        df_display = df_display_filtered.sort_values(by='change_pct', ascending=True)
    
    # 표시용 컬럼 선택
    display_cols = ['title', 'Category', 'views_2023', 'views_2025', 'change', 'change_pct']
    df_display = df_display[display_cols].copy()
    df_display.columns = ['키워드', '카테고리', '2023 조회수', '2025 조회수', '변화량', '변화율(%)']
    df_display = df_display.round(1)
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    st.caption(f"총 {len(df_display)}개 키워드 표시 중")
    
    csv = df_display_filtered.to_csv(index=False).encode('utf-8')
    st.download_button("📥 필터링된 데이터 CSV 다운로드", 
                      data=csv, file_name="ai_trend_analysis_filtered.csv", mime="text/csv")

