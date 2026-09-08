# 2021 C Development: baseline and feasibility audit

This is a read-only audit of
`CUMCM-2021-C-DEVELOPMENT-RC7-REGRESSION-ATTEMPT-002`. It uses the two
registered official input workbooks and does not inspect answer material or
the sealed W217--W240 test period.

## Data and time boundary

- Supplier order/supply matrices are 402 x 240; carrier loss is 8 x 240.
- The supplier material counts are A=146, B=134, C=122.
- The registered split is W001--W168 training and W169--W216 Development
  validation; W217--W240 remains unaccessed.
- Training has 25,409 nonzero order cells, 18,386 nonzero supply cells, and
  1,030 positive carrier-loss observations. Validation has 7,384 nonzero
  order cells, 5,399 nonzero supply cells, and 286 positive loss observations.

## Candidate comparison and rolling-window check

On the registered 48-week window, the candidates score:

| candidate | penalized score | mean shortage | max shortage | cardinality status |
| --- | ---: | ---: | ---: | --- |
| `BASELINE_MEAN_GREEDY` | 2.137602596 | 0.008155889 | 0.098333731 | greedy upper bound |
| `ROBUST_QUANTILE_LEXICOGRAPHIC` | 2.435657334 | 0.010030585 | 0.100407808 | exact MILP |
| `SCENARIO_CVAR_PORTFOLIO` | 7.662617820 | 0.022049162 | 0.310602281 | exact MILP |

The same baseline wins the two additional read-only rolling windows
W001--W120/W121--W168 and W001--W144/W145--W192, with scores 2.081740835 and
1.707991518 versus 2.188576786/1.988188325 for the robust quantile candidate.
This supports selection under this Development metric; it does not establish
global economic optimality.

## Independent recomputation

A separate workbook parser and balance implementation, without importing
`c2021_feasibility`, reconstructed the selected baseline Q2 plan. It reproduced
the reported validation score to absolute difference `3.72e-10` and the
forecast effective receipt to `3.47e-7 m3`.

The forecast receipt is 28199.999990653 m3 against the 28200 m3 target. The
existing verifier accepts this because its explicit demand tolerance is 0.0282
m3; this is a numerical-tolerance pass, not exact equality.

The declared Q2 selected supplier set contains 399 suppliers because the
baseline uses `GREEDY_ALL_POSITIVE_CAPACITY_UPPER_BOUND`; the emitted weekly
plan actually transports from 168 suppliers. Therefore the 399 number must be
reported as a candidate pool/upper bound, not as a proven minimum supplier
count. The current plan has no global-optimality certificate.

## Scientific conclusion

`BASELINE_MEAN_GREEDY` is a reproducible Development winner for the registered
penalized validation metric and its emitted plans pass independent constraint
recalculation within declared numerical tolerance. Its future-behavior,
tariff, inventory, supplier-splitting, and global-optimality assumptions remain
conditional. It is not an independent Validation result.
