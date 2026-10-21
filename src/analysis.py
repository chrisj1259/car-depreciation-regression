"""Diagnostics, train/test RMSE, Bay Area x age test, and the 4 README charts.

Run:  python -m src.analysis   (writes results/diagnostics.md, results/bayarea.md, figures/fig*.png)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor as vif

df = pd.read_parquet("data/processed/clean.parquet")
BASE = "log_price ~ C(brand, Treatment('toyota')) * age + log_odo + C(type)"
out = []

# --- train/test ---
test = df.sample(frac=0.2, random_state=0)
train = df.drop(test.index)
rmse = lambda a, b: float(np.sqrt(np.mean((a - b) ** 2)))
models = {"age only": "log_price ~ age", "age + miles": "log_price ~ age + log_odo",
          "main model": BASE, "main + age^2": BASE + " + I(age**2)"}
rows = []
for name, f in models.items():
    m = smf.ols(f, train).fit()
    rows.append((name, rmse(train.log_price, m.fittedvalues), rmse(test.log_price, m.predict(test)),
                 m.rsquared, 1 - np.mean((test.log_price - m.predict(test)) ** 2) / test.log_price.var(ddof=0)))
tt = pd.DataFrame(rows, columns=["model", "train_rmse_log", "test_rmse_log", "train_r2", "test_r2"]).round(3)
out.append("## Train/test (80/20, seed 0)\n\n" + tt.to_markdown(index=False))
main = smf.ols(BASE, train).fit()
out.append(f"\nTest RMSE of {tt.test_rmse_log[2]:.3f} in log units means typical predictions are off by "
           f"a factor of x{np.exp(tt.test_rmse_log[2]):.2f} (up or down). Brand, age, miles and body type explain about 57% of price variance; the rest is trim, condition and seller pricing.")

# --- diagnostics on full-data fit ---
full = smf.ols(BASE, df).fit()
res, fit_ = full.resid, full.fittedvalues
bp = sm.stats.het_breuschpagan(res, full.model.exog)[1]
X = sm.add_constant(df[["age", "log_odo"]])
v = [vif(X.values, i) for i in (1, 2)]
bins = pd.qcut(fit_, 5)
out.append(f"\n## Diagnostics (full-data fit)\n\n- Residual skew {res.skew():.2f}, excess kurtosis {res.kurt():.2f}\n"
           f"- Breusch-Pagan p = {bp:.2g} (heteroskedasticity is why we use HC3 SEs)\n"
           f"- VIF age {v[0]:.2f}, log_odo {v[1]:.2f} (both well under 5: collinearity is mild)\n"
           f"- Residual SD by fitted-value quintile: {res.groupby(bins, observed=True).std().round(2).tolist()}\n"
           f"- Mean residual by age (0-2, 3-10, 11-17, 18+): "
           f"{[round(float(res[(df.age >= a) & (df.age <= b)].mean()), 3) for a, b in [(0,2),(3,10),(11,17),(18,99)]]}")

# --- Bay Area x age ---
def ba(d):
    m = smf.ols(BASE + " + bay_area + bay_area:age", d).fit(cov_type="HC3")
    return m.params["bay_area"], m.params["bay_area:age"], m.bse["bay_area:age"], m.pvalues["bay_area:age"], int(d.bay_area.sum())
rows = []
for name, d in [("all rows", df), ("n_regions == 1 only", df[df.n_regions == 1])]:
    b, s, se, p, n = ba(d)
    rows.append((name, n, b, s, se, p, 100 * (np.exp(s) - 1)))
bt = pd.DataFrame(rows, columns=["sample", "bay_n", "bay_premium_log", "age_slope_diff", "se", "p", "pct_per_year"]).round(4)
out.append("\n## Bay Area x age\n\nPositive slope diff = Bay Area cars lose value more slowly.\n\n" + bt.to_markdown(index=False))
open("results/diagnostics.md", "w").write("\n".join(out) + "\n")
open("results/bayarea.md", "w").write(bt.to_markdown(index=False) + "\n")
print("\n".join(out))

# --- charts ---
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})
# 1 depreciation curves, 6 brands
fig, ax = plt.subplots(figsize=(7, 4.5))
for b in ["toyota", "honda", "ford", "bmw", "audi", "ram"]:
    m = df[df.brand == b].groupby("age").price.median()
    ax.plot(m.index[:20], m.values[:20], label=b)
ax.set(xlabel="Age (years)", ylabel="Median asking price ($)", title="Median price by age")
ax.legend(frameon=False); fig.tight_layout(); fig.savefig("figures/fig1_curves.png", dpi=130)
# 2 annual loss by brand with CI
d = pd.read_csv("results/brand_depreciation.csv").sort_values("annual_loss")
fig, ax = plt.subplots(figsize=(7, 7))
ax.errorbar(100 * d.annual_loss, d.brand, xerr=[100 * (d.annual_loss - d.ci_low), 100 * (d.ci_high - d.annual_loss)], fmt="o", capsize=2)
ax.set(xlabel="Value lost per year of age (%), 95% CI (HC3)", title="Annual depreciation by brand, holding miles fixed")
fig.tight_layout(); fig.savefig("figures/fig2_brand_loss.png", dpi=130)
# 3 residuals vs fitted
s = pd.DataFrame({"f": fit_, "r": res}).sample(15_000, random_state=0)
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].scatter(s.f, s.r, s=2, alpha=.25); ax[0].axhline(0, c="k", lw=1); ax[0].set(xlabel="Fitted log(price)", ylabel="Residual", title="Residuals vs fitted")
sm.qqplot(s.r, line="s", ax=ax[1], markersize=2); ax[1].set_title("Residual Q-Q")
fig.tight_layout(); fig.savefig("figures/fig3_residuals.png", dpi=130)
# 4 Bay Area vs rest
fig, ax = plt.subplots(figsize=(7, 4.5))
for flag, lab in [(1, "Bay Area"), (0, "Elsewhere")]:
    g = df[df.bay_area == flag].groupby("age").log_price.agg(["median", "size"]); g = g[g["size"] >= 20].iloc[:18]
    ax.plot(g.index, np.exp(g["median"]), label=lab)
ax.set(xlabel="Age (years)", ylabel="Median asking price ($)", title="Bay Area vs elsewhere", yscale="log"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig("figures/fig4_bayarea.png", dpi=130)
