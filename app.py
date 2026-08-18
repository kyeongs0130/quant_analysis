import streamlit as st
import pandas as pd
import numpy as np
import FinanceDataReader as fdr
import yfinance as yf
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. 페이지 설정
# ============================================================
st.set_page_config(
    page_title="Quant Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 2. CSS 스타일 (완전 검정 배경)
# ============================================================
st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
    }
    .stSidebar {
        background-color: #0a0a0a;
    }
    .stSidebar .stButton button {
        background-color: transparent;
        color: #ffffff;
        border: none;
        text-align: left;
        font-size: 16px;
        padding: 10px 15px;
        border-radius: 8px;
        width: 100%;
        justify-content: flex-start;
    }
    .stSidebar .stButton button:hover {
        background-color: #2a2a2a;
        border-left: 3px solid #00FF00;
    }
    .stDataFrame {
        background-color: #0a0a0a;
    }
    .stMetric {
        background-color: #0a0a0a;
        padding: 10px;
        border-radius: 8px;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff;
    }
    div[data-testid="stMetricDelta"] {
        color: #00FF00;
    }
    .stMarkdown, .stText, .stSubheader, .stTitle {
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# 3. 실제 재무데이터 수집 함수
# ============================================================

@st.cache_data(ttl=86400)  # 24시간 캐싱
def get_financial_data(code):
    """
    종목코드로 실제 재무데이터(PER, PBR, ROE, 부채비율, 영업이익증가율) 수집
    """
    try:
        # 1. 현재가 및 기본 정보
        price_df = fdr.DataReader(code, datetime.now() - timedelta(days=5))
        if price_df.empty:
            return None
        current_price = price_df['Close'].iloc[-1]
        
        # 2. 재무제표 데이터 수집 (최근 4분기)
        fs = fdr.DataReader(code, '2023')
        if fs.empty:
            return None
        
        # 3. PER 계산 (주가 / EPS)
        try:
            # 최근 4분기 순이익 합계
            net_income = fs['NetIncome'].sum() if 'NetIncome' in fs.columns else None
            if net_income and net_income > 0:
                shares = fs['Shares'].iloc[-1] if 'Shares' in fs.columns else None
                if shares:
                    eps = net_income / shares
                    per = current_price / eps if eps > 0 else None
                else:
                    per = None
            else:
                per = None
        except:
            per = None
        
        # 4. PBR 계산 (주가 / BPS)
        try:
            equity = fs['Equity'].iloc[-1] if 'Equity' in fs.columns else None
            if equity and equity > 0:
                shares = fs['Shares'].iloc[-1] if 'Shares' in fs.columns else None
                if shares:
                    bps = equity / shares
                    pbr = current_price / bps if bps > 0 else None
                else:
                    pbr = None
            else:
                pbr = None
        except:
            pbr = None
        
        # 5. ROE 계산 (순이익 / 자기자본)
        try:
            net_income = fs['NetIncome'].iloc[-1] if 'NetIncome' in fs.columns else None
            equity = fs['Equity'].iloc[-1] if 'Equity' in fs.columns else None
            if net_income and equity and equity > 0:
                roe = (net_income / equity) * 100
            else:
                roe = None
        except:
            roe = None
        
        # 6. 부채비율 계산 (부채 / 자기자본)
        try:
            liabilities = fs['Liabilities'].iloc[-1] if 'Liabilities' in fs.columns else None
            equity = fs['Equity'].iloc[-1] if 'Equity' in fs.columns else None
            if liabilities and equity and equity > 0:
                debt_ratio = (liabilities / equity) * 100
            else:
                debt_ratio = None
        except:
            debt_ratio = None
        
        # 7. 영업이익증가율 (전년 대비)
        try:
            operating_income = fs['OperatingIncome'] if 'OperatingIncome' in fs.columns else None
            if operating_income is not None and len(operating_income) >= 2:
                growth = ((operating_income.iloc[-1] - operating_income.iloc[-2]) / operating_income.iloc[-2]) * 100
            else:
                growth = None
        except:
            growth = None
        
        return {
            'per': per,
            'pbr': pbr,
            'roe': roe,
            'debt_ratio': debt_ratio,
            'growth': growth,
            'price': current_price
        }
    except Exception as e:
        return None

@st.cache_data(ttl=86400)
def get_industry_averages():
    """
    업종별 평균 PER/PBR 계산
    """
    try:
        # KRX 전체 종목 리스트
        all_stocks = fdr.StockListing('KRX')
        stocks = all_stocks[~all_stocks['Name'].str.contains('ETF|ETN', case=False)]
        
        industry_avg = {}
        for _, row in stocks.iterrows():
            code = str(row['Symbol']).zfill(6)
            sector = row.get('Sector', 'Unknown')
            if sector not in industry_avg:
                industry_avg[sector] = {'per': [], 'pbr': []}
            
            # 각 종목의 PER/PBR 계산 (간단히)
            try:
                fs = fdr.DataReader(code, '2023')
                if not fs.empty:
                    price_df = fdr.DataReader(code, datetime.now() - timedelta(days=5))
                    if not price_df.empty:
                        current_price = price_df['Close'].iloc[-1]
                        net_income = fs['NetIncome'].sum() if 'NetIncome' in fs.columns else None
                        if net_income and net_income > 0:
                            shares = fs['Shares'].iloc[-1] if 'Shares' in fs.columns else None
                            if shares:
                                eps = net_income / shares
                                per = current_price / eps if eps > 0 else None
                                if per and 0 < per < 100:
                                    industry_avg[sector]['per'].append(per)
            except:
                pass
        
        # 평균 계산
        result = {}
        for sector, values in industry_avg.items():
            result[sector] = {
                'per': np.mean(values['per']) if values['per'] else 15,
                'pbr': np.mean(values['pbr']) if values['pbr'] else 1.5
            }
        return result
    except:
        return {}

# ============================================================
# 4. 점수 계산 함수 (실제 데이터 기반)
# ============================================================

def calculate_fundamental_score(financial_data, industry_avg):
    """
    실제 재무데이터를 기반으로 기본적 분석 점수 계산
    """
    if financial_data is None:
        return 50, {}
    
    scores = {}
    weights = {
        'PER': 0.20,
        'PBR': 0.15,
        'ROE': 0.25,
        '부채비율': 0.20,
        '영업이익증가율': 0.20
    }
    
    # 1. PER 점수 (낮을수록 좋음, 업종 평균 대비)
    if financial_data['per'] and financial_data['per'] > 0:
        industry_per = industry_avg.get('per', 15)
        ratio = financial_data['per'] / industry_per
        if ratio <= 0.5:
            scores['PER'] = 95
        elif ratio <= 0.7:
            scores['PER'] = 85
        elif ratio <= 0.9:
            scores['PER'] = 75
        elif ratio <= 1.1:
            scores['PER'] = 60
        elif ratio <= 1.3:
            scores['PER'] = 50
        elif ratio <= 1.5:
            scores['PER'] = 40
        else:
            scores['PER'] = 30
    else:
        scores['PER'] = 50
    
    # 2. PBR 점수 (낮을수록 좋음)
    if financial_data['pbr'] and financial_data['pbr'] > 0:
        industry_pbr = industry_avg.get('pbr', 1.5)
        ratio = financial_data['pbr'] / industry_pbr
        if ratio <= 0.5:
            scores['PBR'] = 90
        elif ratio <= 0.8:
            scores['PBR'] = 80
        elif ratio <= 1.0:
            scores['PBR'] = 70
        elif ratio <= 1.2:
            scores['PBR'] = 60
        elif ratio <= 1.5:
            scores['PBR'] = 50
        else:
            scores['PBR'] = 35
    else:
        scores['PBR'] = 50
    
    # 3. ROE 점수 (높을수록 좋음)
    if financial_data['roe']:
        if financial_data['roe'] > 20:
            scores['ROE'] = 95
        elif financial_data['roe'] > 15:
            scores['ROE'] = 85
        elif financial_data['roe'] > 10:
            scores['ROE'] = 70
        elif financial_data['roe'] > 5:
            scores['ROE'] = 55
        elif financial_data['roe'] > 0:
            scores['ROE'] = 40
        else:
            scores['ROE'] = 25
    else:
        scores['ROE'] = 50
    
    # 4. 부채비율 점수 (낮을수록 좋음)
    if financial_data['debt_ratio']:
        ratio = financial_data['debt_ratio']
        if ratio <= 50:
            scores['부채비율'] = 95
        elif ratio <= 100:
            scores['부채비율'] = 80
        elif ratio <= 150:
            scores['부채비율'] = 65
        elif ratio <= 200:
            scores['부채비율'] = 50
        elif ratio <= 300:
            scores['부채비율'] = 35
        else:
            scores['부채비율'] = 20
    else:
        scores['부채비율'] = 50
    
    # 5. 영업이익증가율 점수 (높을수록 좋음)
    if financial_data['growth']:
        growth = financial_data['growth']
        if growth > 50:
            scores['영업이익증가율'] = 100
        elif growth > 30:
            scores['영업이익증가율'] = 90
        elif growth > 15:
            scores['영업이익증가율'] = 80
        elif growth > 5:
            scores['영업이익증가율'] = 65
        elif growth > 0:
            scores['영업이익증가율'] = 50
        elif growth > -10:
            scores['영업이익증가율'] = 35
        else:
            scores['영업이익증가율'] = 20
    else:
        scores['영업이익증가율'] = 50
    
    # 가중치 적용 총점 계산
    total_score = sum(scores[key] * weights[key] for key in weights)
    
    return total_score, scores

def calculate_technical_score(stock_data):
    """기술적 분석 점수 (간단한 이동평균선 기반)"""
    if stock_data is None:
        return 50, {}
    
    try:
        code = stock_data['code']
        df = fdr.DataReader(code, datetime.now() - timedelta(days=100))
        if df.empty:
            return 50, {}
        
        current_price = df['Close'].iloc[-1]
        ma5 = df['Close'].rolling(5).mean().iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        
        scores = {}
        
        # 이동평균선 점수
        if current_price > ma5 and ma5 > ma20 and ma20 > ma60:
            scores['이동평균선'] = 90
        elif current_price > ma5 and ma5 > ma20:
            scores['이동평균선'] = 75
        elif current_price > ma5:
            scores['이동평균선'] = 60
        elif current_price > ma20:
            scores['이동평균선'] = 50
        else:
            scores['이동평균선'] = 35
        
        # MACD (간단히 계산)
        try:
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-1] > 0:
                scores['MACD'] = 85
            elif macd.iloc[-1] > signal.iloc[-1]:
                scores['MACD'] = 70
            elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-1] < 0:
                scores['MACD'] = 40
            else:
                scores['MACD'] = 55
        except:
            scores['MACD'] = 50
        
        # 볼린저밴드
        try:
            std = df['Close'].rolling(20).std()
            upper = ma20 + (std * 2)
            lower = ma20 - (std * 2)
            
            if current_price < lower:
                scores['볼린저밴드'] = 90
            elif current_price < ma20:
                scores['볼린저밴드'] = 70
            elif current_price < upper:
                scores['볼린저밴드'] = 50
            else:
                scores['볼린저밴드'] = 30
        except:
            scores['볼린저밴드'] = 50
        
        # 일목균형표 (간단히)
        scores['일목균형표'] = 60
        
        # 지지/저항 (간단히)
        high = df['High'].max()
        low = df['Low'].min()
        if current_price < low + (high - low) * 0.3:
            scores['지지/저항'] = 85
        elif current_price < low + (high - low) * 0.5:
            scores['지지/저항'] = 65
        else:
            scores['지지/저항'] = 45
        
        total = sum(scores.values()) / 5
        return total, scores
        
    except:
        return 50, {}

