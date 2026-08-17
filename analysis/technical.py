# analysis/technical.py
import pandas as pd
import numpy as np
from config import TECHNICAL_WEIGHTS

class TechnicalAnalyzer:
    def __init__(self):
        self.weights = TECHNICAL_WEIGHTS
        
    def calculate_ma_score(self, df):
        """
        이동평균선 평가 (5, 20, 60일)
        """
        if df is None or len(df) < 60:
            return 50
        
        close = df['Close']
        ma5 = close.rolling(5).mean()
        ma20 = close.rolling(20).mean()
        ma60 = close.rolling(60).mean()
        
        latest = close.iloc[-1]
        ma5_latest = ma5.iloc[-1]
        ma20_latest = ma20.iloc[-1]
        ma60_latest = ma60.iloc[-1]
        
        score = 50
        
        # 정배열/역배열 평가
        if ma5_latest > ma20_latest > ma60_latest:
            score += 25
        elif ma5_latest > ma20_latest:
            score += 12
        elif ma5_latest < ma20_latest < ma60_latest:
            score -= 25
        elif ma5_latest < ma20_latest:
            score -= 12
        
        # 현재가 vs 이동평균선
        if latest > ma5_latest > ma20_latest:
            score += 10
        elif latest < ma5_latest < ma20_latest:
            score -= 10
        elif latest > ma20_latest:
            score += 5
        elif latest < ma20_latest:
            score -= 5
        
        return max(0, min(100, score))
    
    def calculate_macd_score(self, df):
        """
        MACD 평가
        """
        if df is None or len(df) < 26:
            return 50
        
        close = df['Close']
        
        # MACD 계산
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        
        if len(macd_line) < 2:
            return 50
        
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2] if len(macd_line) > 1 else current_macd
        prev_signal = signal_line.iloc[-2] if len(signal_line) > 1 else current_signal
        
        score = 50
        
        # MACD 시그널 크로스
        if current_macd > current_signal and prev_macd <= prev_signal:
            score += 25  # 골든 크로스
        elif current_macd < current_signal and prev_macd >= prev_signal:
            score -= 25  # 데드 크로스
        
        # 히스토그램 방향
        if len(histogram) > 1:
            if histogram.iloc[-1] > histogram.iloc[-2]:
                score += 15
            elif histogram.iloc[-1] < histogram.iloc[-2]:
                score -= 15
        
        # 0선 기준
        if current_macd > 0:
            score += 10
        else:
            score -= 10
        
        return max(0, min(100, score))
    
    def calculate_bollinger_score(self, df):
        """
        볼린저 밴드 평가
        """
        if df is None or len(df) < 20:
            return 50
        
        close = df['Close']
        window = 20
        std = close.rolling(window).std()
        middle = close.rolling(window).mean()
        upper = middle + (std * 2)
        lower = middle - (std * 2)
        
        latest = close.iloc[-1]
        upper_latest = upper.iloc[-1]
        middle_latest = middle.iloc[-1]
        lower_latest = lower.iloc[-1]
        
        score = 50
        
        # 밴드 내 위치
        if latest > upper_latest:
            score = 90  # 과매수
        elif latest < lower_latest:
            score = 10  # 과매도
        else:
            # 밴드 내 위치를 0~100으로 매핑 (하단=매수기회)
            band_width = upper_latest - lower_latest
            if band_width > 0:
                position = (latest - lower_latest) / band_width
                # 하단(0)일 때 100점, 상단(1)일 때 0점
                score = 100 - (position * 100)
        
        # 밴드 수축/확장
        if len(upper) > 1:
            prev_upper = upper.iloc[-2]
            prev_lower = lower.iloc[-2]
            prev_width = prev_upper - prev_lower
            current_width = upper_latest - lower_latest
            
            if current_width < prev_width * 0.9:
                score += 10  # 밴드 수축 = 변동성 감소
            elif current_width > prev_width * 1.1:
                score -= 10  # 밴드 확장 = 변동성 증가
        
        return max(0, min(100, score))
    
    def calculate_ichimoku_score(self, df):
        """
        일목균형표 평가
        """
        if df is None or len(df) < 52:
            return 50
        
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        # 전환선 (9일)
        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
        # 기준선 (26일)
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
        # 선행스팬 A (26일 후)
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        # 선행스팬 B (52일 후)
        senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
        
        latest = close.iloc[-1]
        tenkan_latest = tenkan.iloc[-1]
        kijun_latest = kijun.iloc[-1]
        senkou_a_latest = senkou_a.iloc[-1] if not pd.isna(senkou_a.iloc[-1]) else 0
        senkou_b_latest = senkou_b.iloc[-1] if not pd.isna(senkou_b.iloc[-1]) else 0
        
        score = 50
        
        # 전환선 vs 기준선
        if tenkan_latest > kijun_latest:
            score += 15
        else:
            score -= 15
        
        # 현재가 vs 구름대
        cloud_top = max(senkou_a_latest, senkou_b_latest)
        cloud_bottom = min(senkou_a_latest, senkou_b_latest)
        
        if latest > cloud_top:
            score += 20  # 구름대 위 = 강세
        elif latest < cloud_bottom:
            score -= 20  # 구름대 아래 = 약세
        
        # 구름대 방향 (상승/하락)
        if len(senkou_a) > 27:
            prev_senkou_a = senkou_a.iloc[-27] if not pd.isna(senkou_a.iloc[-27]) else 0
            if senkou_a_latest > prev_senkou_a:
                score += 10
            else:
                score -= 10
        
        return max(0, min(100, score))
    
    def calculate_sr_score(self, df):
        """
        지지/저항 평가
        """
        if df is None or len(df) < 20:
            return 50
        
        high = df['High']
        low = df['Low']
        close = df['Close']
        latest = close.iloc[-1]
        
        # 최근 20일 고점/저점
        recent_high = high.tail(20).max()
        recent_low = low.tail(20).min()
        
        # 최근 60일 고점/저점 (추세 확인용)
        high_60 = high.tail(60).max()
        low_60 = low.tail(60).min()
        
        score = 50
        
        # 현재가가 저점 근처 (지지) = 매수 기회
        if latest <= recent_low * 1.03:
            score = 85
        # 현재가가 고점 근처 (저항) = 매도 고려
        elif latest >= recent_high * 0.97:
            score = 15
        else:
            # 고점과 저점 사이 위치 평가
            range_width = recent_high - recent_low
            if range_width > 0:
                position = (latest - recent_low) / range_width
                score = 85 - (position * 70)  # 저점에 가까울수록 높은 점수
        
        # 60일 고점/저점 돌파 여부
        if latest > high_60:
            score += 10
        elif latest < low_60:
            score -= 10
        
        return max(0, min(100, score))
    
    def analyze_stock(self, df):
        """
        종목 하나에 대한 기술적 분석 수행
        """
        if df is None or len(df) < 60:
            return {'total': 50, 'scores': {key: 50 for key in self.weights}}
        
        scores = {}
        scores['ma'] = self.calculate_ma_score(df)
        scores['macd'] = self.calculate_macd_score(df)
        scores['bollinger'] = self.calculate_bollinger_score(df)
        scores['ichimoku'] = self.calculate_ichimoku_score(df)
        scores['sr'] = self.calculate_sr_score(df)
        
        total_score = sum(scores[key] * self.weights[key] for key in self.weights)
        
        return {
            'scores': scores,
            'total': round(total_score, 2)
        }