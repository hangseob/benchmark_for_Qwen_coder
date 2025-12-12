import math


class KRWIRSCurve:
    def __init__(self, irs_quotes):
        self.irs_quotes = dict(sorted(irs_quotes.items()))
        self.discount_factors = {}
        self.zero_rates = {}

    def bootstrap(self):
        known_tenors = []

        for tenor, fixed_rate in self.irs_quotes.items():
            if tenor == 1:
                df = 1.0 / (1.0 + fixed_rate)
            else:
                fixed_leg_pv = 0.0

                # ✅ 이미 bootstrap된 지급일만 사용
                for t in known_tenors:
                    fixed_leg_pv += fixed_rate * self.discount_factors[t]

                # par swap condition
                df = (1.0 - fixed_leg_pv) / (1.0 + fixed_rate)

            self.discount_factors[tenor] = df
            self.zero_rates[tenor] = -math.log(df) / tenor
            known_tenors.append(tenor)

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

    irs_quotes = {
        1: 0.03,
        2: 0.03,
        3: 0.03,
        5: 0.03,
        7: 0.03,
        10: 0.03
    }

    curve = KRWIRSCurve(irs_quotes)
    curve.bootstrap()
    curve.summary()
