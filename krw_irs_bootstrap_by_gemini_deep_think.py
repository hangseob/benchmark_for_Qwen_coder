import numpy as np
from scipy.interpolate import interp1d


class SimpleBootstrap:
    def __init__(self):
        self.tenors = []  # 만기 (년 단위)
        self.zero_rates = []  # 제로 금리
        self.dfs = []  # 할인 계수

    def discount_factor(self, r, t):
        """연속 복리 가정: e^(-rt)"""
        return np.exp(-r * t)

    def bootstrap(self, market_data):
        """
        :param market_data: list of tuples (Year, Rate)
        Sorted by year e.g. [(0.25, 0.035), (1.0, 0.036)...]
        """
        # 데이터 정렬
        data = sorted(market_data, key=lambda x: x[0])

        times = []
        discount_factors = []

        for T_end, par_rate in data:
            # Swap Valuation Formula: PV_float = PV_fixed = 0 (at par)
            # 1 = ParRate * sum(DF(ti) * dt) + DF(Tn)
            # DF(Tn) = (1 - ParRate * sum(DF(ti)*dt_prev)) / (1 + ParRate * dt_last)

            # 현금 흐름 주기 가정 (KRW IRS는 보통 분기 지급 = 0.25년)
            dt = 0.25
            cashflow_times = np.arange(dt, T_end + 0.001, dt)

            sum_val = 0.0

            # 마지막 현금흐름(Tn)을 제외한 이전 현금흐름의 가치 계산
            for t in cashflow_times[:-1]:
                # 이미 계산된 구간이면 가져오고, 없으면 보간(Interpolation)
                if times:
                    # Log-Linear Interpolation for DF
                    f_interp = interp1d(times, np.log(discount_factors), kind='linear', fill_value="extrapolate")
                    df_t = np.exp(f_interp(t))
                else:
                    # 첫 데이터 전이면 Flat Rate 가정
                    df_t = 1.0 / (1 + par_rate * t)

                sum_val += df_t * dt

            # 마지막 시점(Tn)의 DF 도출
            # 공식: DF_n = (1 - R * Sum(DF_prev * dt)) / (1 + R * dt)
            df_n = (1.0 - par_rate * sum_val) / (1.0 + par_rate * dt)

            # 제로 금리 역산 (Continuous Compounding)
            zero_r = -np.log(df_n) / T_end

            times.append(T_end)
            discount_factors.append(df_n)

            self.tenors.append(T_end)
            self.zero_rates.append(zero_r)
            self.dfs.append(df_n)

        return self.tenors, self.zero_rates, self.dfs


# --- 실행 예제 ---
if __name__ == "__main__":
    # (만기 년수, 금리)
    market_quotes = [
        (0.25, 0.0350),  # CD 91일
        (0.50, 0.0355),
        (1.00, 0.0365),
        (2.00, 0.0375),
        (3.00, 0.0380),
        (5.00, 0.0390),
        (10.0, 0.0400)
    ]

    bootstrapper = SimpleBootstrap()
    t, z, d = bootstrapper.bootstrap(market_quotes)

    print(f"{'Maturity(Y)':<12} | {'Zero Rate(%)':<15} | {'Discount Factor':<15}")
    print("-" * 50)
    for i in range(len(t)):
        print(f"{t[i]:<12.2f} | {z[i] * 100:<15.4f} | {d[i]:<15.6f}")