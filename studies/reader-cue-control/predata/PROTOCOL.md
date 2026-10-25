# Prospective reader question-cue control

Status: prepared for independent pre-data review. No evaluator has been dispatched and no empirical judgments exist. This local source freeze is not public preregistration, independent timestamp proof, or execution clearance.

## Motivation and bounded hypothesis

The earlier answerability audit compared different tasks with different explicit claim information. Its positive difference does not identify a causal question-cue effect. This new, additive study asks whether a narrow relevant question cue changes unsupported whole-proposition certification when the claim, passage and preservation task are held fixed.

The directional hypothesis is that a narrow relevant cue increases positive support judgments on corrupted passages relative to an unrelated cue. The prespecified primary is the mean of twelve within-source binary differences: supported under relevant cue minus supported under unrelated cue, using corrupted passages only. Uncertain is a valid noncertificate and is reported separately. There is no significance test, population confidence interval, claimed clinically/practically meaningful threshold or binary scientific success gate. Zero or negative differences are retained without redesign.

The intervention includes the particular cue texts and their relevance. It is not a claim to separate every lexical or pragmatic mechanism. Relevant and unrelated cues have identical whitespace word counts within source, not identical character lengths, tokenizations or semantic complexity. The absent-cue arm is a secondary anchor, not a length-matched intervention.

## Frozen material

Twelve newly AI-authored fictional scenarios are in study/fixtures.json. They are not a random sample or human-reviewed ground truth. None reuses the earlier twelve source scenarios. Each has a full one-sentence proposition and four passage variants:

1. Literal: the exact full proposition.
2. Paraphrase: a meaning-preserving restatement that entails the whole proposition.
3. Corrupted: a prespecified missing or changed fact that does not establish the whole proposition.
4. Empty: no passage facts.

Gold support is true only for literal/paraphrase. Normal language interpretation, elementary order/logic and standard duration-unit equivalence are allowed; no outside facts about fictional entities are available. A corruption may leave the proposition possible but not entailed. In particular, omitted exclusivity, location, identity or exclusion is not supplied by the query, plausibility or conversational assumption. Independent semantic review must adjudicate every passage, not simply accept the author's labels.

For each passage, three cue arms are evaluated: absent (empty string), relevant (a narrow question about a retained part of the proposition), and unrelated (a same-word-count question about unrelated entities). Every arm receives the identical full original proposition, passage and preservation instruction. The only varying task-input field is question_cue. All prompts explicitly say not to answer or treat the cue as evidence. This tests robustness under that instruction, not spontaneous question answering or the historical rubric.

## Assignment and denominator

Twelve sources × four variants × three cues = exactly 144 judgments. Twelve fresh contexts each receive twelve cases, exactly one per source. For source index i and block index b, condition index is (i+b) modulo 12 over fixed variant-major/cue-minor order. Every block contains each condition once; every source receives every condition once across blocks. Case IDs and within-block order use deterministic SHA-256 derivations with the frozen seed. No adaptive ordering, retry, replacement, response repair or packet enlargement is allowed.

This Latin layout balances the design but is not a randomized experiment. Source, context, prompt interactions and unknown backend configuration can still matter. Cases within a context and repeated variants of a source are dependent. The 144 cells are not 144 independent observations, and the twelve sources are not demonstrated independent population samples. A condition difference is a descriptive contrast in this fixed assignment, not an unbiased population causal estimate.

## Evaluator and custody requirements

At most twelve scientific invocations, all distinct fresh AI contexts with inherited model selection, requested xhigh reasoning and no inherited conversation. Each receives only its exact frozen Bxx.prompt.txt. The prompts prohibit tools, files, browsing and inter-agent contact. Do not include this protocol, keys, labels, hypotheses, other packets or collection-management instructions in scientific task input. No callbacks or evaluator prompt amendments are permitted.

Shared tools/files are not hard-isolated. Backend/version and tool traces may be unavailable. Record unknown traces as null, never zero. Known tool use or known contamination invalidates operational admission. Observed absence of contamination does not certify hidden absence. Record actual context IDs privately, exact prompt hashes, coordinator-observed start/completion timestamps and raw-response hashes. These records are coordinator attestations, not backend-authenticated telemetry.

