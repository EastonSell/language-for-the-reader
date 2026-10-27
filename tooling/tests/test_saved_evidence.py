"""Offline runner tests: actual subprocesses, no models or external services."""
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

RUNNER = Path(__file__).resolve().parents[1] / 'check_saved_evidence.py'

class SavedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('check_saved_evidence', RUNNER)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def stage(self, source, verdict=None, timeout=3):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'probe.py').write_text(source)
            return self.module.run_stage(root, 'probe', '.', ['probe.py'], verdict, timeout)

    def test_success_captures_output(self):
        row = self.stage("print('retained evidence checked')")
        self.assertEqual(row['status'], 'passed')
        self.assertEqual(row['returncode'], 0)
        self.assertIn('retained evidence checked', row['stdout'])

    def test_exit_failure_captures_both_streams(self):
        row = self.stage("import sys; print('out'); print('bad', file=sys.stderr); sys.exit(7)")
        self.assertEqual(row['status'], 'failed')
        self.assertEqual(row['returncode'], 7)
        self.assertIn('out', row['stdout'])
        self.assertIn('bad', row['stderr'])

    def test_false_structured_verdict_fails_despite_zero_exit(self):
        row = self.stage('print(\'{"operational_complete": false}\')', 'operational_complete')
        self.assertEqual(row['returncode'], 0)
        self.assertEqual(row['status'], 'failed')
        self.assertIn('operational_complete', row['error'])

    def test_true_structured_verdict_passes(self):
        row = self.stage('print(\'{"operational_complete": true}\')', 'operational_complete')
        self.assertEqual(row['status'], 'passed')

    def test_invalid_missing_truthy_or_nonobject_verdict_fails(self):
        for payload in ('not json', '{}', '[]', '{"ok": 1}', '{"ok": "true"}'):
            with self.subTest(payload=payload):
                self.assertEqual(self.stage('print(' + repr(payload) + ')', 'ok')['status'], 'failed')

    def test_timeout_is_reported_with_partial_output(self):
        row = self.stage("import time; print('started', flush=True); time.sleep(10)", timeout=.1)
        self.assertEqual(row['status'], 'failed')
        self.assertIn('timed out', row['error'])
        self.assertIn('started', row['stdout'])

    @unittest.skipUnless(os.name == 'posix', 'POSIX process-group cleanup')
    def test_timeout_stops_nested_subprocess(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            child = "import time; from pathlib import Path; time.sleep(.5); Path('late-marker').write_text('still running')"
            parent = "import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', " + repr(child) + "]); time.sleep(5)"
            (root / 'probe.py').write_text(parent)
            row = self.module.run_stage(root, 'nested', '.', ['probe.py'], None, .2)
            self.assertEqual(row['status'], 'failed')
            time.sleep(.7)
            self.assertFalse((root / 'late-marker').exists())

    def test_missing_cwd_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            row = self.module.run_stage(Path(d), 'missing', 'absent', ['x.py'], None, 1)
            self.assertEqual(row['status'], 'failed')
            self.assertIsNone(row['returncode'])

    def test_no_bytecode_or_pythonpath_import(self):
        source = "import sys; print(sys.dont_write_bytecode); print(sys.flags.ignore_environment); print(sys.flags.no_site)"
        row = self.stage(source)
        self.assertEqual(row['stdout'].splitlines(), ['True', '1', '1'])

    def test_cli_outside_root_reports_all_missing_stages_json(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / 'tooling').mkdir()
            shutil.copyfile(RUNNER, root / 'tooling/check_saved_evidence.py')
            proc = subprocess.run([sys.executable, '-I', '-S', '-B', str(root / 'tooling/check_saved_evidence.py'), '--json'], cwd='/', capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            report = json.loads(proc.stdout)
            self.assertFalse(report['all_passed'])
            self.assertEqual(len(report['checks']), 7)
            self.assertTrue(all(x['status']=='failed' for x in report['checks']))
            self.assertIn('not', report['scope'])

    def test_missing_regression_files_cannot_pass_as_zero_tests(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for stage in self.module.STAGES:
                name, directory, arguments, verdict = stage
                if name in ('cue-tests', 'cue-tests-optimized', 'finite-profile-tests'):
                    (root / directory).mkdir(parents=True, exist_ok=True)
                    testdir = root / directory / ('tests' if name.startswith('cue-') else '.')
                    testdir.mkdir(exist_ok=True)
                    (testdir / 'test_standin.py').write_text('import unittest\nclass One(unittest.TestCase):\n def test_ok(self): pass\n')
                    row = self.module.run_stage(root, *stage, 3)
                    self.assertEqual(row['status'], 'failed', name)

    def test_invalid_timeout_rejected_before_checks(self):
        for arg in ('0', '-1', 'nan', 'inf', '1e300'):
            proc = subprocess.run([sys.executable, '-B', str(RUNNER), '--timeout', arg], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertIn('finite positive', proc.stderr)

if __name__ == '__main__': unittest.main()
