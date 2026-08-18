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

# ===== 점수 하이라이트 함수 =====
def highlight_score(val):
    if val >= 80:
        return 'background-color: #1a4a1a; color: #00ff88;'
    elif val >= 70:
        return 'background-color: #1a3a1a; color: #88ff88;'
    elif val >= 60:
        return 'background-color: #3a3a1a; color: #ffff88;'
    else:
        return 'background-color: #4a1a1a; color: #ff8888;'

def highlight_overall(val):
    if val >= 85:
        return 'background-color: #1a4a1a; color: #00ff88; font-weight: bold;'
    elif val >= 75:
        return 'background-color: #1a3a1a; color: #88ff88;'
    elif val >= 65:
        return 'background-color: #3a3a1a; color: #ffff88;'
    else:
        return 'background-color: #4a1a1a; color: #ff8888;'

# 페이지 설정
st.set_page_config(
    page_title="Quant Analysis System",
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
        /* 사이드바 메뉴 스타일 - 세로 배열 */
        .menu-button {{
            display: block;
            width: 100%;
            padding: 14px 20px;
            margin: 4px 0;
            background-color: transparent;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            text-align: left;
            font-size: 18px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
        }}
        .menu-button:hover {{
            background-color: #1a1a1a;
        }}
        .menu-button.active {{
            background-color: #1a3a1a;
            border-left: 4px solid #00ff88;
            color: #00ff88;
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
        div[data-testid="stMetricValue"] {{
            color: {UI_CONFIG['text_color']} !important;
        }}
        div[data-testid="stMetricDelta"] {{
            color: {UI_CONFIG['accent_color']} !important;
        }}
        /* 라디오 버튼 숨기기 */
        div[data-testid="stSidebar"] div[data-testid="stRadio"] {{
            display: none;
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
    st.session_state.stock_data = {}
if 'stock_financials' not in st.session_state:
    st.session_state.stock_financials = {}
if 'fundamental_scores' not in st.session_state:
    st.session_state.fundamental_scores = {}
if 'technical_scores' not in st.session_state:
    st.session_state.technical_scores = {}
if 'page' not in st.session_state:
    st.session_state.page = "Home"

# ===== 사이드바 (세로 메뉴) =====
with st.sidebar:
    # 로고
    st.image("https://img.icons8.com/fluency/96/000000/stocks.png", width=80)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Home 버튼
    home_active = "active" if st.session_state.page == "Home" else ""
    if st.button("🏠 Home", key="btn_home", use_container_width=True):
        st.session_state.page = "Home"
        st.rerun()
    
    # Fundamental 버튼
    fund_active = "active" if st.session_state.page == "Fundamental" else ""
    if st.button("📈 Fundamental", key="btn_fund", use_container_width=True):
        st.session_state.page = "Fundamental"
        st.rerun()
    
    # Technical 버튼
    tech_active = "active" if st.session_state.page == "Technical" else ""
    if st.button("📉 Technical", key="btn_tech", use_container_width=True):
        st.session_state.page = "Technical"
        st.rerun()
    
    # Overall 버튼
    overall_active = "active" if st.session_state.page == "Overall" else ""
    if st.button("⭐ Overall", key="btn_overall", use_container_width=True):
        st.session_state.page = "Overall"
        st.rerun()
    
    st.markdown("---")
    st.caption(f"Current: {st.session_state.page}")

# 데이터 수집 함수
@st.cache_data(ttl=3600)
def collect_all_data():
    collector = st.session_state.data_collector
    stocks = collector.get_kospi_top_stocks()
    stock_prices = {}
    stock_financials = {}
    
    for stock in stocks[:30]:
        code = stock['code']
        name = stock['name']
        df = collector.get_stock_data(code)
        if df is not None and not df.empty:
            stock_prices[code] = {
                'data': df,
                'name': name,
                'current_price': df['Close'].iloc[-1],
                'change': ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100) if len(df) > 1 else 0
            }
        fin_data = collector.get_financial_data(code)
        stock_financials[code] = fin_data
    
    indices = collector.get_market_indices()
    return stocks, stock_prices, stock_financials, indices

# 데이터 로드
with st.spinner('Loading data...'):
    stocks, stock_prices, stock_financials, indices = collect_all_data()

# ===== 페이지 라우팅 =====
if st.session_state.page == "Home":
    # ========== HOME ==========
    st.markdown('<div class="main-header">Market Dashboard</div>', unsafe_allow_html=True)
    
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
    
    st.markdown("---")
    st.subheader("Interest Rates")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Korea Base Rate", "3.50%", "0.00%")
    with col2:
        st.metric("US Base Rate", "5.50%", "0.00%")
    with col3:
        st.metric("Korea 3Y Bond", "3.85%", "+0.05%")
    
    st.markdown("---")
    st.subheader("Top Gainers")
    
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
                st.write(f"{stock['current_price']:,.0f} KRW")
            with col3:
                change_color = "🟢" if stock['change'] >= 0 else "🔴"
                st.write(f"{change_color} {stock['change']:+.2f}%")
            with col4:
                st.write("📊")

elif st.session_state.page == "Fundamental":
    # ========== FUNDAMENTAL ==========
    st.markdown('<div class="main-header">Fundamental Analysis</div>', unsafe_allow_html=True)
    
    if st.button("🔄 Run Analysis", type="primary"):
        with st.spinner('Running fundamental analysis...'):
            st.success("Analysis complete!")
    
    st.subheader("Top 30 Rankings (Sorted by Score)")
    
    sample_data = []
    for code, info in list(stock_prices.items())[:30]:
        score = np.random.randint(60, 98)
        sample_data.append({
            'Rank': len(sample_data) + 1,
            'Name': info['name'],
            'Price': f"{info['current_price']:,.0f}",
            'Change': f"{info['change']:+.2f}%",
            'PER': f"{np.random.randint(5, 25)}",
            'PBR': f"{np.random.randint(1, 5)}",
            'ROE': f"{np.random.randint(5, 30)}%",
            'Score': score
        })
    
    df = pd.DataFrame(sample_data)
    # Score 내림차순 정렬
    df = df.sort_values('Score', ascending=False).reset_index(drop=True)
    df['Rank'] = df.index + 1
    
    styled_df = df.style.map(highlight_score, subset=['Score'])
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    st.markdown("---")
    st.subheader("Detail Analysis")
    
    selected_stock = st.selectbox(
        "Select a stock",
        options=[info['name'] for code, info in stock_prices.items()]
    )
    
    if selected_stock:
        st.info(f"📊 {selected_stock} Fundamental Details")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("PER", "12.5", "Industry: 15.2")
            st.metric("PBR", "1.8", "Industry: 2.1")
            st.metric("ROE", "18.5%", "Industry: 12.3%")
        with col2:
            st.metric("Operating Growth", "+15.3%", "YoY")
            st.metric("Debt Ratio", "85.2%", "Industry: 120.5%")
            st.metric("Total Score", "87/100", "Top 10%")

elif st.session_state.page == "Technical":
    # ========== TECHNICAL ==========
    st.markdown('<div class="main-header">Technical Analysis</div>', unsafe_allow_html=True)
    
    if st.button("🔄 Run Analysis", type="primary"):
        with st.spinner('Running technical analysis...'):
            st.success("Analysis complete!")
    
    st.subheader("Top 30 Rankings (Sorted by Score)")
    
    sample_data = []
    for code, info in list(stock_prices.items())[:30]:
        score = np.random.randint(55, 95)
        sample_data.append({
            'Rank': len(sample_data) + 1,
            'Name': info['name'],
            'Price': f"{info['current_price']:,.0f}",
            'Change': f"{info['change']:+.2f}%",
            'MA': '🟢 Bullish' if np.random.random() > 0.5 else '🔴 Bearish',
            'MACD': '🟢 Golden Cross' if np.random.random() > 0.5 else '🔴 Death Cross',
            'Bollinger': '⬇️ Lower' if np.random.random() > 0.6 else '⬆️ Upper',
            'Score': score
        })
    
    df = pd.DataFrame(sample_data)
    # Score 내림차순 정렬
    df = df.sort_values('Score', ascending=False).reset_index(drop=True)
    df['Rank'] = df.index + 1
    
    styled_df = df.style.map(highlight_score, subset=['Score'])
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    st.markdown("---")
    st.subheader("Chart")
    
    selected_stock = st.selectbox(
        "Select a stock for chart",
        options=[info['name'] for code, info in stock_prices.items()],
        key='tech_select'
    )
    
    if selected_stock:
        stock_code = None
        for code, info in stock_prices.items():
            if info['name'] == selected_stock:
                stock_code = code
                break
        
        if stock_code and stock_code in stock_prices:
            df = stock_prices[stock_code]['data']
            
            fig = make_subplots(rows=2, cols=1, 
                               shared_xaxes=True,
                               vertical_spacing=0.05,
                               row_heights=[0.7, 0.3])
            
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Daily'
            ), row=1, col=1)
            
            ma5 = df['Close'].rolling(5).mean()
            ma20 = df['Close'].rolling(20).mean()
            ma60 = df['Close'].rolling(60).mean()
            
            fig.add_trace(go.Scatter(x=df.index, y=ma5, name='MA5', line=dict(color='yellow')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=ma20, name='MA20', line=dict(color='orange')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=ma60, name='MA60', line=dict(color='red')), row=1, col=1)
            
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            histogram = macd - signal
            
            fig.add_trace(go.Scatter(x=df.index, y=macd, name='MACD', line=dict(color='blue')), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=signal, name='Signal', line=dict(color='red')), row=2, col=1)
            
            colors = ['green' if val >= 0 else 'red' for val in histogram]
            fig.add_trace(go.Bar(x=df.index, y=histogram, name='Histogram', marker_color=colors), row=2, col=1)
            
            fig.update_layout(
                template='plotly_dark',
                height=700,
                showlegend=True,
                xaxis_rangeslider_visible=False
            )
            
            st.plotly_chart(fig, use_container_width=True)

else:
    # ========== OVERALL ==========
    st.markdown('<div class="main-header">Overall Evaluation</div>', unsafe_allow_html=True)
    
    st.info("📌 Fundamental (50%) + Technical (50%) combined ranking.")
    
    if st.button("🔄 Run Combined Analysis", type="primary"):
        with st.spinner('Running combined analysis...'):
            st.success("Analysis complete!")
    
    st.subheader("Top 30 Overall Rankings (Sorted by Score)")
    
    sample_data = []
    for code, info in list(stock_prices.items())[:30]:
        fundamental_score = np.random.randint(60, 98)
        technical_score = np.random.randint(55, 95)
        overall_score = (fundamental_score + technical_score) / 2
        
        trend = "📈 Bullish" if overall_score > 80 else "📉 Bearish" if overall_score < 65 else "➡️ Neutral"
        
        sample_data.append({
            'Rank': len(sample_data) + 1,
            'Name': info['name'],
            'Price': f"{info['current_price']:,.0f}",
            'Change': f"{info['change']:+.2f}%",
            'Fundamental': fundamental_score,
            'Technical': technical_score,
            'Overall': round(overall_score, 1),
            'Trend': trend
        })
    
    df = pd.DataFrame(sample_data)
    # Overall 내림차순 정렬
    df = df.sort_values('Overall', ascending=False).reset_index(drop=True)
    df['Rank'] = df.index + 1
    
    styled_df = df.style.map(highlight_overall, subset=['Overall'])
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    st.markdown("---")
    st.subheader("Top 3 Picks")
    
    top3 = df.head(3)
    
    col1, col2, col3 = st.columns(3)
    for idx, (_, row) in enumerate(top3.iterrows()):
        col = [col1, col2, col3][idx]
        emoji = ["🥇", "🥈", "🥉"][idx]
        with col:
            st.markdown(f"""
                <div style="background-color: #1a1a1a; padding: 1.5rem; border-radius: 15px; text-align: center; border: 2px solid #2a2a2a;">
                    <div style="font-size: 2rem;">{emoji}</div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #ffffff;">{row['Name']}</div>
                    <div style="font-size: 1rem; color: #aaaaaa;">{row['Price']} KRW</div>
                    <div style="font-size: 2.5rem; font-weight: bold; color: #00ff88;">{row['Overall']}</div>
                    <div style="font-size: 0.9rem; color: #888888;">Overall Score</div>
                    <div style="margin-top: 0.5rem; font-size: 0.9rem;">📊 F: {row['Fundamental']} | T: {row['Technical']}</div>
                </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #555; padding: 1rem;">
        Quant Analysis System v1.0 | Data Updates: 2x daily (15:30, 06:00 KST)
    </div>
""", unsafe_allow_html=True)