# Scientific protocol, public summary

This is a postrun public summary of an already frozen scientific design. It is not a new preregistration. The original pre-data freeze and independent pre-data review were private workflow records. Their original SHA-256 commitments are in DERIVATION.json; the public package does not claim to verify omitted private contents or chronology independently.

## Question and design

Does using a positive original-question answerability label as a certificate of complete source-proposition preservation accept deliberately incomplete or changed propositions more often than an explicit full-proposition entailment task?

The twelve source scenarios and one preselected proposition per scenario are specified in `study/fixtures.json`, drawn from the pinned public source-aware packet. They provide targeted mechanistic coverage, not a representative sample. The historical rubric explicitly separates truth and answerability; the tested shortcut is hypothetical.

Each source has four passage variants:

1. Literal: the entire original source, byte-preserved.
2. Paraphrase: a manually authored meaning-preserving replacement of the selected target fragment, leaving all other source text unchanged.
3. Corrupted: one predeclared meaning-changing replacement, leaving all other source text unchanged.
4. No passage: empty text, a prompt-only negative control.

Target identification is casefold-only and must occur exactly once. The retained pre-data AI stimulus review checks the full modified passage and surrounding clauses. Its semantic approval is fallible, not human ground truth.

Two tasks occur for each variant. The `legacy` task asks the exact saved question and returns answerable, unanswerable or uncertain. The `entailment` task supplies the whole original proposition and returns supported, not_supported or uncertain. Both return the same case ID, decision, answer, exact evidence quotes and rationale fields. The full claim is legitimate entailment task input, not concealed answer-key leakage; its presence is an important task difference.

The 96 cases are distributed into eight packets of twelve cases. Each packet contains exactly one case per source and both tasks, using a fixed Latin rotation across variants/protocols. Opaque case IDs and deterministic SHA-256 ordering are retained. `prepared/packets.json`, `gold-key.json` and all eight exact scientific task prompts are byte-identical retained artifacts.

## Primary endpoint and gates

For source i, define L_i and E_i as 1 for a positive legacy or entailment verdict on its corrupted passage, and 0 for a valid negative or uncertain verdict. The primary endpoint is the mean of the twelve paired L_i − E_i values, with both positive counts reported separately. “False certification” refers to interpreting the verdict as whole-source faithfulness, not necessarily an incorrect answerability label for the question asked.

The pre-data operational rule requires all expected responses structurally valid and all contexts meeting the recorded execution constraints, plus:

- Corrupted-passage difference at least 0.25 (at least 3/12).
- At least 11/12 entailment positives on literal controls.
- At least 11/12 entailment positives on faithful paraphrase controls.
- At most 1/12 entailment positives without passage.

Missing and invalid answers never produce a successful gate. Uncertain is a valid noncertificate; control sensitivity prevents universal abstention from succeeding. Keep all twelve paired source differences, including zeros. No significance test, independent-96-cell inference or population/general-model accuracy estimate is part of this design.

Secondary checks include every task-by-variant cell, invalid/missing/uncertain counts, exact quoted-span integrity and positives lacking quotes. Always-positive, always-negative and a casefold full-claim substring entailment baseline expose trivial strategies. The substring baseline is not input-matched to legacy, whose prompt does not include the full claim. Synthetic oracle/baseline records are tests, never observed model performance.

## Execution limits and custody

Eight distinct fresh AI contexts were recorded with history disabled (`fork_turns=none`), requested xhigh reasoning and inherited model configuration. Model/backend version was not exposed. Each context was sent only its exact frozen scientific prompt as task input, not keys, other packets or study history. Task instructions prohibited tools and outside information, but shared tools/files were not security-isolated and actual tool traces were unavailable. This is procedural-only blinding, not verified absence of access. A recorded absence of observed contamination does not establish absence of hidden contamination.

The fixed budget was eight invocations, 96 judgments and a 60-minute first-start-to-last-completion window, with no retries, response repair or result-driven redesign. Duplicate identities/receipts, malformed responses, known contamination, observed tool use or timing failures would invalidate the relevant evidence. Original identity checks were performed on coordinator records; the public aliases can check derivative consistency, not reauthenticate original identities.

The observed run completed all 96 cases in 297 recorded seconds. Raw payloads are coordinator-captured visible FINAL_ANSWER content, not independently exposed transport bytes. Public receipts preserve prompt/raw hashes, timestamp observations, configuration and disclosure limits while omitting runtime identities. No new model calls are part of reproduction.
