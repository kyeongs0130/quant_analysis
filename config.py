# config.py
import os
from pathlib import Path

# 기본 경로
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
DB_PATH = DATA_DIR / 'stock_data.db'

# 데이터 수집 설정
TOP_N_STOCKS = 150  # 시총 상위 150개

# 업데이트 시간 (KST)
UPDATE_TIMES = {
    'domestic': '15:30',  # 국내 장 종료
    'us': '06:00'         # 미국 장 종료 (다음날 아침)
}

# 기본적 분석 가중치
FUNDAMENTAL_WEIGHTS = {
    'per': 0.25,
    'pbr': 0.20,
    'operating_profit_growth': 0.20,
    'roe': 0.20,
    'debt_ratio': 0.15
}

# 기술적 분석 가중치
TECHNICAL_WEIGHTS = {
    'ma': 0.25,
    'macd': 0.20,
    'bollinger': 0.20,
    'ichimoku': 0.20,
    'support_resistance': 0.15
}

# 종합 평가 가중치
OVERALL_WEIGHTS = {
    'fundamental': 0.5,
    'technical': 0.5
}

# UI 설정
UI_CONFIG = {
    'background_color': '#000000',
    'text_color': '#FFFFFF',
    'accent_color': '#00FF88',
    'danger_color': '#FF4444',
    'warning_color': '#FFAA00'
}