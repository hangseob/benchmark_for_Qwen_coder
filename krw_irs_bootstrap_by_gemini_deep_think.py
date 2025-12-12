import numpy as np
from scipy.interpolate import interp1d


class SimpleBootstrap:
    def __init__(self):
        self.times = [0.0]
        self.discount_factors = [1.0]

        self.result_tenors = []
        self.result_market_rates = []
        self.result_zeros = []
        self.result_dfs = []

    def bootstrap(self, market_data):
        # 만기 순서대로 정렬
        data = sorted(market_data, key=lambda x: x[0])

        for T_end, par_rate in data:
            dt = 0.25
            cashflow_times = np.arange(dt, T_end + 0.001, dt)
            sum_val = 0.0

            # --- [핵심 수정 부분] ---
            # 보간을 위한 점이 1개(t=0) 밖에 없는 경우와 그 이상인 경우 분기 처리

            if len(self.times) < 2:
                # Case 1: 첫 번째 상품인데 만기가 길어서(예: 1년) 중간 이자(0.25년 등)가 있는 경우
                # 이전 커브 데이터가 전무하므로, 현재 상품의 금리(par_rate)를
                # 해당 구간의 "Flat Rate"로 가정하고 단순 할인합니다.
                def get_df_at(t):
                    # Simple Discounting: 1 / (1 + r * t)
                    return 1.0 / (1.0 + par_rate * t)
            else:
                # Case 2: 이미 계산된 포인트가 2개 이상이면 정상적으로 선형 보간 수행
                f_interp = interp1d(
                    self.times,
                    np.log(self.discount_factors),
                    kind='linear',
                    fill_value="extrapolate"
                )

                def get_df_at(t):
                    return np.exp(f_interp(t))

            # --- 중간 현금흐름 할인 합계 계산 ---
            for t in cashflow_times[:-1]:
                df_t = get_df_at(t)
                sum_val += df_t * dt

            # --- DF_n 도출 ---
            df_n = (1.0 - par_rate * sum_val) / (1.0 + par_rate * dt)

            # 제로 금리 역산
            zero_r = -np.log(df_n) / T_end

            # 리스트 업데이트
            self.times.append(T_end)
            self.discount_factors.append(df_n)

            self.result_tenors.append(T_end)
            self.result_market_rates.append(par_rate)
            self.result_zeros.append(zero_r)
            self.result_dfs.append(df_n)

        return self.result_tenors, self.result_market_rates, self.result_zeros, self.result_dfs


if __name__ == "__main__":
    # 요청하신 데이터
    market_quotes = [
        (1.00, 0.03),
        (5.00, 0.04),
        (10.0, 0.05)
    ]

    bootstrapper = SimpleBootstrap()
    tenors, market_rates, zeros, dfs = bootstrapper.bootstrap(market_quotes)

    header = f"{'Maturity(Y)':<12} | {'Mkt Rate(%)':<12} | {'Zero Rate(%)':<12} | {'Discount Factor':<15}"
    print(header)
    print("-" * len(header))

    for i in range(len(tenors)):
        print(f"{tenors[i]:<12.2f} | {market_rates[i] * 100:<12.2f} | {zeros[i] * 100:<12.4f} | {dfs[i]:<15.6f}")