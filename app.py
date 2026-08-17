# app.py - 메인 Streamlit 앱
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 설정 및 모듈 import
from config import UI_CONFIG
from data.collector import DataCollector
from analysis.fundamental import FundamentalAnalyzer
from analysis.technical import TechnicalAnalyzer

def highlight_score(val):
    """
    점수에 따라 배경색을 다르게 표시하는 함수
    """
    if val >= 80:
        return 'background-color: #1a4a1a; color: #00ff88;'  # 높은 점수 - 초록
    elif val >= 70:
        return 'background-color: #1a3a1a; color: #88ff88;'  # 중간 점수 - 연두
    elif val >= 60:
        return 'background-color: #3a3a1a; color: #ffff88;'  # 보통 점수 - 노랑
    else:
        return 'background-color: #4a1a1a; color: #ff8888;'  # 낮은 점수 - 빨강
    
# 페이지 설정
st.set_page_config(
    page_title="퀀트 분석 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 (올블랙)
st.markdown(f"""
    <style>
        .stApp {{
            background-color: {UI_CONFIG['background_color']};
            color: {UI_CONFIG['text_color']};
        }}
        .stSidebar {{
            background-color: #0a0a0a;
        }}
        .main-header {{
            color: {UI_CONFIG['text_color']};
            font-size: 2.5rem;
            font-weight: bold;
            padding: 1rem 0;
            border-bottom: 2px solid {UI_CONFIG['accent_color']};
        }}
        .metric-card {{
            background-color: #1a1a1a;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid {UI_CONFIG['accent_color']};
            margin: 0.5rem 0;
        }}
        .metric-value {{
            font-size: 1.8rem;
            font-weight: bold;
            color: {UI_CONFIG['text_color']};
        }}
        .metric-change-positive {{
            color: {UI_CONFIG['accent_color']};
        }}
        .metric-change-negative {{
            color: {UI_CONFIG['danger_color']};
        }}
        .stock-card {{
            background-color: #0d0d0d;
            padding: 0.8rem;
            border-radius: 8px;
            margin: 0.3rem 0;
            border: 1px solid #2a2a2a;
        }}
        .rank-1 {{
            background-color: #1a2a1a;
            border-left: 4px solid gold;
        }}
        .rank-2 {{
            background-color: #1a1a2a;
            border-left: 4px solid silver;
        }}
        .rank-3 {{
            background-color: #2a1a1a;
            border-left: 4px solid #cd7f32;
        }}
        div[data-testid="stMetricValue"] {{
            color: {UI_CONFIG['text_color']} !important;
        }}
        div[data-testid="stMetricDelta"] {{
            color: {UI_CONFIG['accent_color']} !important;
        }}
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'data_collector' not in st.session_state:
    st.session_state.data_collector = DataCollector()
if 'fundamental_analyzer' not in st.session_state:
    st.session_state.fundamental_analyzer = FundamentalAnalyzer()
if 'technical_analyzer' not in st.session_state:
    st.session_state.technical_analyzer = TechnicalAnalyzer()
if 'stock_data' not in st.session_state:
    st.session_state.stock
    # app.py - 이어서 (위에서 작성한 코드 다음에 붙여넣기)

# ========== 여기서부터 app.py 이어서 작성 ==========

# 사이드바 - 네비게이션
st.sidebar.image("https://img.icons8.com/fluency/96/000000/stocks.png", width=80)
st.sidebar.title("📊 퀀트 분석")

page = st.sidebar.radio(
    "메뉴",
    ["🏠 홈", "📈 기본적 분석", "📉 기술적 분석", "⭐ 종합 평가"]
)

# 데이터 수집 함수
@st.cache_data(ttl=3600)  # 1시간 캐시
def collect_all_data():
    collector = st.session_state.data_collector
    
    # 1. 종목 리스트 가져오기
    stocks = collector.get_kospi_top_stocks()
    
    # 2. 각 종목의 주가 데이터 수집
    stock_prices = {}
    stock_financials = {}
    
    for stock in stocks[:30]:  # 테스트용 30개만 (실제로는 150개)
        code = stock['code']
        name = stock['name']
        
        # 주가 데이터
        df = collector.get_stock_data(code)
        if df is not None and not df.empty:
            stock_prices[code] = {
                'data': df,
                'name': name,
                'current_price': df['Close'].iloc[-1],
                'change': ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100) if len(df) > 1 else 0
            }
        
        # 재무 데이터
        fin_data = collector.get_financial_data(code)
        stock_financials[code] = fin_data
    
    # 3. 시장 지수 데이터
    indices = collector.get_market_indices()
    
    return stocks, stock_prices, stock_financials, indices

# 데이터 로드 (with loading indicator)
with st.spinner('데이터를 수집중입니다...'):
    stocks, stock_prices, stock_financials, indices = collect_all_data()

# ========== 홈 페이지 ==========
if page == "🏠 홈":
    st.markdown('<div class="main-header">📊 시장 현황</div>', unsafe_allow_html=True)
    
    # 주요 지표 표시 (4개씩 행)
    col1, col2, col3, col4 = st.columns(4)
    
    index_list = ['KOSPI', 'KOSDAQ', 'NASDAQ', 'Gold', 'WTI', 'USD/KRW', 'US 10Y']
    cols = [col1, col2, col3, col4]
    
    for i, name in enumerate(index_list[:8]):
        if name in indices:
            data = indices[name]
            col_idx = i % 4
            with cols[col_idx]:
                if data['price']:
                    change_class = "metric-change-positive" if data['change'] >= 0 else "metric-change-negative"
                    st.markdown(f"""
                        <div class="metric-card">
                            <div style="font-size:0.9rem; color:#888;">{name}</div>
                            <div class="metric-value">{data['price']:,.2f}</div>
                            <div class="{change_class}">{data['change']:+.2f}%</div>
                        </div>
                    """, unsafe_allow_html=True)
    
    # 두 번째 행 - 기준금리
    st.markdown("---")
    st.subheader("📋 기준금리")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("한국 기준금리", "3.50%", "0.00%")
    with col2:
        st.metric("미국 기준금리", "5.50%", "0.00%")
    with col3:
        st.metric("한국 국채 3년", "3.85%", "+0.05%")
    
    # 종목 랭킹 미리보기 (상위 5개)
    st.markdown("---")
    st.subheader("🔥 급상승 종목 Top 5")
    
    # 간단한 등락률 기준 정렬
    sorted_stocks = sorted(
        [{'code': code, **info} for code, info in stock_prices.items()],
        key=lambda x: x['change'],
        reverse=True
    )[:5]
    
    for rank, stock in enumerate(sorted_stocks, 1):
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                st.write(f"#{rank} {stock['name']}")
            with col2:
                st.write(f"{stock['current_price']:,.0f}원")
            with col3:
                change_color = "🟢" if stock['change'] >= 0 else "🔴"
                st.write(f"{change_color} {stock['change']:+.2f}%")
            with col4:
                st.write("📊")

# ========== 기본적 분석 ==========
elif page == "📈 기본적 분석":
    st.markdown('<div class="main-header">📈 기본적 분석</div>', unsafe_allow_html=True)
    
    # 분석 실행 버튼
    if st.button("🔄 분석 실행", type="primary"):
        with st.spinner('기본적 분석을 수행중입니다...'):
            # 여기서 실제 분석 수행
            st.success("분석이 완료되었습니다!")
    
    # 분석 결과 표시 (데모 데이터)
    st.subheader("🏆 기본적 분석 순위 (상위 30개)")
    
    # 샘플 데이터 생성 (실제로는 분석 결과 사용)
    sample_data = []
    for code, info in list(stock_prices.items())[:30]:
        # 랜덤 점수 생성 (실제로는 계산된 점수)
        score = np.random.randint(60, 98)
        sample_data.append({
            '순위': len(sample_data) + 1,
            '종목명': info['name'],
            '현재가': f"{info['current_price']:,.0f}",
            '등락률': f"{info['change']:+.2f}%",
            'PER': f"{np.random.randint(5, 25)}",
            'PBR': f"{np.random.randint(1, 5)}",
            'ROE': f"{np.random.randint(5, 30)}%",
            '종합점수': score
        })
    
    df = pd.DataFrame(sample_data)
    
    # 스타일 적용
    def highlight_score(val):
        if val >= 80:
            return 'background-color: #1a4a1a; color: #00ff88;'
        elif val >= 70:
            return 'background-color: #1a3a1a; color: #88ff88;'
        elif val >= 60:
            return 'background-color: #3a3a1a; color: #ffff88;'
        else:
            return 'background-color: #4a1a1a; color: #ff8888;'
    
    styled_df = df.style.applymap(highlight_score, subset=['종합점수'])
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    # 상세 분석 (선택한 종목)
    st.markdown("---")
    st.subheader("🔍 종목 상세 분석")
    
    selected_stock = st.selectbox(
        "분석할 종목을 선택하세요",
        options=[info['name'] for code, info in stock_prices.items()]
    )
    
    if selected_stock:
        st.info(f"📊 {selected_stock}의 기본적 분석 상세")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("PER", "12.5", "업종평균: 15.2")
            st.metric("PBR", "1.8", "업종평균: 2.1")
            st.metric("ROE", "18.5%", "업종평균: 12.3%")
        with col2:
            st.metric("영업이익증가율", "+15.3%", "전년대비")
            st.metric("부채비율", "85.2%", "업종평균: 120.5%")
            st.metric("종합 점수", "87/100", "상위 10%")

# ========== 기술적 분석 ==========
elif page == "📉 기술적 분석":
    st.markdown('<div class="main-header">📉 기술적 분석</div>', unsafe_allow_html=True)
    
    if st.button("🔄 분석 실행", type="primary"):
        with st.spinner('기술적 분석을 수행중입니다...'):
            st.success("분석이 완료되었습니다!")
    
    st.subheader("🏆 기술적 분석 순위 (상위 30개)")
    
    # 샘플 데이터
    sample_data = []
    for code, info in list(stock_prices.items())[:30]:
        score = np.random.randint(55, 95)
        sample_data.append({
            '순위': len(sample_data) + 1,
            '종목명': info['name'],
            '현재가': f"{info['current_price']:,.0f}",
            '등락률': f"{info['change']:+.2f}%",
            '이동평균': '🟢 정배열' if np.random.random() > 0.5 else '🔴 역배열',
            'MACD': '🟢 골든크로스' if np.random.random() > 0.5 else '🔴 데드크로스',
            '볼린저': '⬇️ 하단' if np.random.random() > 0.6 else '⬆️ 상단',
            '종합점수': score
        })
    
    df = pd.DataFrame(sample_data)
    styled_df = df.style.applymap(highlight_score, subset=['종합점수'])
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    # 차트 표시
    st.markdown("---")
    st.subheader("📊 기술적 지표 차트")
    
    selected_stock = st.selectbox(
        "차트를 볼 종목을 선택하세요",
        options=[info['name'] for code, info in stock_prices.items()],
        key='tech_select'
    )
    
    if selected_stock:
        # 해당 종목의 코드 찾기
        stock_code = None
        for code, info in stock_prices.items():
            if info['name'] == selected_stock:
                stock_code = code
                break
        
        if stock_code and stock_code in stock_prices:
            df = stock_prices[stock_code]['data']
            
            # 캔들스틱 + 이동평균선 차트
            fig = make_subplots(rows=2, cols=1, 
                               shared_xaxes=True,
                               vertical_spacing=0.05,
                               row_heights=[0.7, 0.3])
            
            # 캔들스틱
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='일봉'
            ), row=1, col=1)
            
            # 이동평균선
            ma5 = df['Close'].rolling(5).mean()
            ma20 = df['Close'].rolling(20).mean()
            ma60 = df['Close'].rolling(60).mean()
            
            fig.add_trace(go.Scatter(x=df.index, y=ma5, name='MA5', line=dict(color='yellow')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=ma20, name='MA20', line=dict(color='orange')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=ma60, name='MA60', line=dict(color='red')), row=1, col=1)
            
            # MACD
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            histogram = macd - signal
            
            fig.add_trace(go.Scatter(x=df.index, y=macd, name='MACD', line=dict(color='blue')), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=signal, name='Signal', line=dict(color='red')), row=2, col=1)
            
            # 히스토그램
            colors = ['green' if val >= 0 else 'red' for val in histogram]
            fig.add_trace(go.Bar(x=df.index, y=histogram, name='Histogram', marker_color=colors), row=2, col=1)
            
            fig.update_layout(
                template='plotly_dark',
                height=700,
                showlegend=True,
                xaxis_rangeslider_visible=False
            )
            
            st.plotly_chart(fig, use_container_width=True)

# ========== 종합 평가 ==========
else:
    st.markdown('<div class="main-header">⭐ 종합 평가</div>', unsafe_allow_html=True)
    
    st.info("📌 기본적 분석(50%) + 기술적 분석(50%)을 종합한 최종 순위입니다.")
    
    if st.button("🔄 종합 분석 실행", type="primary"):
        with st.spinner('종합 분석을 수행중입니다...'):
            st.success("분석이 완료되었습니다!")
    
    st.subheader("🏆 종합 평가 순위 (상위 30개)")
    
    # 샘플 데이터 (기본+기술 평균)
    sample_data = []
    for code, info in list(stock_prices.items())[:30]:
        fundamental_score = np.random.randint(60, 98)
        technical_score = np.random.randint(55, 95)
        overall_score = (fundamental_score + technical_score) / 2
        
        # 추세 표시
        trend = "📈 상승" if overall_score > 80 else "📉 하락" if overall_score < 65 else "➡️ 횡보"
        
        sample_data.append({
            '순위': len(sample_data) + 1,
            '종목명': info['name'],
            '현재가': f"{info['current_price']:,.0f}",
            '등락률': f"{info['change']:+.2f}%",
            '기본점수': fundamental_score,
            '기술점수': technical_score,
            '종합점수': round(overall_score, 1),
            '추세': trend
        })
    
    df = pd.DataFrame(sample_data)
    
    # 종합점수 기준 정렬
    df = df.sort_values('종합점수', ascending=False).reset_index(drop=True)
    df['순위'] = df.index + 1
    
    # 스타일 적용
    def highlight_overall(val):
        if val >= 85:
            return 'background-color: #1a4a1a; color: #00ff88; font-weight: bold;'
        elif val >= 75:
            return 'background-color: #1a3a1a; color: #88ff88;'
        elif val >= 65:
            return 'background-color: #3a3a1a; color: #ffff88;'
        else:
            return 'background-color: #4a1a1a; color: #ff8888;'
    
    styled_df = df.style.applymap(highlight_overall, subset=['종합점수'])
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    # 상위 3개 하이라이트
    st.markdown("---")
    st.subheader("🥇🥈🥉 TOP 3 종목")
    
    top3 = df.head(3)
    
    col1, col2, col3 = st.columns(3)
    for idx, (_, row) in enumerate(top3.iterrows()):
        col = [col1, col2, col3][idx]
        emoji = ["🥇", "🥈", "🥉"][idx]
        with col:
            st.markdown(f"""
                <div style="background-color: #1a1a1a; padding: 1.5rem; border-radius: 15px; text-align: center; border: 2px solid #2a2a2a;">
                    <div style="font-size: 2rem;">{emoji}</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #ffffff;">{row['종목명']}</div>
                    <div style="font-size: 1rem; color: #aaaaaa;">{row['현재가']}원</div>
                    <div style="font-size: 2.5rem; font-weight: bold; color: #00ff88;">{row['종합점수']}</div>
                    <div style="font-size: 0.9rem; color: #888888;">종합 점수</div>
                    <div style="margin-top: 0.5rem; font-size: 0.9rem;">📊 기본: {row['기본점수']} | 기술: {row['기술점수']}</div>
                </div>
            """, unsafe_allow_html=True)

# 푸터
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #555; padding: 1rem;">
        📊 퀀트 분석 시스템 v1.0 | 데이터 업데이트: 하루 2회 (15:30, 06:00 KST)
    </div>
""", unsafe_allow_html=True)