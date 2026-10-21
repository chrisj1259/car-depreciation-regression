"""Self-check for the cleaning rules. Run: python test_clean.py"""
import pandas as pd

import src.clean as c

c.MIN_BRAND_N = 2  # tiny fixture; keep the brand rule testable

good = dict(region="SF bay area", price=15000, year=2015, manufacturer="toyota", model="camry",
            odometer=80000, title_status="clean", VIN=None, type="sedan", state="ca",
            posting_date="2021-04-10")
rows = [
    good,
    {**good, "price": 16000, "model": " Camry ", "VIN": "abc", "posting_date": "2021-04-01"},
    {**good, "price": 16500, "VIN": "ABC", "posting_date": "2021-04-20"},  # duplicate VIN, later -> dropped
    {**good, "odometer": 80001},
    {**good, "price": 0},                                         # placeholder price
    {**good, "year": 1970},                                       # collector
    {**good, "odometer": 999999},                                 # placeholder miles
    {**good, "year": 2020, "odometer": 120000},                   # 120k miles in 1 year
    {**good, "title_status": "salvage", "odometer": 70000},
    {**good, "region": "chico"},                                  # same car, reposted elsewhere in CA
    {**good, "manufacturer": "ferrari"},                          # rare brand
    {**good, "model": None},                                      # missing core field
    {**good, "region": "fresno / madera", "type": None, "odometer": 90000},
]
df, log = c.clean(pd.DataFrame(rows))
dropped = dict(zip(log.rule, log.dropped))

assert len(df) == 4, df
assert dropped["duplicate VIN"] == 1 and dropped["duplicate listing"] == 1
assert all(dropped[r] == 1 for r in ["price out of range", "year out of range", "odometer out of range",
                                      "implausible miles/year", "bad title", "rare brand", "missing core field"])
assert log.remaining.iloc[-1] == len(df)
assert df.loc[df.VIN == "ABC", "price"].item() == 16000  # earliest posting kept
assert set(df.model) == {"camry"} and df.age.eq(6).all()
assert df.bay_area.sum() == 3 and (df.type == "unknown").sum() == 1
assert df.loc[df.VIN == "ABC", "n_regions"].item() == 1 and df.n_regions.eq(1).all()
print("test_clean ok")
