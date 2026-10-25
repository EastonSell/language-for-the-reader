# Reader cue-control results

**Null result in this instruction-conditioned, fixed fictional assay.** The prespecified corrupted-passage relevant-minus-unrelated positive-support contrast was **0/12 = 0 percentage points**. No corrupted or empty passage was certified in any cue arm; all literal and paraphrase passages were certified. This does not establish general robustness or human benefit.

## Scope and collection

Twelve new AI-authored fictional scenarios × four passage variants × three cue conditions produced 144 judgments. The full proposition, passage and preservation task were held fixed across cue conditions. Relevant and unrelated cues had equal whitespace word counts. Every prompt explicitly instructed the evaluator to ignore the cue as evidence and assess the entire proposition.

The deterministic Latin assignment used 12 fresh contexts, one case per source per context. It was balanced but not randomized. Collection requested no inherited history, xhigh reasoning and inherited model selection. The backend/model identity and tool traces were not exposed; null telemetry does not mean verified zero tool use. No known tool use or contamination was observed, but shared tools/files were not hard-isolated.

Exactly 12 invocations ran sequentially, with no retry, replacement, prompt amendment, response repair or data-dependent expansion. First dispatch: 2026-10-25T08:08:13.829280+00:00. Last raw capture: 2026-10-25T08:20:32.881896+00:00. Elapsed: 739.052616 seconds, within the fixed 2,700-second window.

Raw files preserve the visible final-answer payloads as UTF-8 without an added terminal newline. They are not original transport-byte captures. Invocation metadata consists of coordinator attestations, not authenticated backend telemetry.

## All 12 cells

| Passage | Cue | Supported | Not supported | Uncertain | Missing/invalid | Fixed denominator | Support-rate bounds |
|---|---|---:|---:|---:|---:|---:|---|
| literal | absent | 12 | 0 | 0 | 0 | 12 | [1.0, 1.0] |
| literal | relevant | 12 | 0 | 0 | 0 | 12 | [1.0, 1.0] |
| literal | unrelated | 12 | 0 | 0 | 0 | 12 | [1.0, 1.0] |
| paraphrase | absent | 12 | 0 | 0 | 0 | 12 | [1.0, 1.0] |
| paraphrase | relevant | 12 | 0 | 0 | 0 | 12 | [1.0, 1.0] |
| paraphrase | unrelated | 12 | 0 | 0 | 0 | 12 | [1.0, 1.0] |
| corrupted | absent | 0 | 12 | 0 | 0 | 12 | [0.0, 0.0] |
| corrupted | relevant | 0 | 12 | 0 | 0 | 12 | [0.0, 0.0] |
| corrupted | unrelated | 0 | 12 | 0 | 0 | 12 | [0.0, 0.0] |
| empty | absent | 0 | 12 | 0 | 0 | 12 | [0.0, 0.0] |
| empty | relevant | 0 | 12 | 0 | 0 | 12 | [0.0, 0.0] |
| empty | unrelated | 0 | 12 | 0 | 0 | 12 | [0.0, 0.0] |

All 144 expected cases were admitted; no raw, custody or packet invalidity was recorded. Literal/paraphrase sensitivity against the reviewed fictional labels was 12/12 in every cue arm; empty-passage false certification was 0/12 in every cue arm. These controls rule out an always-positive or always-negative response policy within this assay.

## All 12 primary paired contributions

| Source | Absent supported | Relevant supported | Unrelated supported | Relevant − unrelated bounds |
|---|---:|---:|---:|---|
| amber_beacon | 0 | 0 | 0 | [0, 0] |
| ceramic_quay | 0 | 0 | 0 | [0, 0] |
| chalk_harbor | 0 | 0 | 0 | [0, 0] |
| glass_ferry | 0 | 0 | 0 | [0, 0] |
| lantern_pier | 0 | 0 | 0 | [0, 0] |
| mosaic_depot | 0 | 0 | 0 | [0, 0] |
| paper_aviary | 0 | 0 | 0 | [0, 0] |
| prism_studio | 0 | 0 | 0 | [0, 0] |
| reed_pavilion | 0 | 0 | 0 | [0, 0] |
| ribbon_workshop | 0 | 0 | 0 | [0, 0] |
| sand_observatory | 0 | 0 | 0 | [0, 0] |
| wax_garden | 0 | 0 | 0 | [0, 0] |

Primary mean difference: 0.0. Its [0.0, 0.0] range is the frozen missing-data bound with no missing observations, not a confidence interval. Secondary corrupted relevant-minus-absent and unrelated-minus-absent contrasts are also 0.0. No p-values, population confidence intervals, success threshold or post-hoc subgroup claims are supplied.

## Interpretation limits

The directional cue-inflation hypothesis received no positive evidence in this bounded collection. This null is conditional on explicit whole-proposition instructions and these particular stimuli, cue texts, contexts and unknown backend configuration. It does not show spontaneous question answering is unaffected by cues, repair the earlier between-task confound, establish general model accuracy, rescue the earlier failed reader-capacity gate, demonstrate reader training, or measure human comprehension.

The 144 cells are dependent within contexts and repeated sources. The 12 sources are not a random population sample. AI-authored stimuli and AI-reviewed gold labels are not independently authored human ground truth. One observation per cell supplies no estimate of response stochasticity; the deterministic layout does not identify an unbiased population causal effect.

## Verification and historical preservation

The frozen offline analyzer and all 41 synthetic tests passed again normally and under -OO after collection. These tests are engineering checks, not extra scientific observations. A first postrun test command was launched from the wrong working directory and failed to import two modules; that failed operator check is retained privately, and the correctly scoped test commands passed without code changes. No evaluator was rerun. All 43 files of the prior answerability package remain unchanged.

The independent pre-data semantic/technical review and postrun review passed for the original evidence. See REVIEW.json for scope and original review hashes, METADATA_DERIVATION.md for privacy transformations, and results/ for all retained judgments.