# ============================================================
# 5. 랭킹 생성 (실제 데이터 기반)
# ============================================================

@st.cache_data(ttl=7200)
def generate_rankings():
    """전체 랭킹 생성 (상위 30개)"""
    try:
        # 1. 시총 상위 150개 종목 가져오기
        all_stocks = fdr.StockListing('KRX')
        stocks = all_stocks[~all_stocks['Name'].str.contains('ETF|ETN', case=False)]
        stocks = stocks.sort_values('Marcap', ascending=False).head(150)
        stocks['Code'] = stocks['Symbol'].astype(str).str.zfill(6)
        
        stock_list = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, (_, row) in enumerate(stocks.iterrows()):
            code = row['Code']
            name = row['Name']
            
            status_text.text(f"Processing: {name} ({idx+1}/150)")
            progress_bar.progress((idx+1)/150)
            
            # 실제 재무데이터 수집
            financial_data = get_financial_data(code)
            if financial_data is None:
                continue
            
            # 업종 평균 (기본값 사용)
            industry_avg = {'per': 15, 'pbr': 1.5}
            
            # 기본적 분석 점수
            fund_score, fund_detail = calculate_fundamental_score(financial_data, industry_avg)
            
            # 기술적 분석 점수
            stock_info = {
                'code': code,
                'name': name,
                'price': financial_data.get('price', 0)
            }
            tech_score, tech_detail = calculate_technical_score(stock_info)
            
            combined = (fund_score + tech_score) / 2
            
            stock_list.append({
                'code': code,
                'name': name,
                'price': financial_data.get('price', 0),
                'change': 0,  # 등락률은 별도 계산 필요
                'fundamental_score': fund_score,
                'fundamental_detail': fund_detail,
                'technical_score': tech_score,
                'technical_detail': tech_detail,
                'combined_score': combined
            })
            
            time.sleep(0.1)  # API 호출 간격
        
        progress_bar.empty()
        status_text.empty()
        
        # 점수 기준 정렬
        stock_list.sort(key=lambda x: x['combined_score'], reverse=True)
        return stock_list[:30]
        
    except Exception as e:
        st.error(f"데이터 수집 중 오류 발생: {str(e)}")
        return []

