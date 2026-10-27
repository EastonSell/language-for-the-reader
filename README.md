# Language for the Reader

An explanation should fit the reader without changing the facts. This repository separates **content correctness**, **presentation**, **concept support** and **reader understanding** instead of treating clear-looking or consistent prose as evidence for all four.

## Abstract

This project tests whether explicitly requested presentation can change without corrupting content, using fixed synthetic tasks, a small pretrained-model pilot and retained AI-only semantic audits. Structural content/format separation guarantees stable predicted answers, but does not improve accuracy over a simpler unconditioned control. Auxiliary training objectives show no strict-answer advantage over ordinary supervised fine-tuning (SFT). A reader-specific rewrite attempt fails both semantic capacity thresholds. A subsequent audit shows that questions can remain answerable after a source proposition is corrupted; a separate same-task cue control finds no cue effect under explicit ignore-cue instructions. These results establish useful controls and failure cases, **not a successful reader-adaptation method or improved human comprehension**.

## Research question

**In these fixed synthetic studies, which approaches preserve content when presentation changes, and can answerability certify that the whole source proposition survived?**

The practical problem is that an explanation can be fluent, follow a requested style, and answer a question while still dropping a restriction or changing a participant. “Register” here means an explicit `introductory`, `working` or `technical` presentation request. Later synthetic profiles specify known and unfamiliar concepts. Neither setting infers a person's intelligence or demographics.

**Bounded answer:** separating content from formatting makes the *prediction* invariant, not necessarily true. Neither the auxiliary objectives nor the fixed rewrite attempt establish successful reader adaptation. Answerability is not a certificate of full-proposition preservation. The same-task cue control supplies a conditional null result, not general robustness. The evidence below answers this question within the retained tasks; whether explanations help human readers remains open.

## Findings that answer the question

These are different studies, not scores on one shared benchmark.

| Study and evidence | Observed result | What it answers—and what it does not |
|---|---|---|
| [Synthetic baseline](results/rebuild/summary.json) and [content/format separation](milestone2/RESULTS.md) | Separated width-32/46 models averaged 98.96%/99.31% answer accuracy with zero answer changes; the simpler unconditioned control reached 99.57%. These are means over nine runs: three overlapping splits × three seeds, without an independence or significance claim. | Structural separation preserves a predicted answer across formats, including wrong predictions. It did not beat the simpler control; auxiliary objectives did not fix the conditioned baseline's degradation. |
| [Pretrained LoRA pilot](pretrained/results/RESULTS.md) | Ordinary SFT, SFT + auxiliary head, and SFT + head + consistency each scored **25/48** strict-correct responses: 16 held-out source records × three registers. | No auxiliary-head advantage was demonstrated. The untouched base's 0/48 coincided with zero parser coverage, so that contrast mixes formatting and correctness; the 48 variants are not independent source records. |
| [Ordinary-SFT learning curves](studies/sft-learning-curves/README.md) | Later ordinary SFT reached **46/48 on reused development validation**. The separate repeat produced scheduled outputs through update 384, but its supervisor ended **`incomplete/accounting_failure`**. | More exposure/budget helped this structured task; this is neither a fresh test result nor an auxiliary-objective effect or clean supervised completion. |
| [Reader-specific rewrite capacity gate](studies/reader-capacity-gate/README.md) | **14/24** fluent truth-complete outputs against **18 required**; **3/24** supported every stipulated unfamiliar concept against **12 required**. | Both frozen semantic floors failed despite accepted engineering checks. These AI ratings do not justify the planned B/C/S efficacy comparison or establish human comprehension. |
| [Answerability versus full-proposition audit](studies/reader-answerability-audit/README.md) | Across 12 selected, previously exposed fictional scenarios, corrupted passages received **11/12 positive answerability** verdicts but **0/12 full-proposition entailment** verdicts. All 96 judgments were retained. | A question can remain answerable while the full source claim is no longer preserved. The protocols differ in target and supplied claim information, so this is **not an input-matched causal effect of question wording**. |
| [Same-task question-cue control](studies/reader-cue-control/RESULTS.md) | **144/144 AI judgments** across 12 new, nonrandomly sampled fictional scenarios were admitted. The corrupted-passage relevant-minus-unrelated support contrast was **0 percentage points**. Literal/paraphrase passages were supported 12/12, corrupted/empty passages 0/12, in every cue arm. | With the full proposition and task fixed, there was no positive evidence for cue inflation **under explicit instructions to ignore the cue as evidence**. This is not general robustness, trained-model efficacy or a human-learning result. |

