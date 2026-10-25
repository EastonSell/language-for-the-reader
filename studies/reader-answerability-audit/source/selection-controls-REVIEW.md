# Independent review receipt

Reviewed 2026-10-24. **Pass for the explicitly model-free, exposed-development diagnostic scope.** Not a model-performance finding, comprehension result, new gate pass, or restored corrected005 validation.

## Reproduced evidence

- All 59 retained source files match the bundled SHA-256 inventory. The publication preflight retrieved commit `79b745b5374293560ba9a0c546ce0403837ffb80` and its recursive Git tree; this review independently recomputed all 59 local Git blob identities against those receipts. `publication-source-check.json` records the results. This review did not itself request remote state.
- The offline analyzer's `latest_requested_commit_not_independently_verified` field refers to the analyzer's lack of network verification. It is compatible with the separate publication preflight above, not a claim that the preflight failed.
- Repository-relative defaults resolve the sibling original study and bundled identity inventory. `python analyze.py`, `python controls.py`, and `python -m unittest -v test_controls.py` succeed from this directory; 11 tests pass. `python independent_verify.py` reproduces the separate independent verification result.
- Independent checks confirm 576/576 input-only known-complement selections and 1,728 paired blind-selection checks across 288 source-by-order pairs. These remain 12 source scenarios, not 576 independent observations; even the 12 scenarios are not demonstrated independent draws.
- All 74 unique output-by-proposition judgments match final adjudication one-to-one. There are 64 preserved judgments and 10 failures: 7 omitted, 2 contradicted and 1 uncertain. Five of the 10 failures were nonetheless rated output-only answerable. This recount uses retained AI annotations, not new human adjudication.

## Corrections verified

The original synthetic oracle echoed gold target IDs. The revised oracle computes the complement using only permitted input, then compares with separately stored gold; an input knowledge-swap test and independent implementation verify this. The audit now verifies annotation keys/statuses and denominator integrity. Complementary profiles are checked by source and candidate order, not merely adjacency. Documentation distinguishes uniform-random exact-pair chance (1/6) from the profile-blind paired exact-match ceiling (1/2).

## Interpretation and prospective safeguards

For a valid two-of-four choice reused across complementary profiles, paired recall is exactly 1/2 and paired selectivity exactly zero. The input-only oracle has selectivity +1; its complement has -1. A stochastic blind selector satisfies the null in expectation, not necessarily each realized pair. Invalid outputs receive zero credit and must remain in the denominator; all-invalid selectivity zero is not success.

The correct subset is recoverable by set subtraction. Neither source text nor candidate meaning is needed. This is a narrow explicit-profile routing control, not evidence of semantic understanding, inferred reader knowledge, fluent realization, natural-reader benefit or comprehension. Answerability is not truth preservation. The historical gate remains failed.

Candidate order is fully permuted, and paired inputs differ only in known-term lists. Evaluation questions, gold targets and bookkeeping fields must remain outside future model context/tools. Prospective runs need controlled context, counterbalanced invocation order, fixed decoding/retry policy and complete invalid-response reporting. A result above random exact-match chance alone cannot establish adaptation.

Source-preserving appendices copy glossary definitions and retain source bytes, but have neither matched historical prose length nor independent whole-document semantic/comprehension validation. Their builder uses gold for construction; the input-only oracle shows the same subset is obtainable from permitted input. Any future pipeline comparison should actually route then render.

No blocking defect remains for this diagnostic scope. No model API, training, human experiment or new semantic adjudication was performed by this review. `SHA256.json` binds the published files, excluding itself and generated Python cache files.
