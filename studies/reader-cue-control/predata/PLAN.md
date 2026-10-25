# Reader cue-control preparation

## Approved scope and design

The assigned design is a local, additive, pre-data study: twelve newly authored fictional sources, four passage variants, three cue conditions, twelve fresh contexts, one case per source per context. All arms use the same full proposition and preservation task. No model judgments, external APIs, installations, publication or historical-file edits are part of preparation.

The previous task comparison changed both task and supplied claim information. We choose a within-task cue intervention instead of repeating that comparison. Retained-case reanalysis is possible but cannot repair that confounding or provide fresh scenarios. Training a reader is outside this bounded assay.

## Implementation sequence

1. Define all twelve stimuli, expected entailment labels, exact cue controls and rationale. Independent semantic review is mandatory before evaluation.
2. Write synthetic tests first for complete denominators, Latin balance, equal inputs, strict parsing, quote grounding, partial-response bounds and immutable source identities. Observe expected failures against stubs.
3. Implement standard-library preparation and analysis, with no evaluator or network integration. Inputs are fixed JSON; evaluator output is captured separately without repair.
4. Generate exact prompts and private scoring key. Run normal and optimized synthetic suites; run an oracle-shaped fixture only as an explicitly synthetic analysis check.
5. Hash-freeze all source, stimuli, prompts, key, protocol and analysis. Independent reviewers must cite this exact freeze; changes invalidate review and require a new freeze before any judgments.

## Review focus

- Corrupted passages must not entail the original claim, including when only one qualifier disappears.
- Paraphrases must entail the full claim without relying on external knowledge.
- Relevant cues focus on a retained feature and unrelated cues add no target facts; relevant/unrelated word counts are equal.
- Every source appears exactly once per packet and in all twelve conditions across packets.
- Missing, malformed, duplicate, ungrounded or contaminated responses stay in the fixed 144-cell denominator and cannot become a completed run.

This file records preparation decisions, not execution clearance. No empirical outcome exists.
