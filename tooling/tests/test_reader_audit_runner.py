"""Exercise the real aggregate CLI against synthetic temporary repositories.

The retained audit is copied unchanged except in explicitly synthetic mutation
tests. Tiny NumPy/tooling stand-ins avoid recursively invoking this test suite.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
STUDY = Path("studies/reader-answerability-audit")


class ReaderAuditRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-audit-runner-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        (self.root / "tooling/tests").mkdir(parents=True)
        (self.root / "tests").mkdir()
        shutil.copyfile(ROOT / "tooling/run_tests.py", self.root / "tooling/run_tests.py")
        shutil.copytree(ROOT / STUDY, self.root / STUDY)
        self.audit = self.root / STUDY
        for folder in ("tests", "tooling/tests"):
            (self.root / folder / "test_standin.py").write_text(
                "import unittest\n"
                "class StandIn(unittest.TestCase):\n"
                "    def test_pass(self): self.assertTrue(True)\n",
                encoding="utf-8",
            )

    def run_cli(self, *args, no_site=False, optimized=False, timeout=30):
        env = dict(os.environ)
        # Invoke the parent without -B: the runner must protect its own children.
        env.pop("PYTHONDONTWRITEBYTECODE", None)
        env.pop("PYTHONPYCACHEPREFIX", None)
        command = [sys.executable]
        if no_site:
            command.append("-S")
        if optimized:
            command.append("-O")
        command.extend([str(self.root / "tooling/run_tests.py"), *args])
        return subprocess.run(command, cwd=self.temp.name, env=env,
                              capture_output=True, text=True, check=False, timeout=timeout)

    def assert_release_unchanged(self, before):
        after = {p.relative_to(self.audit).as_posix(): p.read_bytes()
                 for p in self.audit.rglob("*") if p.is_file()}
        self.assertEqual(after, before)
        self.assertFalse(list(self.audit.rglob("__pycache__")))

    def test_default_verifies_release_and_runs_audit_tests_without_writes(self):
        before = {p.relative_to(self.audit).as_posix(): p.read_bytes()
                  for p in self.audit.rglob("*") if p.is_file()}
        run = self.run_cli()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn('"trusted_manifest_pin_checked": true', run.stdout)
        self.assertIn('"cases": 96', run.stdout)
        self.assertIn("test_analysis_arithmetic_and_custody_tampering_rejected", run.stderr)
        self.assertIn("Ran 24 tests", run.stderr)
        self.assert_release_unchanged(before)

    def test_corrupted_observed_payload_fails_aggregate(self):
        raw = self.audit / "run-001/B01.raw.txt"
        raw.write_bytes(raw.read_bytes() + b"\n")
        run = self.run_cli()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("manifest file digest mismatch", run.stderr)

    def test_resealed_synthetic_readme_cannot_replace_published_release(self):
        readme = self.audit / "README.md"
        readme.write_bytes(readme.read_bytes() + b"\nSynthetic test mutation.\n")
        manifest_path = self.audit / "PUBLIC_MANIFEST.json"
        manifest = json.loads(manifest_path.read_bytes())
        row = next(row for row in manifest["files"] if row["path"] == "README.md")
        row.update(bytes=len(readme.read_bytes()), sha256=hashlib.sha256(readme.read_bytes()).hexdigest())
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        seal_path = self.audit / "PUBLIC_SEAL.json"
        seal = json.loads(seal_path.read_bytes())
        seal["public_manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        seal_path.write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n")
        run = self.run_cli()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("published manifest", run.stderr)

    def test_changed_verifier_is_rejected_before_execution(self):
        marker = Path(self.temp.name) / "untrusted-code-executed"
        (self.audit / "verify_public.py").write_text(
            "from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('executed')\n"
        )
        run = self.run_cli()
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse(marker.exists(), "changed release code was executed before authentication")
        self.assertIn("published verifier", run.stderr)

    def test_audit_only_works_without_site_packages_or_other_suites(self):
        # Neither the NumPy suite nor the optional pretrained suite may run.
        (self.root / "tests/test_standin.py").write_text("raise RuntimeError('other suite ran')\n")
        (self.root / "tooling/tests/test_standin.py").write_text("raise RuntimeError('other suite ran')\n")
        run = self.run_cli("--reader-audit-only", no_site=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn('"verified": true', run.stdout)
        self.assertIn("Ran 24 tests", run.stderr)
        self.assertNotIn("other suite ran", run.stdout + run.stderr)

    def test_missing_release_fails_instead_of_silently_skipping(self):
        shutil.rmtree(self.audit)
        run = self.run_cli()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("reader-answerability-audit", run.stderr)

    def test_optimized_python_still_rejects_replaced_manifest(self):
        (self.audit / "PUBLIC_MANIFEST.json").write_text("{}\n")
        run = self.run_cli(optimized=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("published manifest", run.stderr)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO files are not supported on this platform')
    def test_fifo_manifest_is_rejected_without_blocking(self):
        manifest = self.audit / "PUBLIC_MANIFEST.json"
        manifest.unlink()
        os.mkfifo(manifest)
        run = self.run_cli("--reader-audit-only", timeout=5)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("regular file", run.stderr)

    def test_symlink_verifier_is_rejected_before_execution(self):
        verifier = self.audit / "verify_public.py"
        target = Path(self.temp.name) / "synthetic-verifier.py"
        shutil.copyfile(verifier, target)
        verifier.unlink()
        try:
            verifier.symlink_to(target)
        except (NotImplementedError, OSError):
            self.skipTest('Symlinks are not available to this test process')
        run = self.run_cli("--reader-audit-only")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("regular file", run.stderr)

    def test_audit_only_rejects_pretrained_options(self):
        for args in (("--pretrained", "--model-dir", "unused"), ("--model-dir", "unused")):
            with self.subTest(args=args):
                run = self.run_cli("--reader-audit-only", *args)
                self.assertEqual(run.returncode, 2)
                self.assertIn("cannot be combined", run.stderr)

    def test_failing_regular_suite_still_fails_aggregate(self):
        (self.root / "tests/test_standin.py").write_text(
            "import unittest\nclass StandIn(unittest.TestCase):\n"
            "    def test_fail(self): self.fail('synthetic root-suite failure')\n"
        )
        run = self.run_cli()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("synthetic root-suite failure", run.stderr)


if __name__ == "__main__":
    unittest.main()
