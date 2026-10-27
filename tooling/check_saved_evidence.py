"""Check retained reader evidence offline, not model efficacy or comprehension."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import signal
import sys

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ('Retained-file consistency and synthetic regression checks only; not a new '
         'experiment, semantic rerating, successful capacity gate, or human-comprehension result.')
# Existing entrypoints stay unchanged. In particular, cue analysis can exit zero
# while reporting an incomplete run: its JSON verdict is mandatory here.
STAGES = (
    ('answerability', '.', ['tooling/run_tests.py', '--reader-audit-only'], None),
    ('capacity', '.', ['studies/reader-capacity-gate/verify_package.py'], 'public_package_verified'),
    ('cue-preparation', 'studies/reader-cue-control', ['predata/admission.py', '--verify'], None),
    ('cue-analysis', 'studies/reader-cue-control', ['predata/admission.py', '--analyze-run', 'results'], 'operational_complete'),
    ('cue-tests', 'studies/reader-cue-control/predata', ['-m', 'unittest', '-v', 'tests.test_admission', 'tests.test_study'], None),
    ('cue-tests-optimized', 'studies/reader-cue-control/predata', ['-OO', '-m', 'unittest', '-v', 'tests.test_admission', 'tests.test_study'], None),
    ('finite-profile-tests', 'studies/finite-profile-control', ['-m', 'unittest', '-v', 'test_control', 'test_postfreeze_regression'], None),
)


def as_text(value):
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value or ''


def run_stage(root, name, directory, arguments, verdict, timeout):
    """Run one fixed local check, retaining failures instead of aborting the report."""
    command = [sys.executable, '-E', '-S', '-B'] + arguments
    cwd = root / directory
    row = dict(name=name, command=command, cwd=str(cwd), status='failed',
               returncode=None, stdout='', stderr='', error=None)
    env = {k: v for k, v in os.environ.items() if not k.startswith('PYTHON')}
    try:
        with subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, encoding='utf-8',
                              errors='replace', start_new_session=(os.name == 'posix')) as proc:
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired as error:
                # The audit entrypoint launches children. Stop its whole process
                # group on POSIX, not merely the wrapper. No shell is involved.
                if os.name == 'posix':
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    proc.kill()
                try:
                    stdout, stderr = proc.communicate(timeout=1)
                except subprocess.TimeoutExpired as drain_error:
                    stdout, stderr = drain_error.stdout, drain_error.stderr
                row.update(stdout=as_text(stdout), stderr=as_text(stderr),
                           error='Check timed out after ' + str(timeout) + ' seconds')
                return row
        row.update(returncode=proc.returncode, stdout=stdout, stderr=stderr)
        if proc.returncode != 0:
            row['error'] = 'Check exited with status ' + str(proc.returncode)
        elif verdict:
            try:
                value = json.loads(stdout)
                if not isinstance(value, dict) or value.get(verdict) is not True:
                    raise ValueError('Required verdict ' + verdict + ' is not true')
                row['status'] = 'passed'
            except (ValueError, TypeError) as error:
                row['error'] = 'Structured result failed: ' + str(error)
        else:
            row['status'] = 'passed'
    except OSError as error:
        row['error'] = 'Could not run check: ' + str(error)
    return row


def run_checks(root, timeout):
    checks = [run_stage(root, *stage, timeout) for stage in STAGES]
    return dict(schema_version=1, scope=SCOPE,
                all_passed=all(row['status'] == 'passed' for row in checks), checks=checks)


def positive_timeout(value):
    try:
        parsed = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError('timeout must be a finite positive number no greater than 86400 seconds') from error
    if not math.isfinite(parsed) or parsed <= 0 or parsed > 86400:
        raise argparse.ArgumentTypeError('timeout must be a finite positive number no greater than 86400 seconds')
    return parsed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='emit the full machine-readable report to stdout')
    parser.add_argument('--timeout', type=positive_timeout, default=120.0,
                        help='maximum seconds per check, at most 86400 (default: 120)')
    args = parser.parse_args(argv)
    report = run_checks(ROOT, args.timeout)
    if args.json:
        print(json.dumps(report, indent=2, allow_nan=False))
    else:
        for row in report['checks']:
            print(row['status'].upper() + ' ' + row['name'])
            if row['status'] != 'passed':
                print('  ' + row['error'])
                for key in ('stdout', 'stderr'):
                    if row[key]:
                        print('--- ' + key + ' ---\n' + row[key].rstrip())
        print(SCOPE)
        print('The recorded capacity gate remains failed (14/24 truth-complete; 3/24 concept-supported).')
    return 0 if report['all_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
