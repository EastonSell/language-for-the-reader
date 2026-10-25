"""Offline preparation freeze and custody checks. Never invokes an evaluator."""
import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import stat
import study


def read_regular(path, maximum=1048576):
    path=Path(path)
    study.require(not path.is_symlink(), 'symlink input rejected')
    flags=os.O_RDONLY | getattr(os,'O_NOFOLLOW',0) | getattr(os,'O_NONBLOCK',0)
    fd=os.open(path,flags)
    try:
        meta=os.fstat(fd)
        study.require(stat.S_ISREG(meta.st_mode) and meta.st_size <= maximum, 'nonregular or oversized input')
        with os.fdopen(fd,'rb',closefd=False) as f: data=f.read(maximum+1)
        study.require(len(data) <= maximum, 'oversized input')
        return data
    finally:
        os.close(fd)


def inventory(root):
    root=Path(root)
    study.require(root.is_dir() and not root.is_symlink(), 'regular root directory required')
    files={}
    for path in sorted(root.rglob('*')):
        relative=path.relative_to(root)
        if '__pycache__' in relative.parts or '.git' in relative.parts:
            continue
        if relative.as_posix()=='FREEZE.json':
            continue
        study.require(not path.is_symlink(), 'symlink payload rejected')
        if path.is_dir():
            continue
        files[relative.as_posix()]=study.sha(read_regular(path))
    study.require(files, 'empty package')
    return files


def freeze(root):
    root=Path(root)
    value={'schema':1,'study':'reader-cue-control-20261025-v1','expected_cases':144,
           'expected_contexts':12,'empirical_judgments_at_freeze':0,
           'scope':'Local pre-data content identity, not execution clearance or independent timestamp proof.',
           'files':inventory(root)}
    with (root/'FREEZE.json').open('xb') as f:
        f.write(study.encoded(value))
    return value


def verify_freeze(root):
    root=Path(root)
    value=study.strict_json(read_regular(root/'FREEZE.json').decode())
    study.require(type(value) is dict and value.get('schema')==1 and
                  value.get('study')=='reader-cue-control-20261025-v1' and
                  value.get('expected_cases')==144 and value.get('expected_contexts')==12 and
                  value.get('empirical_judgments_at_freeze')==0, 'invalid freeze header')
    study.require(value.get('files')==inventory(root), 'frozen payload inventory or bytes differ')
    return value


def validate_receipts(receipts, packets, raw_by_block, prompts):
    try:
        fields={'block_id','context_id','prompt_sha256','raw_sha256','started_utc','completed_utc',
                'history_disabled','requested_reasoning_effort','requested_model','resolved_model',
                'tool_audit','tool_calls_observed','known_tool_use','known_contamination','capture'}
        expected={p['block_id'] for p in packets}
        study.require(expected=={'B%02d'%i for i in range(1,13)}, 'twelve expected blocks required')
        study.require(type(receipts) is list and len(receipts)==12, 'exactly twelve receipts required')
        contexts=set(); blocks=set(); starts=[]; ends=[]
        for r in receipts:
            study.require(type(r) is dict and set(r)==fields, 'invalid receipt fields')
            b=r['block_id']
            study.require(type(b) is str and b in expected and b not in blocks, 'unknown or duplicate block')
            blocks.add(b)
            c=r['context_id']
            study.require(type(c) is str and c.strip() and c not in contexts, 'missing or duplicate context identity')
            contexts.add(c)
            study.require(type(raw_by_block.get(b)) is bytes and type(prompts.get(b)) is bytes, 'missing raw payload or prompt')
            study.require(r['prompt_sha256']==study.sha(prompts[b]), 'prompt hash mismatch')
            study.require(r['raw_sha256']==study.sha(raw_by_block[b]), 'raw hash mismatch')
            study.require(r['history_disabled'] is True and r['requested_reasoning_effort']=='xhigh' and
                          r['requested_model']=='inherited', 'requested context configuration differs')
            study.require(r['resolved_model'] is None or (type(r['resolved_model']) is str and r['resolved_model'].strip()), 'invalid resolved model disclosure')
            study.require(r['known_tool_use'] is False and r['known_contamination'] is False, 'known tool use or contamination')
            study.require(r['tool_audit']=='not_exposed' and r['tool_calls_observed'] is None, 'unverified tool traces must remain unknown')
            study.require(r['capture']=='visible_final_answer_utf8_no_added_newline', 'raw capture convention differs')
            times=[]
            for field in ('started_utc','completed_utc'):
                study.require(type(r[field]) is str, 'timestamp must be text')
                t=datetime.fromisoformat(r[field].replace('Z','+00:00'))
                study.require(t.tzinfo is not None and t.utcoffset()==timedelta(0), 'timestamp must explicitly use UTC')
                times.append(t)
            study.require(times[0]<=times[1], 'completion precedes start')
            starts.append(times[0]); ends.append(times[1])
        study.require(blocks==expected, 'receipt block coverage differs')
        study.require((max(ends)-min(starts)).total_seconds()<=2700, '45-minute global capture window exceeded')
        return []
    except (ValueError,KeyError,TypeError) as e:
        return [str(e)]


