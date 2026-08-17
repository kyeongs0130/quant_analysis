# utils/industry.py
import pandas as pd
import numpy as np

# 한국 시장 업종 분류 (WICS 기준)
# 실제 데이터는 KRX에서 수집
INDUSTRY_CLASSIFICATION = {
    '005930': 'IT',          # 삼성전자
    '000660': 'IT',          # SK하이닉스
    '005380': '자동차',       # 현대차
    '035420': 'IT',          # NAVER
    '035720': 'IT',          # 카카오
    '051910': 'IT',          # LG화학
    '006400': '금융',         # 삼성SDI
    '003550': '금융',         # LG
    '055550': '금융',         # 신한지주
    '000810': '금융',         # 삼성화재
    '105560': '금융',         # KB금융
    '032830': '금융',         # 삼성생명
    '086790': '금융',         # 하나금융지주
    '028260': 'IT',          # 삼성물산
    '015760': 'IT',          # 한국전력
    '034730': 'IT',          # SK
    '018260': 'IT',          # 삼성에스디에스
    '207940': '바이오',       # 삼성바이오로직스
    '068270': '바이오',       # 셀트리온
    '096770': 'IT',          # SK이노베이션
    # ... 실제로는 더 많은 종목이 필요
}

def get_industry(stock_code):
    """
    종목코드로 업종 반환
    """
    return INDUSTRY_CLASSIFICATION.get(stock_code, '기타')

def get_industry_peers(stock_code, stock_list):
    """
    같은 업종의 종목들 반환
    """
    my_industry = get_industry(stock_code)
    return [s for s in stock_list if get_industry(s) == my_industry]

def get_industry_averages(stock_code, stock_data_dict):
    """
    같은 업종의 평균 재무지표 계산
    """
    industry = get_industry(stock_code)
    peers = [code for code in stock_data_dict.keys() if get_industry(code) == industry]
    
    if not peers:
        return {
            'per_avg': 15,
            'pbr_avg': 1.5,
            'debt_avg': 100,
            'roe_avg': 10
        }
    
    per_list = []
    pbr_list = []
    debt_list = []
    roe_list = []
    
    for code in peers:
        data = stock_data_dict.get(code, {})
        if data.get('per') and data['per'] > 0:
            per_list.append(data['per'])
        if data.get('pbr') and data['pbr'] > 0:
            pbr_list.append(data['pbr'])
        if data.get('debt_ratio') and data['debt_ratio'] > 0:
            debt_list.append(data['debt_ratio'])
        if data.get('roe') and data['roe'] > 0:
            roe_list.append(data['roe'])
    
    return {
        'per_avg': np.mean(per_list) if per_list else 15,
        'pbr_avg': np.mean(pbr_list) if pbr_list else 1.5,
        'debt_avg': np.mean(debt_list) if debt_list else 100,
        'roe_avg': np.mean(roe_list) if roe_list else 10
    }