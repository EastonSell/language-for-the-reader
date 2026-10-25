# Reader cue-control study: pre-data package

This additive package prepares a 144-judgment question-cue assay. No empirical judgments have been collected. The original reader answerability package is unchanged.

The full proposition and preservation task stay identical across cue arms, unlike the earlier between-task comparison. Twelve new fictional scenarios, four passage variants and three cue conditions are counterbalanced across twelve fresh contexts. Relevant and unrelated cues have matched word counts. Read PROTOCOL.md for fixed analyses and limitations.

## Offline checks

From this directory, with existing Python 3.10+ and its standard library:

    python -B -m unittest discover -s tests -v
    python -B -OO -m unittest discover -s tests -v
    python -B admission.py --verify

Preparation already supplies exact prepared/B01.prompt.txt through B12.prompt.txt, prepared/packets.json and prepared/gold-key.json. No command calls models, tools, APIs or network services. FREEZE.json binds all package files except itself and disposable bytecode. Extra payload files or modified bytes fail verification.

The tests exercise generated synthetic fixtures, including an oracle-shaped output, malformed responses, missing-data bounds and custody violations. They are not observed model performance.

## Required independent review

Review all twelve claim/paraphrase/corrupted triples and the cue information boundary in study/fixtures.json. Verify the 144-cell design, prepared prompts, admission logic and fixed analysis. Cite the exact FREEZE.json hash. Execution remains blocked until independent semantic and technical reviews pass and the study lead explicitly admits this exact freeze.

## Eventual collection

If separately admitted, dispatch only each exact scientific prompt to a distinct fresh context, no inherited history, inherited model and xhigh reasoning. Never attach the key or this package to an evaluator. Capture raw final payloads without repair. EXECUTION.md documents the coordinator receipt schema and stopping rules. The 45-minute window and twelve-invocation limit are fixed.

The package does not improve a trained reader or prove human benefit. It addresses a narrow assay-design confound; fixed AI stimuli and procedural blinding constrain any future result.
