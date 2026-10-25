"""Offline NumPy/tooling/audit checks by default; pretrained tests are explicit."""
import argparse,hashlib,os,stat,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Published at 83a1809fd9ada5704b5f40294de2d46eb3bf3136. These are release
# identity pins, not a new freeze, semantic re-evaluation or runtime attestation.
AUDIT_MANIFEST_SHA256 = 'ed880344b01b7a7c42da62c1ef4323278d4fd71696c85b9599523205a466be62'
AUDIT_VERIFIER_SHA256 = 'f376fc946df19497f93f4e7116c7da21f49e4c478ab825ec35fea20ed3e85d27'


def suites(pretrained):
    selected=[('tests','src'),('tooling/tests','pretrained:tooling')]
    if pretrained:selected.append(('pretrained/tests','pretrained'))
    return selected


def read_release_file(path):
    """Reject special files before open and bound reads of release metadata."""
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError('Reader audit requires a regular file, not a symlink or special file: ' + str(path))
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0)
    flags |= getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(path, flags), 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Reader audit requires a regular file: ' + str(path))
        data = stream.read(65537)
    if len(data) > 65536:
        raise ValueError('Reader audit release metadata exceeds the 64 KiB limit: ' + str(path))
    return data


def run_reader_audit():
    """Check the published evidence and its tests without changing the release."""
    study = ROOT / 'studies/reader-answerability-audit'
    # Authenticate the entrypoint before executing it; an adjacent manifest and
    # seal alone would allow a changed package to claim a new consistent hash.
    for filename, expected, label in (
        ('PUBLIC_MANIFEST.json', AUDIT_MANIFEST_SHA256, 'published manifest'),
        ('verify_public.py', AUDIT_VERIFIER_SHA256, 'published verifier'),
    ):
        if hashlib.sha256(read_release_file(study / filename)).hexdigest() != expected:
            raise ValueError('Reader audit does not match the ' + label + ': ' + filename)
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    python = [sys.executable, '-I', '-S', '-B']
    subprocess.run(python + [str(study / 'verify_public.py'),
                            '--expected-manifest-sha256', AUDIT_MANIFEST_SHA256],
                   cwd=ROOT, env=env, check=True)
    subprocess.run(python + ['-m', 'unittest', 'discover', '-s', str(study / 'tests'), '-v'],
                   cwd=ROOT, env=env, check=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pretrained',action='store_true')
    p.add_argument('--reader-audit-only', action='store_true',
                   help='verify the sealed audit and run its tests using only the standard library')
    p.add_argument('--model-dir',type=Path);a=p.parse_args()
    if a.reader_audit_only and (a.pretrained or a.model_dir):
        p.error('--reader-audit-only cannot be combined with --pretrained or --model-dir')
    if a.pretrained and not a.model_dir:p.error('--pretrained requires --model-dir; see pretrained/README.md for optional dependencies and model fetch')
    try:
        run_reader_audit()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print('Reader audit verification failed: ' + str(error), file=sys.stderr)
        return 1
    if a.reader_audit_only:
        return 0
    env=dict(os.environ);env.setdefault('OPENBLAS_NUM_THREADS','1')
    if a.model_dir:env['MODEL_DIR']=str(a.model_dir.resolve())
    if a.pretrained:
        import importlib.util
        missing=[m for m in ['torch','transformers','peft','safetensors'] if importlib.util.find_spec(m) is None]
        if missing:p.error('Missing optional dependencies: '+', '.join(missing)+'; see pretrained/README.md')
        sys.path.insert(0,str(ROOT/'pretrained'));import fetch_model,json
        fetch_model.fetch(json.loads((ROOT/'pretrained/model_manifest.json').read_text()),env['MODEL_DIR'],verify_only=True)
    for folder,paths in suites(a.pretrained):
        env['PYTHONPATH']=os.pathsep.join(str(ROOT/q) for q in paths.split(':'))
        subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',folder,'-v'],cwd=ROOT,env=env,check=True)
    if not a.pretrained:print('Pretrained suite not requested. Use --pretrained --model-dir PATH for all suites.')


if __name__=='__main__':raise SystemExit(main())