The answerability audit is not a correction to the historical rubric, which already separated answerability from truth. Its two tasks cannot isolate question-induced restoration. The cue control tests a narrower contrast; its reported `[0, 0]` missing-data bounds are **not confidence intervals**. Neither audit rescues the failed rewrite gate. The AI audits have unverified backend identity and unavailable tool traces; cells share source scenarios and evaluator contexts, so 144 judgments are not 144 independent observations.

[Selection controls](studies/reader-selection-controls/README.md) further separate choosing unfamiliar meanings from expressing them faithfully: a deterministic input-only complement rule selects 576/576 exact pairs across permutations of 24 profiles from 12 source scenarios. This is an algebraic/synthetic control, **not model performance or 576 independent examples**. The [exploratory fourth-label probe](pretrained/exploratory-results/RESULTS.md) also remains exploratory because its facts were already inspected.

## Inspect the evidence

- [Evidence guide](docs/EVIDENCE_GUIDE.md): measures, failure examples and reproduction limits through the capacity gate.
- [Two-minute worked example](docs/START_HERE.md): a fixed formatter preserves a supplied fact even when that fact is wrong.
- [Research overview](docs/RESEARCH_OVERVIEW.md): motivation, hypotheses, controls and the path toward reader studies.
- [Pilot raw generations and findings](pretrained/results/RESULTS.md), [capacity source/output/ratings package](studies/reader-capacity-gate/README.md), [answerability audit](studies/reader-answerability-audit/README.md), and [cue-control prompts and raw judgments](studies/reader-cue-control/README.md).

## Verify saved evidence first

The following commands run from the repository root with Python 3.10+ and the standard library. They check retained files, mappings, counts and synthetic regression cases; **they do not load a model, dispatch AI evaluators, retrain, rerate semantics or measure comprehension**. Use `-B` to avoid adding bytecode to sealed packages.

```sh
# Published answerability hashes, arithmetic and 24 regression tests
python -B tooling/run_tests.py --reader-audit-only

# Failed rewrite gate: expect 14, 3, and capacity_gate_passed=false
python -B studies/reader-capacity-gate/verify_package.py

# Cue-control preparation, all 144 saved judgments, and 41 tests in each mode
(cd studies/reader-cue-control && python -B predata/admission.py --verify)
(cd studies/reader-cue-control && python -B predata/admission.py --analyze-run results)
(cd studies/reader-cue-control/predata && python -B -m unittest discover -s tests -v)
(cd studies/reader-cue-control/predata && python -B -OO -m unittest discover -s tests -v)
```

A passing verifier establishes consistency with the retained evidence and scoring rules, **not independent validity of AI interpretations or end-to-end historical reproduction**. See the [answerability check scope](tooling/READER_AUDIT_CHECKS.md), [fresh-directory audit reproduction](studies/reader-answerability-audit/REPRODUCE.md), [capacity reproduction limits](studies/reader-capacity-gate/REPRODUCE.md), and [cue metadata derivation](studies/reader-cue-control/METADATA_DERIVATION.md).

The historical root `MANIFEST.sha256` includes an older README hash. `sha256sum -c MANIFEST.sha256` is therefore **not a current-tree integrity check**; its README mismatch after documentation updates is expected. Historical manifests and sealed study evidence are not rewritten to make a new README match.

