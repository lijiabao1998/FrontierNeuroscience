# Independent verification: NEURO-001 synthetic unit baseline

## Verdict

**Full frozen control acceptance: FAILED / INCOMPLETE. Numerical reproduction: PASS for the frozen synthetic instance.** The author validator accepts semantic corruption and an invalid truth probability at its exact-evaluation entry point. The independent verifier rejects every tested corruption. The parent empirical NEURO-001 question remains **OPEN**. This is no evidence for brain mechanisms, clinical utility, cross-subject generalization or a novel method.

The diagnostic input is x=-1. Exact eight-response equal-prior MAP recovery is 3807/4096 = 0.929443359375, versus 1/2 for ordinary x=1/2. Eight-response EIG is 0.7710929067550158 bits, versus zero. For out-of-family Bernoulli(1/2) truth C, P(max closed-family posterior >= 0.95) = 37/128 = 0.2890625; neither candidate is the generator. The mean posterior for A remains 1/2, while mean maximum posterior is approximately 0.8167767600679142. No calibration claim under C follows.

## Role, scope and independence

A separate reviewer session implemented `oracle.py` from the frozen protocol before viewing author source or outputs. It enumerates all 256 ordered binary response sequences per n=8 design, multiplying rational one-response likelihoods. It aggregates count masses only after sequence enumeration. Entropy quantities use direct joint-versus-product mutual information, unlike the author's entropy-difference/binomial-count implementation. No author code is used to calculate oracle values.

Exact results were saved before the author results were opened. The author source was then read to establish the seed-index mapping and audit its validation helper. The helper was loaded without executing the author's main function, and without writing bytecode or other files to the author repository. All reviewer files are in a separate directory. No author file or frozen protocol was amended, no external state was changed, and no packages were installed.

Review took place 2026-10-09, beginning approximately 22:29 UTC and completed at 22:33 UTC. One CPU process at a time, zero spend. The independent simulation recreated the same 60 configurations, 60,000 sequences and 480,000 draws. There were no parameter sweeps, tuning, threshold changes or additional scientific trial configurations.

## Checked artifacts

- Public claim: https://github.com/lijiabao1998/FrontierNeuroscience/issues/3 (read through GitHub connector; web fetch failed with cache miss)
- Round: runs/20261009T222712980221Z-gpt-NEURO-001/round.json, ADMITTED when reviewed
- Governance: 9c3ae2dbaa1c814f3ef451c041dedfe3b77d926f, local HEAD verified
- Protocol SHA256: 6cd7879947d13de6c7b92b0e91974769157dfbddcef844ed21d8e03a0cac9bfa
- Author baseline.py SHA256: 01e492d41322b4983526635012613dc039d402f005b704eefaf5a03ecc1e02aa
- Author results.json SHA256: 4cf9f92ad5d522fc9319d37aad7c345f793416ce7089c9f03073777547cb042e
- Author result location: problems/NEURO-001/results/synthetic_disagreement/results.json
- Initial protocol-first oracle.py SHA256: a1d81a0414d7e6e07abb7e629409c8eff036d1f369b70bf6fcc28b34ad036065

Repo AGENTS, README, STATUS, VALIDATION and NEURO-001 problem card were read, as were pinned governance AGENTS, EVIDENCE_POLICY, RESEARCH_PROTOCOL and GATE_CONTRACT. This review does not independently certify fresh-literature coverage, novelty, author pre-freeze timing claims or repository-wide governance compliance.

## Numerical results

- All nine selection-grid scores agree to <=1.1102230246251565e-16 absolute error; x=-1 is selected.
- All six truth/design count distributions and their rational normalizations agree exactly.
- Exact recovery fractions, confidence fractions, posterior-A means and EIG agree within the frozen 1e-12 entropy/numerical tolerance.
- All nine identical-model n=8 controls have exactly zero EIG and recovery 1/2.
- The improvement is 0.429443359375, exceeding the frozen 0.1 threshold.
- All 60 saved histograms reproduce entry-for-entry using the reported Python random.Random algorithm and seed mapping.
- Every recorded Monte Carlo metric and all ten pooled comparisons reproduce. Largest pooled deviation from exact is 0.000837499999999991, diagnostic C high confidence; the threshold is 0.025.
- Author stdout matches the result's designs, selected input and controls; stderr is empty and exit code is zero.
- The author code and result hashes were rechecked unchanged after the audit.

