"""EDA on the cleaned table: what shape is the data before we model it?

Run:  python -m src.eda   (reads data/processed/clean.parquet, writes results/eda.md + figures/eda_*.png)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_parquet("data/processed/clean.parquet")
Path("figures").mkdir(exist_ok=True)
out = []

def section(title, table):
    out.append(f"## {title}\n\n{table.to_markdown()}\n")

section("Numeric summary", df[["price", "age", "odometer"]].describe().round(0))
section("Corr (log scale)", df[["log_price", "age", "log_odo"]].corr().round(2))
section("Brand: n, median price, median age",
        df.groupby("brand").agg(n=("price", "size"), median_price=("price", "median"), median_age=("age", "median"))
          .sort_values("n", ascending=False).round(0))
section("Median price by age", df.groupby("age")["price"].agg(["size", "median"]).round(0).head(26))
section("Share by region type", df.bay_area.value_counts(normalize=True).round(3).to_frame("share"))
section("Skew: raw vs log price", pd.DataFrame({"skew": [df.price.skew(), df.log_price.skew()]},
                                               index=["price", "log_price"]).round(2))
Path("results/eda.md").write_text("\n".join(out))

fig, ax = plt.subplots(1, 3, figsize=(15, 4))
df.price.hist(bins=60, ax=ax[0]); ax[0].set_title("Price (right-skewed)")
df.log_price.hist(bins=60, ax=ax[1]); ax[1].set_title("log(price) (roughly symmetric)")
s = df.sample(20_000, random_state=0)
ax[2].scatter(s.age, s.log_price, s=2, alpha=.2); ax[2].set_title("log(price) vs age"); ax[2].set_xlabel("age (yrs)")
fig.tight_layout(); fig.savefig("figures/eda_overview.png", dpi=120)

top = df.brand.value_counts().index[:8]
fig, ax = plt.subplots(figsize=(8, 5))
for b in top:
    m = df[df.brand == b].groupby("age").log_price.median()
    ax.plot(m.index[:20], m.values[:20], label=b)
ax.set_xlabel("age (yrs)"); ax.set_ylabel("median log(price)"); ax.legend(); ax.set_title("Depreciation curves, top 8 brands")
fig.tight_layout(); fig.savefig("figures/eda_brand_age.png", dpi=120)
print(Path("results/eda.md").read_text())
