# One-command saved-evidence check

From the repository root, with Python 3.10+ and **only its standard library**:

```sh
python -B tooling/check_saved_evidence.py
# Full per-stage output as machine-readable JSON; optional report outside the repo:
python -I -S -B tooling/check_saved_evidence.py --json > /tmp/reader-evidence-check.json
```

An absolute path to the script works from any working directory. Each check has
an independent 120-second timeout, configurable with `--timeout SECONDS` (finite
and positive, at most 86400 seconds). The runner continues after failures and exits **0 only if all
seven checks pass**; otherwise it exits 1. Argument errors exit 2. Text output
includes every failed check's captured stdout/stderr; JSON includes those streams
for every check, the commands, working directories, return codes and errors.
A timeout is a verification failure, not a negative scientific result. Diagnose
its output before choosing a larger timeout; the tool never retries or repairs.

## Seven checks, not seven new studies

| Check | Existing operation | Meaning of success |
|---|---|---|
| answerability | `tooling/run_tests.py --reader-audit-only` | Published identity pins, retained evidence and 24 audit regressions pass. |
| capacity | `studies/reader-capacity-gate/verify_package.py` | Package mappings/counts verify; JSON `public_package_verified` is exactly true. **The scientific gate remains failed: 14/24 truth-complete, 3/24 concept-supported.** |
| cue-preparation | `predata/admission.py --verify` | Frozen preparation is internally consistent; not execution clearance. |
| cue-analysis | `predata/admission.py --analyze-run results` | Saved judgment admission reports `operational_complete` exactly true. A zero subprocess exit alone is insufficient. |
| cue-tests | The two existing cue test modules | All 41 deterministic regressions pass. |
| cue-tests-optimized | Same modules with `-OO` | Same regressions pass without Python assertions. |
| finite-profile-tests | The two existing finite-profile test modules | All four synthetic arithmetic/validity regressions pass; this is not trained-model transfer. |

Test modules are named explicitly so a missing test file cannot silently reduce
discovery coverage. No retained file is rewritten, and subprocesses use `-B` to
avoid bytecode writes, `-E` to ignore Python environment overrides, and `-S` to
disable site-package startup. Existing audit isolation/pins remain unchanged.
On POSIX, each stage uses a new process group; timeout kills that group, including
nested audit checks. On Windows only the direct subprocess is stopped: descendant
cleanup and a strict wall-clock bound are **not guaranteed**. Windows execution
has not been validated; the tested platform is Linux/Python 3.12.14.

## Scope and trust

This command calls **existing local Python code from a trusted checkout**. It is
not an operating-system sandbox, signature check, whole-tree authenticity check,
or protection against concurrent filesystem changes. Outside the answerability
release's existing pins, internal manifests do not establish independent release
identity. Use a trusted published commit when obtaining the repository.

It does not fetch data/models, train, run AI evaluators, rerate meaning, revive a
closed study, or measure human understanding. Saved AI judgments retain their
backend/procedural limitations. The capacity pass is **verification of a failed
gate**, never permission to continue the gated efficacy study. Historical root
and tooling manifests remain historical snapshots; no seals are regenerated.

The finite-profile regressions recompute the construction in memory; they do not
compare or authenticate `rows.json`. NumPy/model-training suites, selection-control
checks, original training archives, and historical model replay are outside this
quickcheck. For the wider engineering suite use `python -B tooling/run_tests.py`;
for optional pretrained prerequisites consult `pretrained/README.md`.

Regression tests for this wrapper:

```sh
python -B -m unittest discover -s tooling/tests -p test_saved_evidence.py -v
```
