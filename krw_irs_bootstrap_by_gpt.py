# by gpt 5.2 fast mode
# prompt: KRW IRS bootstrap module을 python으로 작성해줘

import math

class KRWIRSCurve:
    def __init__(self, irs_quotes):
        """
        irs_quotes: dict {tenor_years: fixed_rate}
        """
        self.irs_quotes = dict(sorted(irs_quotes.items()))
        self.discount_factors = {}
        self.zero_rates = {}

    def bootstrap(self):
        """
        Bootstrap discount factors from par IRS rates
        """
        for tenor, fixed_rate in self.irs_quotes.items():
            if tenor == 1:
                # 단일 지급
                df = 1.0 / (1.0 + fixed_rate)
            else:
                fixed_leg_pv = 0.0
                for t in range(1, tenor):
                    fixed_leg_pv += fixed_rate * self.discount_factors[t]

                # Par swap condition
                df = (1.0 - fixed_leg_pv) / (1.0 + fixed_rate)

            self.discount_factors[tenor] = df
            self.zero_rates[tenor] = -math.log(df) / tenor

    def get_discount_factor(self, t):
        return self.discount_factors.get(t)

    def get_zero_rate(self, t):
        return self.zero_rates.get(t)

    def summary(self):
        print("Tenor | DF       | Zero Rate (cont)")
        print("----------------------------------")
        for t in self.discount_factors:
            print(
                f"{t:>5}Y | "
                f"{self.discount_factors[t]:.6f} | "
                f"{self.zero_rates[t]*100:.4f}%"
            )

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
