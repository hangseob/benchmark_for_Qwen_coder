import math


class KRWIRSCurve:
    def __init__(self, irs_quotes):
        self.irs_quotes = dict(sorted(irs_quotes.items()))
        self.discount_factors = {}
        self.zero_rates = {}

    def _interpolate_df(self, t):
        tenors = sorted(self.discount_factors.keys())

        if t in self.discount_factors:
            return self.discount_factors[t]

        for i in range(len(tenors) - 1):
            t1, t2 = tenors[i], tenors[i + 1]
            if t1 < t < t2:
                df1 = self.discount_factors[t1]
                df2 = self.discount_factors[t2]

                w = (t - t1) / (t2 - t1)
                log_df = math.log(df1) * (1 - w) + math.log(df2) * w
                return math.exp(log_df)

        raise ValueError(f"Cannot interpolate DF for t={t}")

    def bootstrap(self):
        for tenor, fixed_rate in self.irs_quotes.items():
            if tenor == 1:
                df = 1.0 / (1.0 + fixed_rate)
            else:
                fixed_leg_pv = 0.0
                for t in range(1, tenor):
                    df_t = self._interpolate_df(t)
                    fixed_leg_pv += fixed_rate * df_t

                df = (1.0 - fixed_leg_pv) / (1.0 + fixed_rate)

            self.discount_factors[tenor] = df
            self.zero_rates[tenor] = -math.log(df) / tenor

    def summary(self):
        print("Tenor | DF        | Zero Rate (cont)")
        print("-----------------------------------")
        for t in self.discount_factors:
            print(
                f"{t:>5}Y | "
                f"{self.discount_factors[t]:.6f} | "
                f"{self.zero_rates[t]*100:.4f}%"
            )


if __name__ == "__main__":

    # ✅ 반드시 정의되어야 함
    irs_quotes = {
        1: 0.0320,
        2: 0.0335,
        3: 0.0350,
        5: 0.0365,
        7: 0.0375,
        10: 0.0380
    }

    curve = KRWIRSCurve(irs_quotes)
    curve.bootstrap()
    curve.summary()
