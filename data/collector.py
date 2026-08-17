# data/collector.py
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import json

class DataCollector:
    def __init__(self):
        self.krx_url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        
    def get_kospi_top_stocks(self):
        """
        KRX에서 코스피 시총 상위 종목 리스트 가져오기
        실제로는 KRX API를 호출해야 하지만,
        여기서는 임시로 주요 종목 리스트를 반환
        """
        # 실제로는 KRX에서 150개를 가져와야 함
        # 현재는 테스트용 주요 종목 30개만 제공
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
        return top_stocks
    
    def get_stock_data(self, code, period='1y'):
        """
        yfinance로 주가 데이터 수집
        """
        try:
            # 한국 종목은 .KS (코스피) 또는 .KQ (코스닥) 접미사 필요
            # 여기서는 일단 .KS로 시도
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
        재무 데이터 수집 (yfinance)
        """
        try:
            ticker = f"{code}.KS"
            stock = yf.Ticker(ticker)
            
            # 재무제표
            financials = stock.financials
            balance = stock.balance_sheet
            cashflow = stock.cashflow
            
            # 주요 지표 추출
            data = {}
            
            # PER
            info = stock.info
            data['per'] = info.get('trailingPE', None)
            data['pbr'] = info.get('priceToBook', None)
            data['roe'] = info.get('returnOnEquity', None) * 100 if info.get('returnOnEquity') else None
            
            # 영업이익 증가율 (전년 대비)
            if not financials.empty and 'Operating Income' in financials.index:
                operating_income = financials.loc['Operating Income']
                if len(operating_income) >= 2:
                    current = operating_income.iloc[0]
                    prev = operating_income.iloc[1]
                    if prev != 0:
                        data['operating_profit_growth'] = ((current - prev) / abs(prev)) * 100
                    else:
                        data['operating_profit_growth'] = None
                else:
                    data['operating_profit_growth'] = None
            else:
                data['operating_profit_growth'] = None
            
            # 부채비율
            if not balance.empty and 'Total Debt' in balance.index and 'Total Equity Gross Minority Interest' in balance.index:
                total_debt = balance.loc['Total Debt'].iloc[0] if 'Total Debt' in balance.index else 0
                total_equity = balance.loc['Total Equity Gross Minority Interest'].iloc[0] if 'Total Equity Gross Minority Interest' in balance.index else 1
                if total_equity != 0:
                    data['debt_ratio'] = (total_debt / total_equity) * 100
                else:
                    data['debt_ratio'] = None
            else:
                data['debt_ratio'] = None
            
            return data
            
        except Exception as e:
            print(f"Error fetching financial data for {code}: {e}")
            return {
                'per': None,
                'pbr': None,
                'roe': None,
                'operating_profit_growth': None,
                'debt_ratio': None
            }
    
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
        
        # 한국 기준금리, 미국 기준금리는 별도로 처리
        # (FRED API 등 사용 필요)
        
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
        
        # 기준금리 (임시 데이터)
        data['한국 기준금리'] = {'price': 3.50, 'change': 0}
        data['미국 기준금리'] = {'price': 5.50, 'change': 0}
        
        return data