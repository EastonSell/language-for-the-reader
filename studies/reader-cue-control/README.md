# Reader cue-control study

**Null result, not a robustness or human-learning claim.** Holding the full proposition and preservation task fixed, the 12-source corrupted-passage relevant-minus-unrelated support contrast was 0 percentage points. All 144 expected judgments were retained and admitted. Every prompt explicitly instructed the evaluator to ignore the cue as evidence.

Read [the full results and all denominators](RESULTS.md), [the fixed protocol](predata/PROTOCOL.md), [the exact prompts](predata/prepared), and [all raw outputs](results). The older reader-capacity failure and answerability audit are unchanged.

## Offline reproduction

From this directory, Python 3.10+ standard library only:

```sh
(cd predata && python -B -m unittest discover -s tests -v)
(cd predata && python -B -OO -m unittest discover -s tests -v)
python -B predata/admission.py --verify
python -B predata/admission.py --analyze-run results
```

These commands do not dispatch evaluators. Public context identifiers are distinct pseudonyms, not backend-authenticated identities. See [metadata derivation](METADATA_DERIVATION.md). The public derivative freeze was made after data collection and is not a new preregistration; ORIGINAL_FREEZE.json preserves the original admitted identities. Historical status text under predata describes preparation time, not the current completed state.
