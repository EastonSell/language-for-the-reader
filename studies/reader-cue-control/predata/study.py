"""Offline cue-control preparation and analysis; never calls an evaluator."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

VARIANTS = ('literal', 'paraphrase', 'corrupted', 'empty')
CUES = ('absent', 'relevant', 'unrelated')
DECISIONS = ('supported', 'not_supported', 'uncertain')
SEED = 'reader-cue-control-20261025-v1'
INSTRUCTION = '''Evaluate the 12 independent preservation tasks below.
Use only each task's passage as factual evidence. The claim is the entire proposition
whose preservation you must assess; its presence is not evidence for its own truth.
The optional question_cue may focus on part of the passage or be unrelated. Do not
answer it. Do not use it as factual evidence. It does not change the preservation task.
Do not use tools, browse, read files, consult other agents, or use outside facts.
For every case decide:
supported = the passage entails the ENTIRE claim, including every participant,
restriction, quantity, location, condition, time, order, unit and negation;
not_supported = any part is absent, contradicted or otherwise not established;
uncertain = you cannot resolve the entailment.
An empty passage supplies no facts. Evaluate each task independently.
Return ONLY one JSON array with exactly one object per case and exactly these fields:
case_id: copy the ID;
decision: supported, not_supported, or uncertain;
evidence: a list of exact, contiguous, nonempty quotes from THIS passage, or [];
rationale: a nonempty explanation of at most 60 whitespace-separated words.
A supported decision requires at least one passage quote. Do not quote the claim
or question_cue as passage evidence. Do not add fields, Markdown, or commentary.

TASKS:
'''


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'duplicate JSON object key')
        value[key] = item
    return value


def strict_json(text):
    return json.loads(text, object_pairs_hook=_pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON value')))


def build(fixtures):
    fields = {'source_id', 'kind', 'claim', 'paraphrase', 'corrupted',
              'relevant_cue', 'unrelated_cue', 'corruption_reason'}
    require(type(fixtures) is list and len(fixtures) == 12, 'exactly 12 sources required')
    seen = set()
    for f in fixtures:
        require(type(f) is dict and set(f) == fields, 'invalid fixture fields')
        require(all(type(v) is str and v.strip() for v in f.values()), 'fixture text required')
        require(re.fullmatch('[a-z_]+', f['source_id']) is not None, 'invalid source ID')
        require(f['source_id'] not in seen, 'duplicate source ID')
        seen.add(f['source_id'])
        require(len(f['relevant_cue'].split()) == len(f['unrelated_cue'].split()), 'cue word counts differ')
        require(f['relevant_cue'] != f['unrelated_cue'], 'cue texts identical')
        require(len({f['claim'], f['paraphrase'], f['corrupted']}) == 3, 'passage variants identical')
    conditions = [(v, c) for v in VARIANTS for c in CUES]
    packets, key = [], []
    for b in range(12):
        block = 'B%02d' % (b + 1)
        cases = []
        for i, f in enumerate(fixtures):
            variant, cue = conditions[(i + b) % 12]
            passage = {'literal':f['claim'], 'paraphrase':f['paraphrase'],
                       'corrupted':f['corrupted'], 'empty':''}[variant]
            question = '' if cue == 'absent' else f[cue + '_cue']
            case_id = 'C' + sha((SEED + '|' + f['source_id'] + '|' + variant + '|' + cue).encode())[:20]
            cases.append({'case_id':case_id, 'claim':f['claim'], 'passage':passage, 'question_cue':question})
            key.append({'block_id':block, 'case_id':case_id, 'source_id':f['source_id'],
                        'variant':variant, 'cue':cue, 'gold_support':variant in ('literal','paraphrase')})
        cases.sort(key=lambda c:sha((SEED + '|' + block + '|' + c['case_id']).encode()))
        packets.append({'block_id':block, 'cases':cases})
    key.sort(key=lambda k:k['case_id'])
    return {'packets':packets, 'key':key}


def prompt(packet):
    return INSTRUCTION + json.dumps(packet['cases'], indent=2, ensure_ascii=False) + '\n'


def parse_responses(raw, cases):
    """All-or-none packet admission. Never repairs or drops individual responses."""
    try:
        require(type(raw) is str and len(raw.encode()) <= 262144, 'raw response exceeds 256 KiB or is not text')
        parsed = strict_json(raw)
        require(type(parsed) is list and len(parsed) == len(cases), 'packet response count mismatch')
        expected = {c['case_id']:c for c in cases}
        require(len(expected) == len(cases), 'duplicate expected case')
        seen = set()
        for r in parsed:
            require(type(r) is dict and set(r) == {'case_id','decision','evidence','rationale'}, 'invalid response fields')
            require(type(r['case_id']) is str and r['case_id'] in expected, 'unknown case ID')
            require(r['case_id'] not in seen, 'duplicate response ID')
            seen.add(r['case_id'])
            require(type(r['decision']) is str and r['decision'] in DECISIONS, 'invalid decision')
            require(type(r['rationale']) is str and 0 < len(r['rationale'].split()) <= 60, 'invalid rationale')
            quotes = r['evidence']
            require(type(quotes) is list and len(quotes) <= 8, 'invalid evidence list')
            require(len(set(q for q in quotes if type(q) is str)) == len(quotes), 'duplicate or nontext evidence')
            for q in quotes:
                require(type(q) is str and q.strip() and q in expected[r['case_id']]['passage'], 'quote is not passage evidence')
            require(r['decision'] != 'supported' or len(quotes) > 0, 'supported response lacks evidence')
        require(seen == set(expected), 'missing response IDs')
        return {'responses':parsed, 'issues':[]}
    except (ValueError, TypeError, KeyError, UnicodeError) as e:
        return {'responses':[], 'issues':[str(e)]}


def validate_key(key):
    require(type(key) is list and len(key) == 144, 'fixed denominator must be 144')
    fields = {'block_id','case_id','source_id','variant','cue','gold_support'}
    require(all(type(k) is dict and set(k) == fields for k in key), 'invalid key schema')
    require(all(type(k[x]) is str for k in key for x in fields - {'gold_support'}), 'invalid key text')
    require(all(type(k['gold_support']) is bool and k['gold_support'] == (k['variant'] in ('literal','paraphrase')) for k in key), 'incorrect gold support')
    require(all(k['variant'] in VARIANTS and k['cue'] in CUES for k in key), 'unknown condition')
    require(len({k['case_id'] for k in key}) == 144, 'duplicate key case ID')
    sources = {k['source_id'] for k in key}
    require(len(sources) == 12, 'source denominator changed')
    expected = {(s,v,c) for s in sources for v in VARIANTS for c in CUES}
    require({(k['source_id'],k['variant'],k['cue']) for k in key} == expected, 'condition grid incomplete')
    require({k['block_id'] for k in key} == {'B%02d'%i for i in range(1,13)}, 'block denominator changed')
    for block in {k['block_id'] for k in key}:
        rows = [k for k in key if k['block_id'] == block]
        require(len(rows) == 12 and len({k['source_id'] for k in rows}) == 12 and
                len({(k['variant'],k['cue']) for k in rows}) == 12, 'block balance changed')


def analyze(key, responses):
    """Summarize already admitted responses. CLI performs raw/receipt admission."""
    validate_key(key)
    require(type(responses) is list, 'response list required')
    ids = {k['case_id'] for k in key}
    observed = {}
    for r in responses:
        require(type(r) is dict and type(r.get('case_id')) is str and r['case_id'] in ids, 'unknown response case')
        require(r['case_id'] not in observed, 'duplicate response ID')
        require(type(r.get('decision')) is str and r['decision'] in DECISIONS, 'invalid admitted decision')
        observed[r['case_id']] = r['decision']
    complete = len(observed) == 144
    cells = []
    for v in VARIANTS:
        for c in CUES:
            rows = [k for k in key if k['variant']==v and k['cue']==c]
            decisions = [observed[k['case_id']] for k in rows if k['case_id'] in observed]
            counts = Counter(decisions)
            missing = 12-len(decisions)
            cells.append({'variant':v, 'cue':c, 'denominator':12, 'valid':len(decisions),
                          'missing_or_invalid':missing, 'positive':counts['supported'],
                          'uncertain':counts['uncertain'], 'negative':counts['not_supported'],
                          'positive_rate_bounds':[counts['supported']/12, (counts['supported']+missing)/12]})
    indexed = {(k['source_id'],k['variant'],k['cue']):k for k in key}
    paired = []
    for source in sorted({k['source_id'] for k in key}):
        ds = {}
        for c in CUES:
            decision = observed.get(indexed[source,'corrupted',c]['case_id'])
            ds[c] = None if decision is None else int(decision=='supported')
        a,b = ds['relevant'],ds['unrelated']
        lo=(0 if a is None else a)-(1 if b is None else b)
        hi=(1 if a is None else a)-(0 if b is None else b)
        paired.append({'source_id':source, **ds, 'relevant_minus_unrelated_bounds':[lo,hi]})
    bounds=[sum(p['relevant_minus_unrelated_bounds'][j] for p in paired)/12 for j in (0,1)]
    return {'expected_cases':144, 'valid_cases':len(observed), 'response_complete':complete,
            'uncertain':sum(v=='uncertain' for v in observed.values()), 'cells':cells,
            'primary':{'contrast':'corrupted relevant minus unrelated positive-support rate',
                       'source_denominator':12, 'difference_bounds':bounds,
                       'point_difference':bounds[0] if complete else None,
                       'per_source':paired},
            'scope':'Descriptive fixed-stimulus contrast only; no p-value, population confidence interval, human benefit or learned-reader claim.'}


def prepare(root):
    root=Path(root)
    plan=build(strict_json((root/'study/fixtures.json').read_text()))
    target=root/'prepared'
    target.mkdir(exist_ok=False)
    (target/'packets.json').write_bytes(encoded(plan['packets']))
    (target/'gold-key.json').write_bytes(encoded(plan['key']))
    for p in plan['packets']:
        (target/(p['block_id']+'.prompt.txt')).write_text(prompt(p), encoding='utf-8')
    return plan


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    args=parser.parse_args()
    if args.prepare:
        plan=prepare(args.root)
        print(json.dumps({'prepared_cases':len(plan['key']), 'blocks':len(plan['packets']), 'empirical_judgments':0}))
    else:
        parser.error('choose --prepare; no evaluator dispatch exists in this program')