The frozen collection window is 45 minutes from the first dispatch start to the final captured completion. Record twelve receipts even if an invocation fails, using the actual failure record rather than a fabricated scientific response. Missing or failed final payloads stay missing. There are no retries. A late return is retained but not admitted as a completed on-protocol run. If interrupted, preserve partial evidence and report inconclusive rather than filling gaps.

Raw files are UTF-8 encodings of the visible FINAL_ANSWER payload exactly as received, with no added terminal newline or content repair. Original transport bytes are not exposed; do not claim they are captured. JSON formatting defects are outcomes, not instructions to fix a response.

## Analysis and invalidity

study.py fixes design, strict response validation and analysis. admission.py verifies the complete pre-data file inventory, deterministic packet reconstruction, raw and prompt hashes, distinct contexts, requested configuration and capture window before combining responses. It has no evaluator, API or network integration.

Expected response fields are case_id, decision, evidence and rationale. Decisions are supported, not_supported or uncertain. Evidence entries must be unique, nonempty exact passage substrings; a positive decision needs at least one. Rationale must have 1–60 whitespace-separated words. At most eight evidence quotes and 256 KiB raw text per context are admitted. Duplicate JSON keys, nonfinite JSON constants, unknown/duplicate/missing IDs, extra fields, invalid types and Markdown wrappers are rejected, not repaired.

Any malformed response invalidates its whole twelve-case packet conservatively. Any missing/invalid custody receipt invalidates whole-run admission. Raw evidence remains retained. All 144 expected cells and all twelve sources remain in every analysis. Unknown cells contribute [0,1] binary bounds; corrupted paired differences retain their sharp missing-data range. No missing/invalid response becomes a negative judgment. A primary point estimate is withheld unless all 144 responses are admitted. Valid uncertain responses count as nonpositive but are separately enumerated. Operational completeness is not semantic correctness or a scientific discovery.

Report all twelve variant-by-cue cells: positive, negative, uncertain, missing/invalid, fixed denominator and positive-rate bounds. Report all twelve corrupted-passage paired differences, including zero values. Secondary contrasts are relevant-minus-absent and unrelated-minus-absent on corrupted cases, read directly from the published cell rates and paired rows. Report literal/paraphrase sensitivity and empty-passage false certification for every cue. These controls distinguish genuine selectivity from universal positive/negative policies. No post-hoc exclusion of difficult sources or follow-up subgroup inference is allowed.

Strict quote matching checks textual custody, not whether a quoted span semantically proves the claim. Independent postrun review must inspect semantic judgments and preserve disagreement rather than repair raw responses or silently relabel cells.

## Review, freeze and stopping gates

Before dispatch, independent reviewers must cite the exact FREEZE.json SHA-256 and confirm:
- Every literal/paraphrase supports the whole claim; every corrupted/empty passage does not.
- Cues add no factual evidence absent from the always-present claim and do not reveal scoring labels.
- Relevant/unrelated word counts, fixed-input equality and complete Latin assignment hold.
- Frozen analysis retains failures, complete denominators and valid null interpretations.
- Synthetic tests, fixture outputs and review prose are not empirical model observations.

The study lead must separately admit execution after both semantic and technical review. Review is not publication permission. Any pre-data correction produces a new freeze and requires relevant re-review. No data-dependent protocol change, rerun or replacement is permitted after first dispatch.

Stop after the twelve bounded invocations or an operational failure preventing further valid dispatch. Keep collected evidence, report its state and do not retry. No APIs, credentials, installations, remote publication or historical package modification are part of this study preparation.

## Interpretation limits

Even a positive contrast would establish only a bounded vulnerability in these AI judgments under the assigned cue manipulation. It would not demonstrate a historical scoring bug, trained-reader improvement, human understanding, general model accuracy, real-world efficacy or novelty. A null does not establish robustness generally. The earlier failed reader-capacity result is unchanged.
