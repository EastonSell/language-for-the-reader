# Selection is not realization: a falsifiable reader-adaptation control

Model-free analysis dated 2026-10-24. Published as an additive diagnostic supplement, not a new model result. No model/API run, retraining, corrected005 reconstruction, or B/C/S/test admission was performed. The original gate remains failed (14/24 fluent truth-complete, 3/24 all unknown supported). Lost corrected005 seals remain lost; that gate is NULL/unvalidated.

## New diagnostic result

The public annotations separate two defects often conflated as “failure to adapt”: choosing the appropriate meanings and expressing them without destroying scenario constraints. This package turns that distinction into an executable control rather than recommending more training.

1. There are 74 unique output-by-proposition judgments: 64 preserved and 10 failed. Exactly 5 of the 10 failed proposition judgments were nevertheless rated output-only **answerable**. Four are missing exclusive restrictions (O001/O002 and O005/O006); the fifth is O011's wrong mixture entity. An answerability reward can therefore positively credit the failure mechanism. This is a recount of retained AI annotations, not five newly adjudicated judgments and not evidence of human error.
2. All-support successes are concentrated in **two of 12 scenarios**: bubble_clock-01 has 1/2 and bubble_clock-02 has 2/2; each of the remaining ten scenarios has 0/2. None of the three support successes is truth-complete. At the scenario-pair level, 3/12 have zero truth-complete profiles, 4/12 have one, and 5/12 have both. The 24 outputs are not 24 independent scenarios.
3. A full glossary sentence and a correct binding are different things. O001 contains a correct wheel/cord description without an explicit pulley link. Conversely O014 binds a toothed wheel to the correct participant but omits outgoing motion transfer; the annotation marks gear support uncertain. O009/O011 show a more severe correct-domain/wrong-role problem. These examples motivate separate routing, definition-completeness, and realization diagnostics, not a single readability score.
4. The synthetic profile supplies the relevant knowledge state explicitly. Its routing subproblem has a deterministic solution: choose the complement of known terms. The executable oracle computes the complement from model_input alone, without access to gold target IDs, and achieves 576/576 exact selections across 24 public profiles and all 24 candidate permutations. **This is not model performance**. It establishes that any subsequent adaptive prose system must be compared with simple routing plus faithful composition, not only with an unadapted language model.

## Minimal discriminating experiment

Use `selector-inputs.jsonl` as an exposed-development diagnostic, not a new held-out benchmark. Feed ONLY each record's `model_input` to a future model; `case_id` and `kind` are bookkeeping, never prompt features. Keep `selector-gold.jsonl` inaccessible to the selector. No frozen proposition questions, expected answers, source-aware ratings, historical outputs, unknown-term list, or profile A/B suffix occurs in the model input. Source facts and candidate meanings are legitimate task inputs, not evaluation answers.

For each source, both complementary knowledge profiles see the **same source and identical four candidate meanings in the same order**. Only `reader_knows` changes. All candidate definitions are copied from the authoritative public glossary, rather than mixing truthful candidates with attractive false candidates. The source is not rewritten. The output is exactly two distinct sorted one-digit IDs, e.g. `0,2`, so output verbosity cannot improve recall. The same maximum response-token budget must be used prospectively; three ASCII characters are not a guarantee of identical model token counts. Permutations balance position and candidate-length preferences; a profile-blind length preference still has exactly 1/2 paired recall. Unequal glossary lengths cannot masquerade as a profile effect because both profiles see the identical full menu. Do not compare the lengths of rendered prose as if they were matched.

Primary scores are validity, unknown recall, and selectivity = unknown-selection rate minus known-selection rate. For two selected concepts out of four with two unknown, selectivity equals hits minus one. Report invalid responses separately and retain them in the denominator with zero credit; do not mistake an all-invalid selectivity of zero for successful null behavior.

The key paired statistic is the average selectivity across the two complementary profiles (equivalently, mean matched-minus-swapped unknown recall). Any deterministic profile-blind selector using the same pair for both profiles has **exactly zero**, whatever its candidate or length preference. The oracle is +1 and the swapped oracle is -1. Uniform two-of-four selection has mean unknown recall 1/2 and exact-pair probability 1/6, derived by enumeration, not simulation. **Important:** the 1/6 exact-pair figure is the uniform-random null, not the profile-blind ceiling. A profile-blind selector can memorize one of the two exposed complementary concept sets and score 1/2 exact-pair accuracy while ignoring the profile entirely. Exceeding 1/6 therefore does not establish adaptation. Paired selectivity remains exactly zero for that policy. The 576 permutation cells remain only 12 source clusters; never treat them as 576 independent examples.

