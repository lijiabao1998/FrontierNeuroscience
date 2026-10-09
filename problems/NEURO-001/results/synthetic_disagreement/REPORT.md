# NEURO-001: synthetic model-disagreement unit baseline

Status: numerical outputs independently reproduced; overall frozen control acceptance FAILED/INCOMPLETE. Registered empirical NEURO-001 remains OPEN.

Public claim: https://github.com/lijiabao1998/FrontierNeuroscience/issues/3

## What was executed

A purpose-built, fixed-parameter Bernoulli example, not a reimplementation of either cited paper's neural networks or empirical results. Models A and B agree for nonnegative scalar inputs. A frozen nine-point model-only information criterion selects x=-1; ordinary comparison uses x=1/2. Evaluation uses new response draws at the selected input, not an unseen stimulus domain or held-out subjects. There are no subjects, sessions, species, recording modality, neural data, clinical data, model fitting or training.

The frozen affine functions replaced an earlier unfrozen sigmoid sketch before admission. Exact rational calculations enumerate nine binomial counts for eight independent responses. Sixty seeded configurations generated 60,000 sequences/480,000 draws. Histograms are the sufficient raw evidence for the frozen likelihood/posterior metrics; individual response sequences are reproducible from recorded seeds and Python version.

## Numerical results, independently reproduced

- Ordinary design: recovery 1/2 and expected information gain 0 bits.
- Diagnostic design: recovery 3807/4096 = 0.929443359375; eight-response information gain 0.7710929067550158 bits.
- Important misspecification result: with generator C (Bernoulli1/2) outside both candidates, max closed-family posterior reaches >=95% with probability37/128 = 28.90625%. High confidence cannot establish either candidate is true.
- Author checks passed their limited fixtures, but independent mutation testing exposed validator gaps described below. No thresholds were adjusted.

These are exact/float computations within a deliberately easy synthetic model family. No novelty, biological mechanism, clinical effect, natural-stimulus validity, general model-selection guarantee or completion of the parent empirical question is inferred. C has no candidate label, so its recovery accuracy is explicitly undefined rather than falsely scored correct/incorrect.

## Reproduce

From repository root, use Python standard library only:

    python problems/NEURO-001/experiments/synthetic_disagreement/baseline.py

Frozen protocol and code live under experiments/synthetic_disagreement. Results are under results/synthetic_disagreement. The admitted round contains search/provenance records, original stdout/stderr and exit code. Running again overwrites generated results; copy originals first when comparing execution metadata. Numerical outputs and histograms are deterministic; runtime/platform metadata need not match.

## Sources and reuse

- Golan, Raju and Kriegeskorte, arXiv1911.09288v2: https://arxiv.org/html/1911.09288v2 . Methods and limitations motivate model-disagreement controls. No source code, images or empirical data reused.
- Making models disagree to learn how brains compute: https://pmc.ncbi.nlm.nih.gov/articles/PMC13558085/ . Sections3.1/3.2 describe model uncertainty and expected-information objectives. This example uses prescribed scalar probabilities and does not reproduce review figures.

Only original short summaries, equations implemented independently, and wholly synthetic sufficient statistics are included. No third-party corpus, personal data, weights, credentials or paid services.

## Independent review and preserved failures

A separate verifier derived an ordered-sequence probability oracle from the protocol before reading author outputs. All60 seeded histograms reproduced exactly; largest entropy discrepancy was1.11e-16 and largest pooled Monte Carlo error0.0008375.

The author validator catches histogram-total changes but fails to reject total-preserving histogram corruption, changed diagnostic information gain, changed C confidence, NaN ordinary information gain, changed selected input and duplicate seed. The author exact probability routine also accepts an invalid truth probability outside[0,1], even though the separate entropy routine rejects it. These are real validation failures. Full frozen acceptance is therefore FAILED/INCOMPLETE, and the author's original all-checks flag must not be used as release or scientific acceptance. Independent checking supports the saved numerical outputs only. No author code was repaired this round.

The frozen protocol also left design-index label order and the posterior-mean referent implicit. The actual implementation uses ordinary then diagnostic, A/B/C truth order, and mean P(A|Y). These are disclosed post-freeze implementation choices, not retrospectively preregistered facts. Individual response replay is established for that implementation and environment.
