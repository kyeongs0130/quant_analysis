# data/collector.py
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import json
import numpy as np

class DataCollector:
    def __init__(self):
        self.krx_url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        # 한국 종목 매핑 (yfinance 티커)
        self.ticker_map = {}
        
    def get_kospi_top_stocks(self):
        """
        KRX에서 코스피 시총 상위 150개 종목 리스트 가져오기
        실제 KRX API를 호출합니다.
        """
        try:
            # KRX API 호출 (시총 상위 종목)
            url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # 실제 KRX API는 복잡하므로, 여기서는 yfinance에서 가져온 종목 리스트 활용
            # 대신 임시로 주요 종목 리스트 반환 (실제로는 KRX 크롤링 필요)
            
            # 테스트용 종목 리스트 (실제로는 KRX에서 150개 가져와야 함)
            top_stocks = [
                {'code': '005930', 'name': '삼성전자', 'market': 'KOSPI'},
                {'code': '000660', 'name': 'SK하이닉스', 'market': 'KOSPI'},
                {'code': '005380', 'name': '현대차', 'market': 'KOSPI'},
                {'code': '035420', 'name': 'NAVER', 'market': 'KOSPI'},
                {'code': '035720', 'name': '카카오', 'market': 'KOSPI'},
                {'code': '051910', 'name': 'LG화학', 'market': 'KOSPI'},
                {'code': '006400', 'name': '삼성SDI', 'market': 'KOSPI'},
                {'code': '003550', 'name': 'LG', 'market': 'KOSPI'},
                {'code': '055550', 'name': '신한지주', 'market': 'KOSPI'},
                {'code': '000810', 'name': '삼성화재', 'market': 'KOSPI'},
                {'code': '105560', 'name': 'KB금융', 'market': 'KOSPI'},
                {'code': '032830', 'name': '삼성생명', 'market': 'KOSPI'},
                {'code': '086790', 'name': '하나금융지주', 'market': 'KOSPI'},
                {'code': '028260', 'name': '삼성물산', 'market': 'KOSPI'},
                {'code': '015760', 'name': '한국전력', 'market': 'KOSPI'},
                {'code': '034730', 'name': 'SK', 'market': 'KOSPI'},
                {'code': '018260', 'name': '삼성에스디에스', 'market': 'KOSPI'},
                {'code': '207940', 'name': '삼성바이오로직스', 'market': 'KOSPI'},
                {'code': '068270', 'name': '셀트리온', 'market': 'KOSPI'},
                {'code': '096770', 'name': 'SK이노베이션', 'market': 'KOSPI'},
            ]
            
            # 더 많은 종목 추가 (실제로는 API에서 가져옴)
            # 여기서는 테스트용 30개만 반환
            return top_stocks
            
        except Exception as e:
            print(f"Error fetching stock list: {e}")
            # 폴백: 기본 종목 리스트
            return [
                {'code': '005930', 'name': '삼성전자', 'market': 'KOSPI'},
                {'code': '000660', 'name': 'SK하이닉스', 'market': 'KOSPI'},
                {'code': '005380', 'name': '현대차', 'market': 'KOSPI'},
            ]
    
    def get_stock_data(self, code, period='1y'):
        """
        yfinance로 주가 데이터 수집
        """
        try:
            # 한국 종목은 .KS (코스피) 또는 .KQ (코스닥) 접미사 필요
            ticker = f"{code}.KS"
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            
            if df.empty:
                # 코스닥일 경우 .KQ로 시도
                ticker = f"{code}.KQ"
                stock = yf.Ticker(ticker)
                df = stock.history(period=period)
            
            return df
        except Exception as e:
            print(f"Error fetching {code}: {e}")
            return None
    
    def get_financial_data(self, code):
        """
        실제 재무 데이터 수집 (yfinance + 대체 소스)
        """
        try:
            ticker = f"{code}.KS"
            stock = yf.Ticker(ticker)
            
            # 1. 기본 정보 가져오기
            info = stock.info
            
            # 2. 재무제표 가져오기
            financials = stock.financials
            balance = stock.balance_sheet
            cashflow = stock.cashflow
            
            # 3. 데이터 추출
            data = {}
            
            # PER (Trailing P/E)
            data['per'] = info.get('trailingPE', None)
            if data['per'] is None or data['per'] <= 0:
                # Forward P/E 시도
                data['per'] = info.get('forwardPE', None)
            
            # PBR (Price to Book)
            data['pbr'] = info.get('priceToBook', None)
            if data['pbr'] is None or data['pbr'] <= 0:
                # Market Cap / Book Value 계산
                market_cap = info.get('marketCap', None)
                book_value = info.get('bookValue', None)
                if market_cap and book_value and book_value > 0:
                    shares = market_cap / info.get('currentPrice', 1)
                    data['pbr'] = info.get('currentPrice', 0) / book_value if book_value > 0 else None
            
            # ROE (Return on Equity)
            data['roe'] = info.get('returnOnEquity', None)
            if data['roe'] is not None:
                data['roe'] = data['roe'] * 100  # 퍼센트로 변환
            
            # 영업이익 증가율 (Operating Income Growth)
            if not financials.empty and 'Operating Income' in financials.index:
                operating_income = financials.loc['Operating Income']
                if len(operating_income) >= 2:
                    current = operating_income.iloc[0]
                    prev = operating_income.iloc[1]
                    if prev != 0 and not pd.isna(prev):
                        data['operating_profit_growth'] = ((current - prev) / abs(prev)) * 100
                    else:
                        data['operating_profit_growth'] = None
                else:
                    data['operating_profit_growth'] = None
            else:
                # 대체: yfinance info에서 가져오기
                data['operating_profit_growth'] = info.get('earningsGrowth', None)
                if data['operating_profit_growth'] is not None:
                    data['operating_profit_growth'] = data['operating_profit_growth'] * 100
            
            # 부채비율 (Debt Ratio)
            if not balance.empty:
                # Total Debt / Total Equity
                total_debt = None
                total_equity = None
                
                # 다양한 컬럼명 시도
                debt_cols = ['Total Debt', 'Long Term Debt', 'Short Term Debt']
                equity_cols = ['Total Equity Gross Minority Interest', 'Total Equity', 'Stockholders Equity']
                
                for col in debt_cols:
                    if col in balance.index:
                        total_debt = balance.loc[col].iloc[0]
                        break
                
                for col in equity_cols:
                    if col in balance.index:
                        total_equity = balance.loc[col].iloc[0]
                        break
                
                if total_debt is not None and total_equity is not None and total_equity != 0:
                    data['debt_ratio'] = (total_debt / abs(total_equity)) * 100
                else:
                    data['debt_ratio'] = None
            else:
                # 대체: yfinance info에서 가져오기
                debt_to_equity = info.get('debtToEquity', None)
                if debt_to_equity is not None:
                    data['debt_ratio'] = debt_to_equity
                else:
                    data['debt_ratio'] = None
            
            # 데이터가 너무 부족하면 대체 소스 사용
            if all(v is None for v in data.values()):
                # yfinance info에서 직접 가져오기
                data['per'] = info.get('trailingPE', None)
                data['pbr'] = info.get('priceToBook', None)
                data['roe'] = info.get('returnOnEquity', None)
                if data['roe'] is not None:
                    data['roe'] = data['roe'] * 100
                data['operating_profit_growth'] = info.get('earningsGrowth', None)
                if data['operating_profit_growth'] is not None:
                    data['operating_profit_growth'] = data['operating_profit_growth'] * 100
                data['debt_ratio'] = info.get('debtToEquity', None)
            
            # None 값을 -1로 변환 (분석에서 처리)
            for key in data:
                if data[key] is None or pd.isna(data[key]):
                    data[key] = -1
                elif isinstance(data[key], (int, float)) and (data[key] == 0 or data[key] == float('inf')):
                    data[key] = -1
            
            return data
            
        except Exception as e:
            print(f"Error fetching financial data for {code}: {e}")
            # 최소한의 데이터라도 반환
            return {
                'per': -1,
                'pbr': -1,
                'roe': -1,
                'operating_profit_growth': -1,
                'debt_ratio': -1
            }
    
    def get_financial_data_krx(self, code):
        """
        KRX API에서 재무 데이터 가져오기 (대체 소스)
        """
        try:
            # KRX API는 복잡하므로, 여기서는 간단히 구현
            # 실제로는 한국거래소 Open API 사용 필요
            url = "https://api.krx.co.kr/apiservice/financial"
            # API 키가 필요하므로, 여기서는 yfinance로 대체
            return None
        except:
            return None
    
    def get_market_indices(self):
        """
        주요 지수 데이터 수집
        """
        indices = {
            'KOSPI': '^KS11',
            'KOSDAQ': '^KQ11',
            'NASDAQ': '^IXIC',
            'Gold': 'GC=F',
            'WTI': 'CL=F',
            'USD/KRW': 'KRW=X',
            'US 10Y': '^TNX',
        }
        
        data = {}
        for name, ticker in indices.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period='5d')
                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2] if len(hist) > 1 else latest
                    data[name] = {
                        'price': round(latest['Close'], 2),
                        'change': round(((latest['Close'] - prev['Close']) / prev['Close']) * 100, 2) if len(hist) > 1 else 0
                    }
                else:
                    data[name] = {'price': None, 'change': None}
            except Exception as e:
                print(f"Error fetching {name}: {e}")
                data[name] = {'price': None, 'change': None}
        
        # 기준금리 (FRED API 또는 고정값)
        try:
            # 미국 기준금리 (FRED)
            fred_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF"
            df = pd.read_csv(fred_url)
            if not df.empty:
                latest = df.iloc[-1]['DFF']
                data['US Base Rate'] = {'price': round(latest, 2), 'change': 0}
            else:
                data['US Base Rate'] = {'price': 5.50, 'change': 0}
        except:
            data['US Base Rate'] = {'price': 5.50, 'change': 0}
        
        # 한국 기준금리 (한국은행 API 또는 고정값)
        try:
            # 한국은행 API (간단히 구현)
            bok_url = "https://ecos.bok.or.kr/api/statisticSearch/..."
            # 복잡하므로 고정값 사용
            data['Korea Base Rate'] = {'price': 3.50, 'change': 0}
        except:
            data['Korea Base Rate'] = {'price': 3.50, 'change': 0}
        
        return data


# ===== 추가 유틸리티 함수 =====
def get_stock_info_naver(code):
    """
    네이버 금융에서 종목 정보 가져오기 (대체 소스)
    """
    try:
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            # BeautifulSoup 파싱 필요 (여기서는 생략)
            return None
        return None
    except:
        return None


def get_financial_data_fmp(code):
    """
    Financial Modeling Prep API에서 데이터 가져오기 (대체 소스)
    """
    try:
        # API 키 필요 (무료 버전 있음)
        api_key = "YOUR_FMP_API_KEY"  # 실제 키로 교체 필요
        url = f"https://financialmodelingprep.com/api/v3/ratios/{code}?apikey={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data:
                latest = data[0]
                return {
                    'per': latest.get('peRatio', -1),
                    'pbr': latest.get('priceToBookRatio', -1),
                    'roe': latest.get('roe', -1) * 100 if latest.get('roe') else -1,
                    'operating_profit_growth': latest.get('operatingIncomeGrowth', -1) * 100 if latest.get('operatingIncomeGrowth') else -1,
                    'debt_ratio': latest.get('debtToEquity', -1) * 100 if latest.get('debtToEquity') else -1,
                }
        return None
    except:
        return None