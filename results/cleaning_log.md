| rule                   | why                                                                                       |   dropped |   remaining |
|:-----------------------|:------------------------------------------------------------------------------------------|----------:|------------:|
| raw listings           |                                                                                           |         0 |      426880 |
| missing core field     | price, year, odometer, brand or model is blank                                            |     26997 |      399883 |
| duplicate VIN          | same car reposted; keep the earliest posting                                              |    140832 |      259051 |
| duplicate listing      | same price, year, brand, model, miles and state (catches reposts without a VIN)           |     29639 |      229412 |
| price out of range     | under $500 ($0/$1 placeholders, 'call for price') or over $150,000 (typos like $3.7B)     |     19769 |      209643 |
| year out of range      | model year before 1995 (collector cars price differently) or after 2022                   |     10548 |      199095 |
| odometer out of range  | under 100 or over 400,000 miles (0, 1, 999999 placeholders)                               |      2388 |      196707 |
| implausible miles/year | over 50,000 miles per year of age (likely an extra digit)                                 |       289 |      196418 |
| bad title              | salvage, rebuilt, parts-only, missing or blank title; damaged cars are a different market |     10840 |      185578 |
| rare brand             | brand has fewer than 1,000 clean listings, too few for its own depreciation slope         |      4296 |      181282 |
