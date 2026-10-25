# Reproduce offline from a fresh directory

Requirements: Python 3.10 or newer, standard library only. Use `-B` as shown: the sealed public release contains no Python cache directories or bytecode, and the verifier rejects them. No installations, credentials, network, private bundle, original runtime identities, or AI calls are required.

From this study directory, run:

```sh
python -B verify_public.py
python -B -m unittest discover -s tests -v
```

For a fresh-directory reproduction with no private files available, run this from the study directory:

```sh
python -B - <<'PY'
import pathlib, shutil, subprocess, sys, tempfile
source = pathlib.Path.cwd()
with tempfile.TemporaryDirectory(prefix="reader-audit-public-") as temporary:
    target = pathlib.Path(temporary) / "study"
    shutil.copytree(source, target)
    subprocess.run([sys.executable, "-B", "verify_public.py"], cwd=target, check=True)
    subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=target, check=True)
PY
```

The verifier checks exact manifest coverage and file hashes, source Git blob custody, all packet/prompt/key/fixture relationships, eight strict raw payload schemas, all 96 unique cases, exact quote spans, sanitized receipt consistency and timing, all cell counts and paired primary values. It independently recomputes the score and compares the byte-identical original scorer and retained analysis projection. Expected observations: 75 exact quotes; 96 valid records; corrupted legacy 11/12 versus entailment 0/12; entailment literal and paraphrase both 12/12; both no-passage cells 0/12; a 297-second recorded window; operational gate true under recorded context evidence.

Tests introduce synthetic mutations only in temporary copies. They never alter retained observed data. `prepared/synthetic-checks.json` is similarly labeled synthetic and is not an AI run.

The original `reference/original_audit.py` is preserved byte-for-byte as scientific apparatus. Do not use its original `prepare`, `verify` or `analyze-run` commands for this derivative: those expect omitted original files and do not define the public package. Do not regenerate an original private freeze from this postrun material.

A manifest and its adjacent seal detect inconsistency relative to their stated hashes, not adversarial replacement of both. Check the manifest SHA-256 against an independently retained release value for an external trust anchor. The verifier supports `--expected-manifest-sha256 HEX` for this purpose. Neither hashes nor public aliases prove backend model identity, zero hidden tool use, transport-byte authenticity or pre-data publication. A new AI run would be a new experiment, not deterministic reproduction of the judgments here.
