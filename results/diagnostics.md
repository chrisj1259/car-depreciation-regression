## Train/test (80/20, seed 0)

| model        |   train_rmse_log |   test_rmse_log |   train_r2 |   test_r2 |
|:-------------|-----------------:|----------------:|-----------:|----------:|
| age only     |            0.665 |           0.669 |      0.422 |     0.419 |
| age + miles  |            0.653 |           0.658 |      0.444 |     0.439 |
| main model   |            0.569 |           0.573 |      0.577 |     0.574 |
| main + age^2 |            0.566 |           0.57  |      0.582 |     0.578 |

Test RMSE of 0.573 in log units means typical predictions are off by a factor of x1.77 (up or down). Brand, age, miles and body type explain about 57% of price variance; the rest is trim, condition and seller pricing.

## Diagnostics (full-data fit)

- Residual skew -1.65, excess kurtosis 10.04
- Breusch-Pagan p = 0 (heteroskedasticity is why we use HC3 SEs)
- VIF age 1.37, log_odo 1.37 (both well under 5: collinearity is mild)
- Residual SD by fitted-value quintile: [0.62, 0.54, 0.52, 0.52, 0.63]
- Mean residual by age (0-2, 3-10, 11-17, 18+): [-0.038, 0.026, -0.066, 0.082]

## Bay Area x age

Positive slope diff = Bay Area cars lose value more slowly.

| sample              |   bay_n |   bay_premium_log |   age_slope_diff |     se |      p |   pct_per_year |
|:--------------------|--------:|------------------:|-----------------:|-------:|-------:|---------------:|
| all rows            |    1681 |            0.0259 |           0.0053 | 0.0025 | 0.0325 |         0.5267 |
| n_regions == 1 only |    1551 |            0.0309 |           0.0053 | 0.0026 | 0.0375 |         0.5329 |