## Controls: passes and failures

The author's three explicit invalid-input cases reject (domain x=2, unknown model, entropy probability=2). Its total-changing histogram corruption rejects. Those narrow reported tests are reproduced successfully.

However, `validate_report` accepts all of the following semantic corruptions:

1. Move one observation between histogram bins while preserving the total 1000.
2. Add 0.125 bits to diagnostic EIG.
3. Replace diagnostic C high-confidence probability with zero.
4. Set ordinary EIG to NaN; the absolute-error comparison does not reject NaN.
5. Change selected_x from -1 to 1.
6. Duplicate a seed across rows.

These are concrete failed robustness tests of the author validation helper, not observed corruption in the frozen submitted result. `compare.py`, which checks against the independent oracle and exact replay, rejects all six and the original total-changing histogram corruption.

The author's `exact` entry point also accepts truth probability 2 and returns invalid signed probability masses; validation of probabilities is localized to `entropy` rather than uniformly enforced. Frozen calls use valid rational probabilities, so this does not alter the verified submitted numbers. The reviewer oracle rejects invalid rational and nonfinite probabilities and invalid input/sequence cases.

Do not describe the author's helper as an integrity checker for arbitrary tampered results or invalid inputs. The frozen requirement says invalid probability and tampered-result controls must reject: the existing narrow examples pass, but the broader mutations above expose inadequate rejection. Consequently the full frozen control acceptance is FAILED / INCOMPLETE, despite correct submitted arithmetic. This is not aggregate scientific success. Preserve these failures rather than silently strengthening the author's implementation within the frozen baseline. The independent verifier accompanies the numerical reproduction but does not erase this original failure. No author evaluator repair was attempted in this round; any repair needs a separate frozen review.

## Reproducibility ambiguities and interpretation limits

The protocol does not explicitly assign labels to design_index or truth_index, and its phrase "posterior mean" does not identify which posterior quantity. Post-freeze source details resolve these as ordinary then diagnostic; A, B, C; and mean P(A|Y). Full artifact replay is exact after these implementation details are read. Protocol-only attribution of a unique seed-to-condition mapping is weaker. The ordered-sequence arithmetic and selected input do not depend on the seed mapping and remain independently checkable.

This is a model-constructed easy discrimination example. Selection uses prescribed model probabilities, with no realized evaluation responses, but the selected input appears in evaluation. It is response holdout only. There is no unseen stimulus-domain, subject or session split; no biological data or model fitting; and no assessment of ecological validity, model flexibility, causal use or mechanistic exclusion. The public preparatory issue's broader wording about separate stimulus sets is not what the final frozen protocol or report claims.

## Reproduce the independent verification

From any directory, using Python standard library only (substitute absolute REPO and VERIFIER directories):

    python3 VERIFIER/oracle.py --repo REPO --simulate --design-order ordinary/diagnostic
    python3 VERIFIER/compare.py --repo REPO

`oracle.py` writes `oracle_results.json` next to itself by default. `compare.py` reads that file and writes `comparison.json`. Both paths can be redirected using their command-line flags where provided. Comparison pins the original author baseline/results and fails if they change; later revisions require an explicitly identified new review, not silently replacing these pins. To reproduce only protocol-first exact arithmetic without simulation, omit `--simulate` and write to a distinct file with `--output`.

## Deliverables and preserved attempt

- oracle.py: independent ordered-sequence/rational oracle and seeded replay
- compare.py: independent artifact comparison and author-control adversarial audit
- oracle_exact_results.json / oracle_exact.stdout.txt: protocol-first exact output
- oracle_results.json / oracle.stdout.txt: exact output plus all 60 independently generated histograms
- comparison.json / compare.stdout.txt: numerical agreement and exact failed-control evidence
- attempt_01_syntax_error.stdout.txt: initial oracle syntax error, before any computation; corrected locally and preserved
- MANIFEST.json: checksums and environment provenance

The raw comparator stdout and JSON preserve their original numerical PASS and LIMITED-coverage wording. The final acceptance judgment above is FAILED / INCOMPLETE; the raw comparison does not claim aggregate protocol success.

The initial implementation attempt had an unmatched parenthesis in the recovery-expression line. Python rejected it before computation. The syntax was corrected without changing models, evaluator or thresholds. No failed numerical scientific attempt was suppressed.
