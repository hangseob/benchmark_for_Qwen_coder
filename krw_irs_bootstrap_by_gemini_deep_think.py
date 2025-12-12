import numpy as np
from scipy.interpolate import interp1d


class SimpleBootstrap:
    def __init__(self):
        # 1. 보간(Interpolation)을 위한 기준점 초기화
        # t=0 시점의 할인계수는 항상 1.0 (현재 가치 = 현재 가치)
        self.times = [0.0]
        self.discount_factors = [1.0]

        # 2. 결과 저장용 리스트
        self.result_tenors = []  # 만기 (년)
        self.result_market_rates = []  # 입력된 시장 금리 (Market Quote)
        self.result_zeros = []  # 계산된 제로 금리
        self.result_dfs = []  # 계산된 할인 계수

    def bootstrap(self, market_data):
        """
        :param market_data: list of tuples (Year, Rate)
        """
        # 만기 순서대로 정렬 (중요)
        data = sorted(market_data, key=lambda x: x[0])

        for T_end, par_rate in data:
            # KRW IRS 현금 흐름 주기: 분기 지급 (0.25년) 가정
            dt = 0.25

            # 현금 흐름 시점 생성 (예: 0.25, 0.50 ... T_end)
            # floating point error 방지를 위해 약간의 여유값(0.001) 추가
            cashflow_times = np.arange(dt, T_end + 0.001, dt)

            sum_val = 0.0

            # --- 보간 함수 생성 (Log-Linear) ---
            # self.times에는 항상 (0.0, 1.0)과 이전 계산된 점들이 포함되어 있음
            f_interp = interp1d(
                self.times,
                np.log(self.discount_factors),
                kind='linear',
                fill_value="extrapolate"
            )

            # 마지막 현금흐름(만기일)을 제외한 중간 이자 지급액들의 현재 가치 합산
            for t in cashflow_times[:-1]:
                df_t = np.exp(f_interp(t))
                sum_val += df_t * dt

            # --- 부트스트랩 공식 ---
            # DF_n = (1 - SwapRate * Sum(DF_prev * dt)) / (1 + SwapRate * dt)
            df_n = (1.0 - par_rate * sum_val) / (1.0 + par_rate * dt)

            # --- 제로 금리 역산 (연속 복리) ---
            # ZeroRate = -ln(DF) / T
            zero_r = -np.log(df_n) / T_end

            # [중요] 다음 만기 계산을 위해 현재 결과를 보간 기준점에 추가
            self.times.append(T_end)
            self.discount_factors.append(df_n)

            # 결과 리스트에 저장
            self.result_tenors.append(T_end)
            self.result_market_rates.append(par_rate)  # <--- 시장 금리 저장
            self.result_zeros.append(zero_r)
            self.result_dfs.append(df_n)

        return self.result_tenors, self.result_market_rates, self.result_zeros, self.result_dfs


# --- 실행 및 출력 ---
if __name__ == "__main__":
    # 입력 데이터: (만기 년수, 시장 금리)
    market_quotes = [
        (1.00, 0.03),
        (5.00, 0.04),
        (10.0, 0.05)
    ]

    bootstrapper = SimpleBootstrap()
    # 결과 반환값 4개 받기 (Tenor, MarketRate, ZeroRate, DF)
    tenors, market_rates, zeros, dfs = bootstrapper.bootstrap(market_quotes)

    # 출력 포맷 설정
    header = f"{'Maturity(Y)':<12} | {'Mkt Rate(%)':<12} | {'Zero Rate(%)':<12} | {'Discount Factor':<15}"
    print(header)
    print("-" * len(header))

    for i in range(len(tenors)):
        print(f"{tenors[i]:<12.2f} | {market_rates[i] * 100:<12.2f} | {zeros[i] * 100:<12.4f} | {dfs[i]:<15.6f}")