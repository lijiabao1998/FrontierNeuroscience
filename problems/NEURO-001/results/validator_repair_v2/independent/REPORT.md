# NEURO-001 v2: independent finite-scope validator audit

## Verdict

**PASS_FINITE_INDEPENDENT_REVIEW** for the frozen artifact-integrity repair, completed 2026-10-11 at 04:23:25 UTC. All 82 recorded checks passed. This is a repair/reproduction result, not a neuroscience discovery. The original attempt remains **FAILED/INCOMPLETE**, and parent problem NEURO-001 remains **OPEN**.

The verdict is deliberately bounded: exact targets and the declared finite corruption suite, supplemented by eight independently designed report corruptions, were checked. It is not a proof of universal validator security, general mathematical correctness, neural validity, or parent-problem completion.

## What was verified

- Protocol SHA256: `97ccf1310b31de7cac5b253a58e0a267c7ec97d077fdb430d1f9488082311435`.
- All four code-freeze hashes matched. The three original input hashes matched the protocol.
- Every one of 78 existing non-Git files in the candidate directory was hashed before and after. No file changed or was added during the audit. Author code, original results, failed-history reports, repaired-validator author results, and author replay were left untouched.
- Pinned original report and preserved author baseline replay both passed the unmodified validator.
- Every one of the 21 frozen report corruptions was independently reconstructed and rejected by the actual frozen validator, including the seven historical report cases. The original six semantic acceptance failures and invalid-truth-probability failure remain in historical evidence.
- All eight newly designed corrupt reports were rejected:
  1. Shift pooled estimate and exact target together while retaining their difference.
  2. Substitute a numerically equivalent, noncanonical rational string.
  3. Replace a histogram integer with an equal-valued float.
  4. Corrupt equal-prior recovery alone.
  5. Transfer one histogram count and coherently recompute its per-seed metrics and affected pooled summaries.
  6. Invent a recovery value for out-of-family truth C, where null is required.
  7. Add an unrecognized top-level scientific claim.
  8. Put an exponent-overflow JSON number in a mathematical field.
- Six parser rejection fixtures covered nested NaN, positive Infinity in metadata, negative Infinity in an array, duplicate top-level keys, nested duplicates, and duplicate keys made equal by JSON escaping.
- Twenty direct invalid guarded-input fixtures were rejected, including arbitrarily close rational excursions outside [0,1], each nonfinite type and False in all three probability positions, unknown truth, and unsupported endpoint candidate support. Six new valid off-grid/boundary fixtures matched independently computed exact expectations.

## Independent mathematical evidence

The new reviewer oracle enumerates all 256 ordered binary-response sequences for each eight-response case. It multiplies rational response probabilities directly, forms exact rational posteriors, and accumulates recovery, confidence, count masses, and posterior means. It does not call the candidate's mathematical functions, the baseline, or the historical oracle for its expected values.

For information gain, it uses `1 - E[H(P(A|Y))]` and 70-digit Decimal logarithms, separate from the candidate's binomial-count likelihood-ratio sum. These logarithms are high-precision numerical calculations, not formally certified interval bounds. Agreement with the candidate and both saved baseline reports was within **1.1102230246251565e-16**, below the frozen **1e-12** tolerance.

Key independent values:

- Selected x: **-1**; ordinary x: **1/2**.
- Ordinary recovery: **1/2**; ordinary EIG8: **0**.
- Diagnostic A/B recovery: **3807/4096 = 0.929443359375**.
- Diagnostic EIG8: approximately **0.7710929067550159034 bits**.
- Diagnostic A/B high-confidence probability: **22373/32768 = 0.682769775390625**.
- Diagnostic posterior mean P(A|Y): **17810681/19640066** under A; **1829385/19640066** under B; **1/2** under C.
- Diagnostic outside-family C high-confidence probability: **37/128 = 0.2890625**.

For the diagnostic design, the posterior odds A:B after k positive responses are `3^(8-2k)`. Thus MAP selects A for k<4, B for k>4, and gives half credit at k=4. Confidence at least 0.95 holds at k<=2 or k>=6. Under C, k is binomial(8, 1/2), so this event has exact probability `2*(1+8+28)/256 = 37/128`. This is closed-set model confidence; C is not a candidate. It does not demonstrate calibration when the candidate family is wrong.