Prospective falsification:
- Failure to exceed profile-blind selectivity, or failure under candidate-order permutations, identifies a routing/profile-use problem before costly prose training. An invalid response rate must be reported alongside this statistic.
- Good routing with poor source-aware prose performance shifts the bottleneck to realization/meaning completeness, not whether the model noticed the reader profile. This is a diagnostic implication to test, not an observed model result.
- A prose system that cannot outperform the deterministic scaffold on truth and unknown-concept support does not demonstrate that learning the rendering stage was necessary. It may still outperform it in style or usability, which requires a separate evaluation.
- All-glossary output can attain support coverage without adaptation. It is rejected by the exactly-two selector rule; in prose comparisons retain it as a nonadaptive verbosity control and report known-concept explanation rate, not only unknown recall.

## Faithful-composition control, clearly synthetic

`synthetic-scaffolds.jsonl` contains 24 deterministic source-plus-glossary constructions. The source prefix is byte-identical to the public source. Each appendix explicitly binds a term to its full authoritative definition, removing O001-style disconnected-description ambiguity by construction. They do not attempt contextual prose rewriting, and their lengths are not matched to historical outputs. Source-byte preservation and glossary provenance are verified; human comprehension and whole-document semantic adequacy are NOT independently established. These are neither repairs of the historical generated outputs nor replacements for historical gate scores.

The next realization experiment should compare source-preserving appendices, controlled contextual insertion, and free rewriting while holding selected meanings fixed. Evaluate source-specific scope, participant binding, and defining functions separately. Before any broader run, freeze a new protocol and new development fixtures. Do not revive corrected005 or reuse the original held-out B/C/S/test plan based on these controls.

## Answer-leakage sensitivity

The existing questions are not a sufficient semantic test. For example, “When is balance checked?” can be answered “after closing” while dropping “only”; “Does the pulley lift the counterweight today?” itself supplies the day anchor, although the retained answerer correctly flagged its absence in O004. We found no demonstrated question-induced restoration in O004. A future audit should include neutral extraction (“What timing restrictions are explicitly stated?”), boundary probes (“Is checking before closure excluded?”), and source-free evidence spans. Compare full, restriction-deleted, and wrong-entity text in a frozen synthetic suite. Questions must not be visible to the rewriting model; answerability alone must not replace source-aware truth scoring. Such question effects are hypotheses, not results of this model-free package.

## Reproduction and provenance

From this directory:

    python analyze.py
    python controls.py
    python -m unittest -v test_controls.py

Standard-library only; no network or model execution. `analyze.py` verifies every consumed public file against the retained `SOURCE_IDENTITY.json` SHA-256 inventory before recounting. Defaults use the sibling `../reader-capacity-gate` study and the bundled `SOURCE_IDENTITY.json`; `--source` and `--identity` allow relocation for the audit. Clone the repository and run from this supplement directory. This is a derivative analysis of saved public evidence. Acquired public commit: 66c97db6c78fb62ef42739acc2ff67ba6ae84b80. Publication preflight independently verified main at 79b745b5374293560ba9a0c546ce0403837ffb80 and matched all 59 original source files to its recursive Git tree by Git blob identity. The original study remains untouched.

Main source: https://github.com/EastonSell/language-for-the-reader/tree/66c97db6c78fb62ef42739acc2ff67ba6ae84b80/studies/reader-capacity-gate

Limits: one small-model fixed attempt; exposed synthetic development data; AI-only annotations; manually chosen mechanistic examples; correlated profiles; a deterministic construction is not an empirical finding about model or human adaptation. The algebraic routing null is exact for the stated task, not a universal lower bound for natural readers.

## Construct and prospective-use limits

The correct labels are explicitly recoverable by set complement; source text and candidate meaning can be ignored. This deliberately trivial routing diagnostic cannot establish semantic understanding, inferred reader knowledge, novelty, natural-reader benefit, or comprehension. A single prompt failure is not universal incapacity. The exact paired null applies to a deterministic profile-blind choice; a stochastic policy satisfies it in expectation. Future runs must isolate context, counterbalance order, fix decoding and retry policy, keep gold inaccessible to model tools/context, and report invalid responses without valid-only filtering. The 12 source scenarios are descriptive clusters, not demonstrated independent draws.

The scaffold builder uses gold for construction; the input-only oracle independently obtains the same subset. A future system comparison must actually route then render. Glossary copying is provenance, not new semantic validation. These controls do not change the failed historical gate or restore corrected005.
