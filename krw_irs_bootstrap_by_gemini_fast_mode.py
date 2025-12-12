# created by gemini fast mode
# prompt: KRW IRS bootstrap module을 python으로 작성해줘

import numpy as np
from datetime import date, timedelta
from typing import List, Dict, Tuple


class KrwIrsBootstrapper:
    """
    KRW IRS 시장 금리를 이용한 할인 계수(Discount Factor) 부트스트래핑 모듈.
    주의: 실제 시장 관례(Day Count, Business Day Rule 등)를 단순화하여 구현했습니다.
    """

    def __init__(self, settlement_date: date):
        """
        :param settlement_date: 기준일 (결제일)
        """
        self.settlement_date = settlement_date
        # 부트스트랩으로 계산된 할인 계수를 저장할 딕셔너리: {만기_일수: 할인_계수}
        self.discount_factors: Dict[int, float] = {}

    def get_time_in_years(self, target_date: date) -> float:
        """
        기준일로부터 목표일까지의 연 단위 시간(Time in Years)을 계산합니다.
        Actual/365 Day Count Convention을 단순 적용 (윤년 무시)
        """
        day_count = (target_date - self.settlement_date).days
        return day_count / 365.0

    def bootstrap_irs(self, tenors: List[int], market_rates: List[float]):
        """
        IRS 만기 및 시장 금리를 사용하여 순차적으로 할인 계수를 계산합니다.

        :param tenors: 만기 (예: 1, 2, 3... 년)
        :param market_rates: 각 만기에 해당하는 IRS Par Swap Rate (예: 0.035 = 3.5%)
        """
        if len(tenors) != len(market_rates):
            raise ValueError("만기 리스트와 금리 리스트의 길이가 일치해야 합니다.")

        sorted_instruments = sorted(zip(tenors, market_rates))

        for tenor, rate in sorted_instruments:
            # 해당 만기의 실제 날짜를 계산 (단순화: 월/일 무시)
            maturity_date = self.settlement_date + timedelta(days=tenor * 365)
            # 기준일로부터의 일수
            maturity_days = (maturity_date - self.settlement_date).days

            # --- 부트스트래핑 로직 시작 ---

            # 1. 이전 현금 흐름의 할인 계수 합계 (DF Sum)를 계산
            # 부트스트랩 특성상 이전 만기의 DF는 이미 계산되어 있어야 합니다.
            df_sum = 0.0

            # IRS는 만기까지의 모든 지급 시점에 대한 DF를 필요로 합니다.
            # 단순화를 위해 연 1회 지급(Annual)으로 가정
            for i in range(1, tenor):
                # 이전 지급 시점의 일수를 찾습니다 (정확한 구현은 날짜 규칙을 따라야 함)
                prev_pay_date = self.settlement_date + timedelta(days=i * 365)
                prev_days = (prev_pay_date - self.settlement_date).days

                # 이전 만기의 DF가 계산되어 있는지 확인
                if prev_days in self.discount_factors:
                    df_sum += self.discount_factors[prev_days]
                else:
                    # 중간 만기의 DF가 없으면 보간(Interpolation)이 필요하지만,
                    # 이 예제에서는 순차적인 만기(1Y, 2Y, 3Y...)만 사용한다고 가정
                    print(f"경고: {i}년 만기의 DF가 없어 0으로 간주하고 계속합니다.")

            # 2. 현재 만기(n)의 할인 계수(DF_n) 계산
            # Par Swap Rate 공식 기반 역산: DF_n = (1 - Rate * DF_Sum) / (1 + Rate)
            # 여기서 Rate는 고정금리 leg의 Payment Frequency에 맞게 조정되어야 하지만,
            # 단순화를 위해 Annually (1년) 이자 지급 가정으로 Day Count Factor (DCF)를 1로 간주

            # Note: DCF_n = self.get_time_in_years(maturity_date) - self.get_time_in_years(prev_pay_date)
            # 연 1회 지급 가정에서는 마지막을 제외하고 DCF는 1.0 (연차)

            # Simplified formula assuming annual payments and DCF=1 for all intermediate payments
            df_n = (1 - rate * df_sum) / (1 + rate)

            # 결과 저장
            self.discount_factors[maturity_days] = df_n

            print(f"만기 {tenor}년 (DF Index: {maturity_days}일): 시장 금리 {rate * 100:.2f}%, DF {df_n:.6f}")

        print("\n--- 부트스트랩 완료 ---")
        self.calculate_zero_rates()

    def calculate_zero_rates(self):
        """
        계산된 할인 계수로부터 Zero-Coupon Rate (제로 금리)를 계산합니다.
        """
        zero_rates: Dict[int, float] = {}
        print("\n** Zero-Coupon Rates **")

        sorted_dfs = sorted(self.discount_factors.items())

        for days, df in sorted_dfs:
            time_in_years = self.get_time_in_years(self.settlement_date + timedelta(days=days))
            # 제로 금리 공식: ZeroRate = (1/DF)^(1/T) - 1
            if df > 0 and time_in_years > 0:
                zero_rate = (1 / df) ** (1 / time_in_years) - 1
                zero_rates[days] = zero_rate
                print(f"만기 {time_in_years:.2f}년: DF {df:.6f}, Zero Rate {zero_rate * 100:.4f}%")

        return zero_rates


# --- 사용 예시 ---

# 1. 기준일 설정
settle_date = date(2025, 12, 12)

# 2. KRW IRS 시장 관측 금리 (예시 데이터)
# 만기 (년)
krw_tenors = [1, 2, 3, 4, 5, 7, 10]
# IRS Par Swap Rate (예: 1Y=3.50%, 10Y=4.20%)
# 실제 시장 데이터는 예금/FRA/IRS 등을 혼합하여 사용합니다.
krw_swap_rates = [0.0350, 0.0370, 0.0385, 0.0395, 0.0405, 0.0415, 0.0420]

# 3. 부트스트래퍼 초기화 및 실행
bootstrapper = KrwIrsBootstrapper(settle_date)
bootstrapper.bootstrap_irs(krw_tenors, krw_swap_rates)