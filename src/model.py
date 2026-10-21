"""OLS on log(price): brand x age, plus log odometer and body type, HC3 robust SEs.

Run:  python -m src.model   (writes results/ols_summary.txt, results/brand_depreciation.md)
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

df = pd.read_parquet("data/processed/clean.parquet")
FORMULA = "log_price ~ C(brand, Treatment('toyota')) * age + log_odo + C(type)"
fit = smf.ols(FORMULA, df).fit(cov_type="HC3")

# Per-brand age slope = main age effect + that brand's interaction; t-test it so the CI is correct.
names = list(fit.params.index)
rows = []
for b in sorted(df.brand.unique()):
    L = np.zeros(len(names)); L[names.index("age")] = 1
    key = f"C(brand, Treatment('toyota'))[T.{b}]:age"
    if key in names: L[names.index(key)] = 1
    t = fit.t_test(L)
    lo, hi = t.conf_int()[0]
    rows.append((b, 1 - np.exp(t.effect[0]), 1 - np.exp(hi), 1 - np.exp(lo)))  # % value lost per year of age
out = pd.DataFrame(rows, columns=["brand", "annual_loss", "ci_low", "ci_high"]).sort_values("annual_loss")

import pathlib
pathlib.Path("results/ols_summary.txt").write_text(str(fit.summary()))
out.to_csv("results/brand_depreciation.csv", index=False)
pathlib.Path("results/brand_depreciation.md").write_text(out.round(3).to_markdown(index=False) + "\n")
print(f"n={int(fit.nobs):,}  R2={fit.rsquared:.3f}  adjR2={fit.rsquared_adj:.3f}")
print(f"log_odo coef={fit.params['log_odo']:.3f}  (10% more miles -> {100*(1.1**fit.params['log_odo']-1):.1f}% price)")
print(out.round(3).to_string(index=False))
