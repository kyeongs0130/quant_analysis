# analysis/fundamental.py
import pandas as pd
import numpy as np
from config import FUNDAMENTAL_WEIGHTS

class FundamentalAnalyzer:
    def __init__(self):
        self.weights = FUNDAMENTAL_WEIGHTS
        
    def calculate_per_score(self, per, industry_per_avg):
        """
        PER 평가 (낮을수록 좋음)
        업종 평균 대비 평가
        """
        if per is None or industry_per_avg is None or industry_per_avg <= 0:
            return 50
        
        if per <= 0:
            return 80  # PER이 음수면 적자기업이지만 일단 점수 부여
        
        ratio = industry_per_avg / per
        # ratio가 2 이상이면 만점, 0.5 이하면 0점
        score = min(max((ratio - 0.5) / 1.5 * 100, 0), 100)
        return score
    
    def calculate_pbr_score(self, pbr, industry_pbr_avg):
        """
        PBR 평가 (낮을수록 좋음)
        """
        if pbr is None or industry_pbr_avg is None or industry_pbr_avg <= 0:
            return 50
        
        if pbr <= 0:
            return 80
        
        ratio = industry_pbr_avg / pbr
        score = min(max((ratio - 0.5) / 1.5 * 100, 0), 100)
        return score
    
    def calculate_growth_score(self, growth_rate):
        """
        영업이익 증가율 평가
        """
        if growth_rate is None:
            return 50
        
        # -50% ~ +100% 범위를 0~100점으로 매핑
        # (증가율이 높을수록 좋음)
        score = min(max((growth_rate + 50) / 150 * 100, 0), 100)
        return score
    
    def calculate_roe_score(self, roe):
        """
        ROE 평가 (높을수록 좋음)
        """
        if roe is None:
            return 50
        
        # 0% ~ 30% 범위를 0~100점으로 매핑
        score = min(max(roe / 30 * 100, 0), 100)
        return score
    
    def calculate_debt_score(self, debt_ratio, industry_debt_avg):
        """
        부채비율 평가 (낮을수록 좋음)
        """
        if debt_ratio is None or industry_debt_avg is None or industry_debt_avg <= 0:
            return 50
        
        if debt_ratio <= 0:
            return 90
        
        ratio = industry_debt_avg / debt_ratio
        score = min(max((ratio - 0.3) / 1.7 * 100, 0), 100)
        return score
    
    def analyze_stock(self, stock_data, industry_data):
        """
        종목 하나에 대한 기본적 분석 수행
        """
        scores = {}
        
        # 각 지표 계산
        scores['per'] = self.calculate_per_score(
            stock_data.get('per'), 
            industry_data.get('per_avg')
        )
        scores['pbr'] = self.calculate_pbr_score(
            stock_data.get('pbr'), 
            industry_data.get('pbr_avg')
        )
        scores['growth'] = self.calculate_growth_score(
            stock_data.get('operating_profit_growth')
        )
        scores['roe'] = self.calculate_roe_score(
            stock_data.get('roe')
        )
        scores['debt'] = self.calculate_debt_score(
            stock_data.get('debt_ratio'), 
            industry_data.get('debt_avg')
        )
        
        # 가중 평균 계산
        total_score = sum(scores[key] * self.weights[key] for key in self.weights)
        
        return {
            'scores': scores,
            'total': round(total_score, 2)
        }
    
    def analyze_all_stocks(self, stock_data_dict):
        """
        모든 종목에 대한 기본적 분석 수행
        """
        from utils.industry import get_industry_averages
        
        results = {}
        
        for code, data in stock_data_dict.items():
            # 업종 평균 데이터 계산
            industry_avg = get_industry_averages(code, stock_data_dict)
            
            # 분석 수행
            result = self.analyze_stock(data, industry_avg)
            results[code] = result
        
        return results