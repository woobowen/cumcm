# Native Development science audit before v6 implementation

Actual native agent: `/root/rc8_fact_binding_audit`, read-only scientific reviewer.
Input HEAD started a42e2b545ffc74103076be70b89d9b7b40112025 and ended
565ab5d5b855b8d2b84ac4eaceae87223fed5f6b while the main agent committed concurrently.
This report preserves the returned tool observations and scientific conclusions. The agent did
not write files, execute an optimizer/model/helper, install packages, read fresh cases or answers,
or access benchmark-vault. Its raw temporary subprocess transcript was not retained as a replay
artifact; the following observations are native review evidence, not a substitute for captured Runs.

## Verified inputs and code

2021 archive SHA256 3391573f546fce4511e9a99c24c386e28203d8fee3d29bb2dccada5921cefe7b;
problem 4a592c20adad12d4f0678a783bfb47995bda03b1c7484adf254d96327f534056;
supplier workbook 1b93a7598b8f0489e3c054439967bca654a83654837908c833752617cf950e1b;
carrier workbook 29e1499b133aa88d765902081bfb827f78ffb4c091f5f75341fc37d844344685.

2022 archive c27eb1b665f070341e134f5dc13bb2af469230424ff2eedabf594eee708bfee4;
problem 573ee0f2865af13f8b2fbd12dab7f8efa68cf61ec6b8edf132a2120424480dbd;
workbook ffb82a8e209a005f26883e115de3ddea42ab6e0a34986d312a52a3cea6b1063c;
inner C archive cda2851e819c4b95a32209240ad047badb0479d91bae904bcfb3c42c1f4ef5c6.

Audited v5 2021 producer SHA256
1eeb338db3529d8d50f10269b0e089511505155d1e306516c159c720d9756cb8;
2022 producer f7c45d65c803f1c18db9f818d960acdb2fe15d39fcb016df6a32fe6385555f4a;
2021 helper f64bcb3942e10bbe804ae979e85f4f7d26ce8315eef650e0d9bedb397e606ef6.

## Actual independent calculations

The agent verified CaseConfig hashes before reading exact official PDFs/workbooks. `pdftotext`
help and both extractions exited 0. Independent statistics used its own workbook parser without
importing model or checker code. First attempt failed on trailing empty Excel rows; second failed
serializing NumPy integers; third exited 0. No optimizer or model fit was run.

2021 W001-W168: 402 suppliers (A146/B134/C122), 399 positive estimated delivered capacities.
Best carrier retention 0.9977284651162791. Top13 optimistic effective capacity
27580.851002167405, top14 28574.226696212954, versus weekly demand28200. Thus at least14
suppliers are required under that conditional model; this ignores the best carrier's capacity and
does NOT prove14 feasible. Historical168 used suppliers was not independently recomputed.

2022: 58 artifacts,69 sampled rows,67 valid samples,56 valid artifact groups (16 high-potassium,
40 lead-barium). Invalid samples15/17 sum to79.47/71.89. Fixed groups32train/12validation/12test.
All56-group CV includes the12 namedtest groups;280 predictions=56groups×5repeats, not280
independent samples. Only2 artifacts have both weathered/unweathered observations. Table3 has8
unknown samples, all valid. No unknown labels were accessed.

## Required scientific corrections

2021: purchase all actual supply at p*s, not p*order or p*s/delivery_ratio. Producer LP, validation
score and old helper shared the wrong semantics. Optimize supplier cardinality on one fixed
parameterization and save incumbent/bound/gap; distinguish candidate pool, used count and minimum.
Then use declared economic/loss objectives. Independently recurse24week inventory and transport
balances, including increased Q4 demand and Development supply fluctuations. Q3 requires its own
material-mix, cost/loss evidence. Missing absolute tariffs and true capacity remain assumptions.

2022: sparse contingency tables need bounded permutation checks; artifact-level dependence matters
for backcast and association. Two paired artifacts do not identify weathering causality. Full-group
CV's test_labels_accessed=false is false; internal namedtest groups are permanently Development.
`predict_unknown` DOES restrict fitting to train+validation: it does not share that bug. KNN votes
are not calibrated probabilities. Hellinger transformation ignores the zero-fraction parameter,
so its old fraction sweep applies no perturbation and cannot establish robustness. Add real
composition perturbations, subtype stability, unknown applicability-domain checks and artifact-level
association uncertainty. Undefined correlations must not be replaced by empirical zero.

## Limits and disposition

Both v5 ATTEMPT-013 selected output paths are absent on this host. The agent retained that missing
evidence finding and did not substitute older attempts. No v5 full-result replication or scientific
PASS is claimed. Main-agent v6 captured runs and independently checked results remain required.
Implementation workers are separate from this read-only reviewer; worker output is not acceptance.
