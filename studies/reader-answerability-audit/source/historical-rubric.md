# Frozen prospective A-only dev rubric

No pretrained output has been generated or scored by this candidate. This is a preregistered procedure candidate for review, not a validated psychometric instrument. The dataset/references were authored and reviewed by AI without independent human validation. The fixed gate is feasibility only.

## Identity and blinding

Use O001–O024 exactly as frozen in EVALUATION_CASES.json, preserving source/profile/proposition/unknown-concept mappings. Do not score the references or copy/glossary controls as learned outputs. Complete RATING_TEMPLATE.json in a separate adjudication directory with adjudicator identity, AI/human kind, resolved-disagreement flag, exact output evidence spans and rationales. In this A-only gate arm blinding has no comparative value and no arm-blinding claim is made. Do not show the future answerer the model seed, training loss or any performance summary. Do not choose a favorable output or checkpoint.

## Phase 1: output-only answerability, separate descriptive record

An answerer sees ONLY scoring_text and the frozen required proposition questions, never source, ledger answers, reference, profile, glossary or previous adjudication. For each question record an answer, an exact output evidence span, answerable/unanswerable/uncertain, and a rationale based solely on output. Do not fill missing details with world knowledge or inferred original source. Later compare answers to the frozen ledger. Retain this phase before source-aware adjudication, preferably with a separate answerer/context. It is researcher/AI answerability, NOT measured human comprehension and NOT a substitute for truth/support judgments.

## Phase 2: source-aware truth

Using source, required proposition ledger, profile and authoritative shared glossary (but not reference rewrite), classify EVERY required proposition as preserved, omitted, contradicted or uncertain. Preservation requires correct participants/roles, negation/polarity, quantities and units, comparison/direction, causal or temporal order, conditions, exception and uncertainty scope. Paraphrases are welcome; exact reference/string overlap is irrelevant. A correct answer guessed from outside knowledge does not rescue an absent statement in the output. Ambiguous scope is uncertain, not preserved. Every preserved decision must quote an exact scoring_text span and explain the entailment; spans can be reused when appropriate. Record all unsupported scenario assertions with spans and rationale. Accurate generic supplied definitions are licensed background, not invented scenario events.

Truth-complete = every required proposition preserved, no omitted/contradicted/uncertain item. Truth-safe = truth-complete and no unsupported scenario assertion. Unsupported assertions remain separately visible even though the historical numeric fluency/truth gate did not add them as a third threshold.

## Phase 3: unknown-concept support

For EVERY stipulated unknown concept, classify supported, inaccurate, absent_or_unglossed or uncertain, with exact span/rationale. Support requires an accurate ordinary-language replacement or correct explanation that conveys the concept’s relevant meaning in context. A term alone, dropping the concept/event, or an inaccurate/ambiguous gloss is not support. A clear replacement can support without retaining the technical label. Definitions must not distort the proposition. Require all unknown concepts to be supported for that output’s support pass. Extra accurate explanations of known concepts are optional and recorded descriptively, not automatic failures. A universal-glossary answer can legitimately pass both truth and support.

## Phase 4: presentation

Fluency pass means grammatical/intelligible connected English whose clauses and references can be resolved without reconstructing missing text; minor harmless punctuation/spelling does not fail it. Fail garbling, fragmentary dangling clauses, repeated degeneration or semantically uninterpretable language. Mark uncertain when judgment cannot be resolved conservatively.

Task-following pass means an attempted faithful rewrite of the supplied scenario, not unrelated answers/instructions, a refusal, meta-commentary alone or a list of disconnected definitions instead of the scenario. Copying a faithful source is not by itself task failure; it may fail unknown support. Fluent omissions fail truth, regardless of presentation. A token-cap hit is recorded but does not automatically pass or fail semantics: a complete grammatical answer can finish without observed EOS, while a dangling capped fragment fails fluency/truth as applicable.

Record token length, cap/EOS status, source-copying, repetition, additional known-concept explanations and paired-profile selectivity descriptively. Do not infer register generalization or cognitive modeling from these measures. No lexical/readability/head-accuracy proxy can replace semantic adjudication.

## Derived counts and unchanged decision

Fixed denominator = all 24 expected profile outputs. Missing/unscored/uncertain/unresolved items count zero; do not drop them or change the denominator. Unresolved disagreements count conservative failure and are described separately. Do not mark adjudication_complete until each proposition, unknown concept, fluency/task following and unsupported-assertion review is complete.

- Fluent/truth-complete numerator: fluency pass AND task-following pass AND every required proposition preserved. Advance floor >=18/24.
- Unknown-support numerator: every stipulated unknown concept supported, independently of the first count. Advance floor >=12/24.
- Historical gate: both separate floors met. They are not a demand for 18 or 12 joint successes and do not imply the same outputs pass both.
- Also report truth-safe AND all-unknown-supported success, all contradictions/omissions/uncertainties, unsupported assertions, missing/incomplete ratings, each output and source/profile pair. This stricter endpoint is NOT a post hoc replacement numeric gate.

If no output has completed semantic adjudication, report semantic_status unmeasured and capacity_gate_passed null, rather than calling an absent measurement a model failure. With partial adjudication, retain the 24-output denominator and count every missing/unfinished rating conservatively as zero; disclose partial measurement.

Scores must bind to strictly validated returned outputs and actual evidence-span substrings. scripts/score.py first reconstructs the expected frozen admission and strictly reconciles the complete model run with external exit evidence. It cannot adjudicate semantics. A failed/incomplete engineering run cannot be promoted to a semantic gate pass by scoring a favorable subset. Retain complete individual ratings/rationales and AI/human limitation disclosures before announcing any capacity conclusion. A pass never launches other arms or opens test.
