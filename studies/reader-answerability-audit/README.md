# Reader answerability audit: public derivative

A positive answerability verdict is not a certificate that an entire source proposition was preserved.

This package contains a completed, bounded AI-only audit on twelve selected fictional source scenarios, not a new trained reader or a human comprehension experiment. The public derivative was assembled after the run on 2026-10-25. Its public seal is not preregistration. A pre-data freeze and review existed as private workflow records; their hashes are retained in DERIVATION.json.

## Result

Positive verdicts per 12 source scenarios:

| Passage | Original-question answerability | Full-proposition entailment |
| --- | ---: | ---: |
| Literal original | 12/12 | 12/12 |
| Faithful paraphrase | 11/12 | 12/12 |
| Predeclared corruption | 11/12 | 0/12 |
| No passage | 0/12 | 0/12 |

The paired corrupted-passage difference is 11/12 = 0.9166666666666666. All 96 responses were structurally valid and all 75 supplied evidence quotes are exact contiguous passage substrings. The frozen operational gate passed under the coordinator-recorded context evidence. This checks arithmetic and quote integrity, not independent semantic adequacy of every quote.

The assay concerns an unsafe **hypothetical answerability-as-faithfulness shortcut**, not the actual historical rubric. The [historical rubric](https://github.com/EastonSell/language-for-the-reader/blob/fb85a2ef6ea8d11bd0e5f6a82a15b78d8caeda21/studies/reader-capacity-gate/evaluation/rubric.md) already separates truth from answerability and later compares answers with a ledger. A question can remain genuinely answerable even when its passage no longer preserves the whole original proposition.

For example, removing “only” can leave “When is balance checked?” answerable while losing exclusivity; omitting a signal's location can leave its duration question answerable. A changed process name may still answer its question, even though comparison against the original answer key would expose the change. The yesterday-for-today corruption was rejected by both tasks. One faithful threshold paraphrase was labeled unanswerable under the question task; that surface-sensitive result is retained without repair.

Neither protocol certified any no-passage case. Thus this run did not demonstrate prompt-only unsupported certification. No causal question-induced restoration effect follows: the protocols differ in target, explicit claim information and decision task, not wording alone.

## Method and limits

- Twelve intentionally selected, previously exposed fictional scenarios, including related domain pairs; four passage variants and two protocols yield 96 cells, not 96 independent observations. The twelve sources are not demonstrated independent random draws.
- Eight fresh AI contexts, twelve cases each, one case per source per context; history disabled, requested xhigh reasoning, inherited model configuration. Backend model/version and deterministic decoding were not exposed. No retries or scientific response repairs were recorded.
- Only each scientific prompt was supplied as study task input. Blinding was procedural, not security isolation: tools/files were shared, and tool traces were unavailable. Null observed-call counts mean unknown, not verified zero use. No guarantee against unobserved access is made.
- The coordinator recorded the visible FINAL_ANSWER payloads and timestamps. The eight raw files preserve those captured payloads byte-for-byte, including visible whitespace and no added terminal newline. Underlying transport bytes were unavailable. Public context aliases are postrun derivatives, not original runtime identities.
- Recorded pre-dispatch-to-final-receipt window: 2026-10-25 05:23:14–05:28:11 UTC, 297 seconds. These are coordinator observations, not backend execution telemetry.
- Stimuli and semantic review were AI-authored/reviewed, not human ground truth. Shared-provider effects, unknown backend, targeted selection and procedural blinding constrain interpretation. No population accuracy, general-model accuracy, human benefit, trained-model improvement or reader adaptation is established. The historical failed reader-capacity gate remains failed; no paused/lost dataset was reconstructed or admitted.

Full-claim entailment accepted all literal and paraphrase controls, unlike universal abstention or the casefold whole-claim substring baseline, which accepts literal originals but no paraphrases. Synthetic checks exercise arithmetic only and are explicitly separate from observed responses.

## Inspect and reproduce

Read [PROTOCOL.md](PROTOCOL.md) for the scientific method, [REPRODUCE.md](REPRODUCE.md) for an offline fresh-directory reproduction, and [DERIVATION.md](DERIVATION.md) for provenance and omissions. PUBLIC_MANIFEST.json hashes every payload file; PUBLIC_SEAL.json hashes that manifest. FILES.txt lists the complete public tree, including those two self-authentication files.

The supported entrypoint is `python -B verify_public.py`. It makes no model or network calls and requires only the Python standard library. `reference/original_audit.py` is an unchanged inspection/cross-check source; its original private-bundle CLI is not the public reproduction entrypoint.