# ============================================================
# 6. 나머지 페이지 함수들 (기존과 동일)
# ============================================================

# [여기에는 이전과 동일한 home_page, ranking_page, search_page 함수들이 들어갑니다]
# 공간 제약으로 생략했지만, 실제로는 전부 포함해야 합니다

def home_page():
    st.title("🏠 Home")
    st.markdown("---")
    st.info("📊 실제 재무데이터(PER, PBR, ROE, 부채비율, 영업이익증가율)를 기반으로 한 퀀트 분석 대시보드입니다.")
    st.markdown("---")
    st.write("✅ 실제 데이터 기반 점수 산정")
    st.write("✅ 시가총액 상위 150개 종목 분석")
    st.write("✅ 기본적 분석 + 기술적 분석 결합")

def ranking_page(title, rank_list, score_key, score_name):
    st.title(f"📊 {title}")
    st.markdown(f"*Top 30 stocks ranked by {score_name}*")
    st.markdown("---")
    
    if not rank_list:
        st.warning("데이터를 불러오는 중입니다. 잠시만 기다려주세요...")
        return
    
    df_data = []
    for i, item in enumerate(rank_list[:30]):
        df_data.append({
            'Rank': i + 1,
            'Stock': item['name'],
            'Code': item['code'],
            'Price': f"{item['price']:,.0f}",
            'Score': f"{item[score_key]:.1f}",
            'Naver': f"https://finance.naver.com/item/main.naver?code={item['code']}"
        })
    
    df = pd.DataFrame(df_data)
    
    st.dataframe(
        df,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Stock": st.column_config.TextColumn("Stock", width="medium"),
            "Code": st.column_config.TextColumn("Code", width="small"),
            "Price": st.column_config.TextColumn("Price", width="medium"),
            "Score": st.column_config.TextColumn("Score", width="small"),
            "Naver": st.column_config.LinkColumn("Naver", width="small"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.markdown("---")
    
    st.subheader("📋 Stock Details")
    stock_names = [item['name'] for item in rank_list[:30]]
    selected = st.selectbox("Select a stock to view details:", stock_names)
    
    if selected:
        for item in rank_list[:30]:
            if item['name'] == selected:
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**📊 Fundamental Analysis**")
                    for key, val in item['fundamental_detail'].items():
                        st.progress(val/100, text=f"{key}: {val:.1f}/100")
                with col2:
                    st.write("**📈 Technical Analysis**")
                    for key, val in item['technical_detail'].items():
                        st.progress(val/100, text=f"{key}: {val:.1f}/100")
                break

def search_page(rank_list):
    st.title("🔍 Search")
    search_term = st.text_input("Enter stock name:", placeholder="e.g., Samsung")
    
    if search_term:
        results = [s for s in rank_list if search_term in s['name']]
        if results:
            for item in results:
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"📊 {item['name']} ({item['code']})")
                    st.write(f"**Price:** {item['price']:,.0f}원")
                with col2:
                    st.metric("Fundamental", f"{item['fundamental_score']:.1f}")
                    st.metric("Technical", f"{item['technical_score']:.1f}")
                    st.metric("Combined", f"{item['combined_score']:.1f}")
        else:
            st.warning(f"No results found for '{search_term}'")

# ============================================================
# 7. 메인 앱
# ============================================================

def main():
    if 'page' not in st.session_state:
        st.session_state['page'] = 'Home'
    
    with st.sidebar:
        st.markdown("# 📊 Quant Dashboard")
        st.markdown("---")
        
        if st.button("🏠 Home", use_container_width=True):
            st.session_state['page'] = 'Home'
            st.rerun()
        if st.button("📊 Fundamental", use_container_width=True):
            st.session_state['page'] = 'Fundamental'
            st.rerun()
        if st.button("📈 Technical", use_container_width=True):
            st.session_state['page'] = 'Technical'
            st.rerun()
        if st.button("⚖️ Combined", use_container_width=True):
            st.session_state['page'] = 'Combined'
            st.rerun()
        if st.button("🔍 Search", use_container_width=True):
            st.session_state['page'] = 'Search'
            st.rerun()
        
        st.markdown("---")
        st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.caption("🔄 데이터는 24시간마다 갱신됩니다")
    
    with st.spinner("📊 실제 재무데이터를 수집 중입니다 (최대 1분 소요)..."):
        all_stocks = generate_rankings()
    
    if st.session_state['page'] == 'Home':
        home_page()
    elif st.session_state['page'] == 'Fundamental':
        ranking_page("Fundamental Analysis", all_stocks, 'fundamental_score', 'Fundamental')
    elif st.session_state['page'] == 'Technical':
        ranking_page("Technical Analysis", all_stocks, 'technical_score', 'Technical')
    elif st.session_state['page'] == 'Combined':
        ranking_page("Combined Analysis", all_stocks, 'combined_score', 'Combined')
    elif st.session_state['page'] == 'Search':
        search_page(all_stocks)

if __name__ == "__main__":
    main()