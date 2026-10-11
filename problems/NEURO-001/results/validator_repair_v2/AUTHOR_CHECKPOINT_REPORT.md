# NEURO-001 validator repair: finite author tests passed; current independent review pending

## Finding

The separately versioned strict validator passed all 53 frozen author checks, including rejection of all 21 deliberately corrupted mathematical reports. A fresh run of the unchanged original baseline reproduced all 60 seeded histograms and every JSON field other than the three explicitly excluded runtime/platform paths. A historical, differently implemented ordered-sequence oracle also reproduced all 60 histograms; its largest entropy discrepancy was 1.1102230246251565e-16.

This is a finite artifact-integrity and reproducibility result. **It is not a new neuroscience discovery and does not complete NEURO-001.** No subjects, neural observations, clinical records, intervention, trained model or new synthetic configuration was added. The scientific parent remains OPEN.

Current status is **PASS_FINITE_AUTHOR_TESTS / INDEPENDENT_REVIEW_PENDING**. The historical oracle was authored independently in an earlier session, but executing that existing source now is historical cross-implementation replay, not a freshly authored independent test of the repaired validator.

## Original failures remain preserved

The original validator still accepts all six retained semantic corruptions: a histogram transfer preserving the total, changed diagnostic EIG, changed outside-family C confidence, NaN ordinary EIG, changed selected input and a duplicated seed. Its exact-evaluation entry still accepts a truth probability outside [0,1]. The original total-changing histogram control continues to reject.

The new validator rejects those six corruptions and the original malformed-histogram case, plus 14 additional schema/type/semantic corruptions. It rejects invalid probability input in each of three argument positions, unknown truth, unsupported candidate posterior endpoints, nonfinite JSON literals and duplicate JSON keys.

All 42 tracked files from source commit `65dbef8313d4c9170f0cdcf119901eeb76bb0434` remain byte-identical. The original frozen round's **FAILED/INCOMPLETE** verdict is unchanged. Author flags in old reports are not release or scientific approval.

## What ran

- 20 invalid probability/label/support cases rejected, five valid exact-input fixtures accepted.
- Four strict-JSON rejection fixtures passed.
- Original mathematical payload accepted; all 21 report mutations rejected.
- Fresh baseline matched exactly outside `/runtime_seconds`, `/environment/python`, `/environment/platform`; its mathematical payload passed the new validator.
- Total: 53/53 author checks.
- Historical oracle: nine identical-model controls, 15 invalid-input controls, all 60 original seeded histograms; reused comparison script reconfirmed all seven old report mutation outcomes.
- Three full seeded replay passes used: new-validator expectation, original baseline, historical oracle. At most one more is reserved for the current independent reviewer.

Author harness elapsed 0.364 seconds; parent plus baseline-child CPU was 0.415 seconds. Recorded parent peak RSS was 13,952 KiB, child 13,824 KiB. The historical oracle elapsed about 0.297 seconds. Budget was $0, one CPU process at a time, 4 GiB maximum, 30 CPU minutes, and a full-round wall deadline of 2026-10-11 04:43:46 UTC. No paid resources, extra data or external publication after the scope claim.

## Exact mathematical values reproduced

Ordinary recovery = 1/2 and EIG = 0. Diagnostic recovery = 3807/4096 = 0.929443359375 and EIG = 0.7710929067550158 bits. Under out-of-candidate-family Bernoulli(1/2) truth C, at least 95% closed-family confidence occurs with probability 37/128 = 0.2890625. The last result remains a warning against interpreting closed-family confidence as evidence either candidate is true.

These numbers were already present in the earlier baseline; they are reproduction, not new discovery. Maximum pooled Monte Carlo discrepancy from the exact target remains 0.000837499999999991.

## Provenance and chronology

The 2026-10-10 preparation expired without execution. A new round started at 2026-10-11T04:13:46.153905+00:00. Repository main and source PR heads were rechecked unchanged; fresh four-category source searches and method/documentation reads followed. The new public scope claim was accepted and read back before admission and computation:

https://github.com/lijiabao1998/FrontierNeuroscience/pull/4#issuecomment-6105335060

The prior independent static review is retained. Only new round identity, paths and budget times differ from the previously reviewed implementation; strict validator and mutation manifest hashes are unchanged. The new code/protocol freeze was recorded before the first test. During setup, directly embedding API JSON into Python produced a NameError on a JSON boolean. This occurred before code freeze or computation; the complete setup failure is recorded, and safe JSON parsing completed the metadata preparation. No failed scientific result was omitted.

Frozen protocol SHA256: `97ccf1310b31de7cac5b253a58e0a267c7ec97d077fdb430d1f9488082311435`.
Strict validator SHA256: `a7e69413be49fcf29d214422bd47cf115a498e4efdee2781b16dc66ac09c9ea3`.
Runner SHA256: `611dd250b2c319906e0b8397a1e3bc0b8078e42f8b282a9ba42155f6d321dfc1`.
Mutations SHA256: `46f710a00ac514495797076212f503c2b170e3c0c7ab0826a5ad4435aff2d7bd`.

## Reproduce and review

From a fresh copy of this repository, inspect the frozen protocol, `runs/20261011T041346153905Z-gpt-NEURO-001/code-freeze.json`, raw execution records and `source-integrity.json` first. The one-shot author harness intentionally refuses to overwrite an existing result directory and enforces its absolute round deadline. Do not bypass those protections; a later execution requires a new admitted round.

A simple read-only validation of the saved original mathematical payload is:

    PYTHONDONTWRITEBYTECODE=1 python problems/NEURO-001/experiments/validator_repair_v2/strict_validator.py problems/NEURO-001/results/synthetic_disagreement/results.json

That command performs one seeded expectation replay in a new process and therefore counts toward the four-pass round budget if used before this round closes. Historical replay commands and exact output path are preserved in `historical-oracle.execution.json`. The separate current reviewer should derive exact expectations without importing the new validator for mathematical truth, test additional unseen corruptions, and report scope, failures, resources and hashes. A successful finite review would still not establish universal validator security or neural validity.
