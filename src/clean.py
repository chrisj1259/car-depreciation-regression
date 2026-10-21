"""Clean the Craigslist vehicles dump into a modeling table.

Every rule is applied in order and logs how many rows it dropped, so the
README table is generated, not hand-typed.

Run:  python -m src.clean   (reads data/raw/vehicles.csv, writes data/processed/clean.parquet)
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw/vehicles.csv")
OUT = Path("data/processed/clean.parquet")
LOG = Path("results/cleaning_log.md")

COLS = ["id", "region", "price", "year", "manufacturer", "model", "odometer",
        "title_status", "VIN", "type", "state", "posting_date"]

SCRAPE_YEAR = 2021  # all listings posted Apr 4 - May 4, 2021
MIN_PRICE, MAX_PRICE = 500, 150_000
MIN_YEAR, MAX_YEAR = 1995, 2022  # 2022 model years were already on sale in spring 2021
MIN_ODO, MAX_ODO = 100, 400_000
MAX_MILES_PER_YEAR = 50_000
MIN_BRAND_N = 1_000
BAY_AREA_REGION = "SF bay area"


def _dupe_key(df):
    return df.duplicated(["price", "year", "manufacturer", "model", "odometer", "state"])


# (name, why, function returning a boolean mask of rows to DROP)
RULES = [
    ("missing core field", "price, year, odometer, brand or model is blank",
     lambda d: d[["price", "year", "odometer", "manufacturer", "model"]].isna().any(axis=1)),
    ("duplicate VIN", "same car reposted; keep the earliest posting",
     lambda d: d["VIN"].notna() & d.duplicated("VIN")),
    ("duplicate listing", "same price, year, brand, model, miles and state (catches reposts without a VIN)",
     _dupe_key),
    ("price out of range", f"under ${MIN_PRICE} ($0/$1 placeholders, 'call for price') or over ${MAX_PRICE:,} (typos like $3.7B)",
     lambda d: ~d["price"].between(MIN_PRICE, MAX_PRICE)),
    ("year out of range", f"model year before {MIN_YEAR} (collector cars price differently) or after {MAX_YEAR}",
     lambda d: ~d["year"].between(MIN_YEAR, MAX_YEAR)),
    ("odometer out of range", f"under {MIN_ODO} or over {MAX_ODO:,} miles (0, 1, 999999 placeholders)",
     lambda d: ~d["odometer"].between(MIN_ODO, MAX_ODO)),
    ("implausible miles/year", f"over {MAX_MILES_PER_YEAR:,} miles per year of age (likely an extra digit)",
     lambda d: d["odometer"] / np.maximum(SCRAPE_YEAR - d["year"], 1) > MAX_MILES_PER_YEAR),
    ("bad title", "salvage, rebuilt, parts-only, missing or blank title; damaged cars are a different market",
     lambda d: ~d["title_status"].isin(["clean", "lien"])),
    ("rare brand", f"brand has fewer than {MIN_BRAND_N:,} clean listings, too few for its own depreciation slope",
     lambda d: d.groupby("brand")["brand"].transform("size") < MIN_BRAND_N),
]


def prepare(df):
    """Normalize text fields before the rules run."""
    df = df.sort_values("posting_date").copy()
    df["brand"] = df["manufacturer"].replace({"land rover": "rover"})  # same make, two spellings
    df["model"] = df["model"].str.lower().str.strip()
    df["VIN"] = df["VIN"].str.upper().str.strip()
    # National dealers post one car to up to ~250 regions; its kept region is then arbitrary.
    df["n_regions"] = df.groupby("VIN")["region"].transform("nunique").fillna(1).astype(int)
    return df


def apply_rules(df):
    log = [("raw listings", "", 0, len(df))]
    for name, why, rule in RULES:
        drop = rule(df).to_numpy()
        df = df[~drop]
        log.append((name, why, int(drop.sum()), len(df)))
    return df, pd.DataFrame(log, columns=["rule", "why", "dropped", "remaining"])


def add_features(df):
    df = df.copy()
    df["age"] = (SCRAPE_YEAR - df["year"]).clip(lower=0).astype(int)
    df["log_price"] = np.log(df["price"])
    df["log_odo"] = np.log(df["odometer"])
    df["type"] = df["type"].fillna("unknown")  # 22% blank; dropping them would cost too much data
    df["bay_area"] = (df["region"] == BAY_AREA_REGION).astype(int)
    return df.reset_index(drop=True)


def clean(raw):
    df, log = apply_rules(prepare(raw))
    return add_features(df), log


if __name__ == "__main__":
    raw = pd.read_csv(RAW, usecols=COLS)
    df, log = clean(raw)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    LOG.write_text(log.to_markdown(index=False) + "\n")
    print(log.to_string(index=False))
    print(f"\nkept {len(df):,} of {len(raw):,} ({len(df) / len(raw):.1%}); Bay Area rows: {df.bay_area.sum():,}")
