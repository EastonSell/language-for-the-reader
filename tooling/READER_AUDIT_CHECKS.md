# Reader audit checks in the aggregate runner

The regular `python -B tooling/run_tests.py` command now starts by checking the
published reader answerability audit, then runs the existing NumPy and tooling
suites. The optional pretrained suite still requires `--pretrained --model-dir
PATH`; no model fetch or AI call is added.

For the audit alone, from the repository root:

```sh
python -B tooling/run_tests.py --reader-audit-only
```

This path requires only Python 3.10 or newer and its standard library. It can
also run with site packages disabled:

```sh
python -I -S -B tooling/run_tests.py --reader-audit-only
```

`--reader-audit-only` cannot be combined with pretrained/model-directory options.
The regular aggregate retains its existing Python 3.11+ and NumPy requirement.

## What is checked

1. Before executing the study's verifier, reject symlinks and nonregular
   entrypoint/manifest files, bound each metadata read to 64 KiB, and check the published manifest and
   verifier SHA-256 identities recorded at commit
   `83a1809fd9ada5704b5f40294de2d46eb3bf3136`.
2. Run that unchanged verifier with the explicit published manifest pin.
3. Run all 24 unchanged audit tests. They mutate temporary copies, never the
   retained release.

The published manifest SHA-256 is
`ed880344b01b7a7c42da62c1ef4323278d4fd71696c85b9599523205a466be62`.
The verifier SHA-256 is
`f376fc946df19497f93f4e7116c7da21f49e4c478ab825ec35fea20ed3e85d27`.
These pins are deliberately outside the sealed study. Changing a payload and
replacing its adjacent manifest/seal must not silently become the same release.

The audit commands use isolated Python startup with site packages and bytecode
writes disabled. A successful audit reports `trusted_manifest_pin_checked:
true`, 96 cases, 75 exact evidence quotes, corrupted-passage positives of 11/12
for answerability and 0/12 for full-proposition entailment. All 43 files under
`studies/reader-answerability-audit/` remain byte-identical to the published
release, including the scientific prompts, raw responses, apparatus and seals.

## Failures and limits

Missing files, changed verifier bytes, a replaced manifest, evidence corruption,
or a failed audit test make the command fail. The runner does not skip, repair,
re-seal or delete anything, including pre-existing Python caches. If the release
was accidentally changed, inspect the difference and restore the appropriate
files from the pinned commit before rechecking. A future release must receive
its own reviewed identity; do not update these pins just to make a failure pass.

This is deterministic verification of retained observations, not a new
experiment, preregistration, semantic rejudgment or proof of human learning.
It retains the original unknown backend and procedural-blinding limitations.
The pins require a trusted copy of this runner or the published commit; they
are not signatures or independent timestamps. Isolated Python startup is not
an operating-system sandbox or protection against concurrent filesystem
modification.

The unchanged `tooling/MANIFEST.sha256` and `tooling/RELEASE.md` describe the
older tooling snapshot, not the current aggregate runner. Its old runner hash
will differ after this additive integration.

## Regression tests

`tooling/tests/test_reader_audit_runner.py` invokes the real CLI in temporary
repositories with tiny stand-ins for the unrelated suites. It checks default
inclusion, audit-only operation without site packages, release byte identity,
missing/corrupt/re-sealed evidence, rejection of changed code before execution,
optimized-Python failure handling, incompatible options, and propagation of
regular-suite failure. No retained judgments are edited.