def verify_preparation(root):
    root=Path(root)
    freeze_value=verify_freeze(root)
    plan=study.build(study.strict_json(read_regular(root/'study/fixtures.json').decode()))
    for name,value in [('packets.json',plan['packets']),('gold-key.json',plan['key'])]:
        study.require(read_regular(root/'prepared'/name)==study.encoded(value), 'prepared data does not match deterministic construction')
    for p in plan['packets']:
        study.require(read_regular(root/'prepared'/(p['block_id']+'.prompt.txt'))==study.prompt(p).encode(), 'prepared prompt differs')
    return plan,freeze_value


def analyze_run(root, run):
    root,run=Path(root),Path(run)
    plan,_=verify_preparation(root)
    raw={}; raw_issues=[]
    prompts={p['block_id']:read_regular(root/'prepared'/(p['block_id']+'.prompt.txt')) for p in plan['packets']}
    for p in plan['packets']:
        b=p['block_id']
        try:
            raw[b]=read_regular(run/(b+'.raw.txt'),262144)
        except (OSError,ValueError) as e:
            raw_issues.append({'block_id':b,'issue':str(e)})
    try:
        receipts=study.strict_json(read_regular(run/'receipts.json').decode())
        custody_issues=validate_receipts(receipts,plan['packets'],raw,prompts)
    except (OSError,ValueError,UnicodeError) as e:
        custody_issues=[str(e)]
    responses=[]; packet_issues=[]
    if not custody_issues:
        for p in plan['packets']:
            b=p['block_id']
            try:
                parsed=study.parse_responses(raw[b].decode('utf-8'),p['cases'])
            except UnicodeError as e:
                parsed={'responses':[],'issues':[str(e)]}
            if parsed['issues']:
                packet_issues.append({'block_id':b,'issues':parsed['issues']})
            responses.extend(parsed['responses'])
    result=study.analyze(plan['key'],responses)
    result.update(custody_issues=custody_issues,raw_issues=raw_issues,packet_issues=packet_issues,
                  operational_complete=not custody_issues and not raw_issues and not packet_issues and result['response_complete'],
                  freeze_sha256=study.sha(read_regular(root/'FREEZE.json')),
                  tool_trace_disclosure='Not exposed; no verified claim of zero tool use or hard isolation.',
                  result_kind='Captured AI judgments, subject to independent postrun semantic and custody review.')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--freeze',action='store_true')
    group.add_argument('--verify',action='store_true')
    group.add_argument('--analyze-run',type=Path)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    args=p.parse_args()
    if args.freeze:
        value=freeze(args.root)
        print(json.dumps({'frozen_files':len(value['files']),'empirical_judgments':0}))
    elif args.verify:
        plan,value=verify_preparation(args.root)
        print(json.dumps({'status':'preparation-consistent','cases':len(plan['key']),'files':len(value['files']),'execution_clearance':False}))
    else:
        print(json.dumps(analyze_run(args.root,args.analyze_run),indent=2,allow_nan=False))