## Run the NumPy rebuild

This is a separate synthetic experiment, not verification of saved model outputs. Python 3.11+ and NumPy are required; the recorded environment was Python 3.12.14 with NumPy 2.3.5. Use a fresh output path:

```sh
export PYTHONPATH=src OPENBLAS_NUM_THREADS=1
python -B -m unittest discover -s tests -v
python -B -m run --out results/reproduction
python -B tooling/run_tests.py
```

These commands need no model download or API. The run regenerates all 12 synthetic models, splits and histories; the text-only baseline omits binary weights. The aggregate runner separates NumPy/tooling tests from the optional pretrained suite. See [separation reproduction](milestone2/RESULTS.md#reproduce) for that experiment.

For optional pretrained work, [pretrained/README.md](pretrained/README.md) documents the isolated dependencies, pinned model and replay setup. The [learning-curve guide](studies/sft-learning-curves/REPRODUCE.md) distinguishes inspecting saved evidence, replaying checkpoints and training again. Its model-free tests still require torch and safetensors. The capacity release does **not** include the complete historical training archive; obtaining the base model alone cannot recreate that attempt. Missing originals are not reconstructed by a passing public-package verifier.

## Finishing point and open questions

The deliverable here is a bounded, inspectable research record with explicit negative and null findings—not a deployed reader-adaptation system. The current question is answered by the retained comparisons and audits; the failed capacity thresholds and failed supervision status remain part of that answer. No auxiliary-head benefit, general robustness or human-comprehension improvement has been established.

Further work would be a **new study**, with its own prospective protocol:

1. Do ordinary SFT, auxiliary objectives and stop-gradient controls differ on genuinely new facts under comparable budgets?
2. Can a rewrite preserve restrictions, participant binding and uncertainty while explaining all stipulated unfamiliar concepts, beyond simple routing and source-preserving glossary controls?
3. Do independently authored explanations help people answer or act more accurately, without hiding omissions behind readability or answerability scores?

Correctness, consistency, style compliance, concept support and comprehension need separate outcomes. See the [research overview](docs/RESEARCH_OVERVIEW.md) for hypotheses; none of these open questions is silently counted as a completed result.

## Watch the narrated explanation

[![Narrated concept illustration](docs/animations/narrated/poster.png)](docs/animations/narrated/concept.mp4)

[43.5-second narrated MP4](docs/animations/narrated/concept.mp4) · [Complete transcript](docs/animations/narrated/transcript.txt) · [Captions](docs/animations/narrated/captions.vtt) · [Editable source and reproduction](docs/animations/narrated/RENDERING.md)

Speech-led Manim animation with a synthetic stock voice. Fixed template illustration · no model or reader experiment. This is an explanatory upgrade, not a new experimental result. Captions have approximate sentence timing. The [static-first viewer](docs/animations/narrated/index.html), poster and complete transcript provide a no-motion alternative. The original silent version and its historical QA remain unchanged below.

## Watch the concept in 24 seconds

[![The wrong supplied fact Bay 9 is copied into three requested formats. Agreement across formats does not verify the fact.](docs/animations/poster.png)](docs/animations/concept.mp4)

[24-second Manim MP4](docs/animations/concept.mp4) · [Optional GIF preview](docs/animations/concept.gif) · [Text transcript](docs/animations/transcript.txt) · [Captions](docs/animations/captions.vtt)

Rendered with Manim Community 0.22.0. Fixed template illustration · no model or reader experiment. No audio. The poster and transcript provide a no-motion alternative. The downloaded [HTML viewer](docs/animations/index.html) is static by default and never autoplays.

## Provenance and license

The NumPy studies are newly written recovery implementations. [The recovered historical README](historical/README.original.md) is preserved separately; its old metrics and commands are unvalidated historical material. Original code and synthetic data are [MIT licensed](LICENSE); the pretrained model and its retained notices use Apache-2.0.
