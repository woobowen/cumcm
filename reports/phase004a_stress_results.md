# Phase 004A Stress Results

| Variant | Transformation | Final state | Selection / WAPE | STALE evidence | Result |
|---|---|---|---|---|---|
| A | file/row/column reorder; unrelated master field | READY_FOR_PAPER_HANDOFF | same decision; 0.31407446 | new input hashes, no old reuse | PASS |
| B | quantity represented in grams; scale 0.001 to kg; dates +365 days | READY_FOR_PAPER_HANDOFF | same decision; 0.31407446 | old-binding probe STALE | PASS |
| C | 0.1% row removal; price/cost missingness; loss source unavailable | READY_FOR_PAPER_HANDOFF | changed decision hash; 0.31413260 | old-binding probe STALE | PASS |

Stress A changed all workbook hashes but reproduced all three candidate scores and final metrics,
showing order invariance while maintaining new lineage. Stress B recorded the conversion and date
shift, reproduced kg-scale outputs exactly and propagated metadata mutation through experiment plan
and all manifests. Stress C retained 877,160 positive rows, reported 4,225 missing wholesale joins
and 877,160 missing loss rows, selected the same family but changed metrics and profit proxy; its
uncertainty and missing-source limitation remain in handoff.

These are semantics-preserving/degraded variants of one Development case. They are not independent
historical problems and do not prove generalization.
