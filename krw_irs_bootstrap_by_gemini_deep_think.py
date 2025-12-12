import numpy as np
from scipy.interpolate import interp1d


class SimpleBootstrap:
    def __init__(self):
        # [수정 1] 초기화 시점에 t=0, df=1.0을 추가하여 보간 에러 방지
        self.times = [0.0]  # 시간축
        self.discount_factors = [1.0]  # 할인계수축 (t=0일 때 1.0)

        # 결과 저장용 리스트 (0.0 시점 제외하고 실제 만기만 저장)
        self.result_tenors = []
        self.result_zeros = []
        self.result_dfs = []

    def bootstrap(self, market_data):
        """
        :param market_data: list of tuples (Year, Rate)
        Sorted by year e.g. [(0.25, 0.035), (1.0, 0.036)...]
        """
        # 데이터 정렬
        data = sorted(market_data, key=lambda x: x[0])

        for T_end, par_rate in data:
            # 현금 흐름 주기 (KRW IRS 분기 지급 = 0.25년 가정)
            dt = 0.25

            # 0.25, 0.50, ... T_end 까지의 현금흐름 시점 생성
            # np.arange는 부동소수점 오차가 있을 수 있어 epsilon 추가
            cashflow_times = np.arange(dt, T_end + 0.001, dt)

            sum_val = 0.0

            # --- 보간 함수 생성 ---
            # [수정 2] self.times에는 이미 (0.0, 1.0)과 이전 계산된 점들이 들어있음
            # Log-Linear Interpolation: ln(DF)에 대해 선형 보간
            # 점이 2개 이상이므로 interp1d가 정상 작동함
            f_interp = interp1d(
                self.times,
                np.log(self.discount_factors),
                kind='linear',
                fill_value="extrapolate"
            )

            # 마지막 현금흐름(Tn)을 제외한 이전 현금흐름들의 가치 합산
            for t in cashflow_times[:-1]:
                # 보간된 DF 계산
                df_t = np.exp(f_interp(t))
                sum_val += df_t * dt

            # --- 마지막 시점(Tn)의 DF 도출 ---
            # 공식: DF_n = (1 - Rate * Sum(DF_prev * dt)) / (1 + Rate * dt)
            df_n = (1.0 - par_rate * sum_val) / (1.0 + par_rate * dt)

            # --- 제로 금리 역산 (Continuous Compounding) ---
            # ZeroRate = -ln(DF) / T
            zero_r = -np.log(df_n) / T_end

            # [수정 3] 다음 루프의 보간을 위해 리스트에 추가
            self.times.append(T_end)
            self.discount_factors.append(df_n)

            # 결과 저장 (사용자 출력용)
            self.result_tenors.append(T_end)
            self.result_zeros.append(zero_r)
            self.result_dfs.append(df_n)

        return self.result_tenors, self.result_zeros, self.result_dfs


# --- 실행 예제 ---
if __name__ == "__main__":
    # (만기 년수, 금리)
    market_quotes = [
        (0.25, 0.03),  # CD 91일
        (0.50, 0.03),
        (1.00, 0.03),
        (2.00, 0.03),
        (3.00, 0.03),
        (5.00, 0.03),
        (10.0, 0.03)
    ]

    bootstrapper = SimpleBootstrap()
    t, z, d = bootstrapper.bootstrap(market_quotes)

    print(f"{'Maturity(Y)':<12} | {'Zero Rate(%)':<15} | {'Discount Factor':<15}")
    print("-" * 50)
    for i in range(len(t)):
        print(f"{t[i]:<12.2f} | {z[i] * 100:<15.4f} | {d[i]:<15.6f}")