MC recovery, confidence, pooled means, and absolute errors were independently reconstructed from saved counts and independently derived decision/posterior rules. All 60 histogram arrays matched between the real candidate replay, pinned original, and author replay.

## Independence and budget

The reviewer wrote a fresh oracle and fresh held-out mutations in a separate agent session. The reviewer had already read frozen candidate code and historical outputs before authoring the oracle; this is **independent implementation, not blinded validation**.

Only one additional full seeded pass was performed. It called the real, unmodified candidate `expected_payload()` and retained its actual cache throughout all report tests. There was no replacement or injected expectation cache. Therefore this current seeded pass is a candidate replay, not a newly independently authored RNG implementation. The separate, earlier historical cross-implementation replay remains distinct evidence; it was not rerun here.

The pre-execution reviewer plan and script hash were frozen at 04:23:18 UTC. Execution started and ended within the existing round deadline of 04:43:46.153905 UTC.

- Report-validation calls: **32**
- Strict-parser calls: **7**
- Real seeded-expectation generation: **1**
- Total non-guard entry calls, conservatively including generation: **40/40**
- Direct guarded-input calls: **26**
- Additional internal guarded calls from expectation generation: **6**
- Reviewer guarded calls: **32/32**; combined author plus reviewer guarded calls: **63/64**
- Additional seeded configurations: **60**; sequences: **60,000**; Bernoulli draws: **480,000**
- Cumulative full seeded passes: **4/4**, according to the existing historical execution record
- Wall execution: approximately **0.99 seconds**; process CPU: approximately **1.02 seconds**
- No publication, branch changes, new scientific configurations, or external services

No second run, retuning, or hidden retry occurred. Syntax compilation before the freeze was a setup check only; no target import/test occurred then.

## Boundaries exposed by held-out tests

1. **Known metadata is intentionally unvalidated.** A payload with forged `independent_verification`, controls, and limits still passes its mathematical payload. The validator correctly returns `metadata_claims=NOT_VALIDATED`, `scientific_claim=NONE`, and `historical_acceptance=FAILED/INCOMPLETE`. Consumers must preserve these labels and must never convert mathematical acceptance into endorsement of the supplied metadata.
2. **Strict parsing is not a general finite-float guarantee.** The valid JSON numeral `1e400` parses to infinity. The mathematical report comparator then rejects it, so this did not evade mathematical validation. The frozen requirement to reject named NaN/Infinity/-Infinity literals and duplicate keys passed. A broader claim that every parsed float is finite, including in ignored metadata, is not established and should not be made.
3. **Tests are finite.** This review did not evaluate adversarial resource exhaustion, arbitrary hostile Python objects, all probability distributions, all model families, runtime/OS diversity, or universal robustness.

## What remains unresolved

The parent problem asks whether model-disagreement stimuli distinguish mechanisms across held-out subjects/stimuli and model architectures. This synthetic scalar Bernoulli instance has no subjects, sessions, biological measurements, fitted high-capacity models, naturalistic stimulus constraints, causal interventions, or empirical mechanism exclusion. Its holdout is response-only: the selected stimulus is reused in evaluation.

Consequently, the parent claim remains empirically unresolved by these artifacts. This is **lack of relevant evidence**, not an impossibility theorem or a proof that the broader problem has no solution. Empirical data and preregistered cross-subject/stimulus/model-family evaluation would be needed for the parent scope. The current work supports only finite validation engineering and reproducibility of the specified synthetic example.

## Evidence files

All files are in this independent review directory, outside the author's candidate tree:

- `review-plan-freeze.json`: pre-execution plan, call caps, scope, and frozen script hash
- `independent_review.py`: single-run reviewer source
- `independent-oracle.json`: independently computed exact/Decimal oracle, persisted before importing the target validator
- `results.json`: all 82 checks, exact errors, call counters, key results and limitations
- `source-hashes-before.json`, `source-hashes-after.json`: all 78 original candidate file hashes
- `stdout.txt`, `stderr.txt`, `exitcode`: execution record; exit code 0, empty stderr

Reviewer source SHA256: `276e90528ee99f5c9dc2fffc6780f01020420b3637176469fb4b0ac9b597344f`.

Independent oracle SHA256: `050df17359d5a1f3a9a3144bb7904ee7e6583e59a0d862d7b85165a477caaa09`.
