"""Exhaustive synthetic lookup versus complement; no model invocation."""
import itertools
import json

U = frozenset(range(4))
EXPOSED = frozenset({(0,1),(2,3),(0,2),(1,3)})

def score(known, answer):
    valid = (isinstance(answer, (tuple,list)) and len(answer)==2 and
             all(type(i) is int and i in U for i in answer) and len(set(answer))==2)
    if not valid:
        return False, 0, 0, 0
    hits = len((U - set(known)) & set(answer))
    return True, int(set(answer)==U-set(known)), hits/2, hits-1

def evaluate():
    rows=[]
    table={k:tuple(sorted(U-set(k))) for k in EXPOSED}
    for known in itertools.combinations(range(4),2):
        for policy, answer in [('lookup', table.get(known, (0,1))),
                               ('oracle', tuple(sorted(U-set(known))))]:
            valid, exact, recall, selectivity=score(known,answer)
            rows.append(dict(known=known, policy=policy, answer=answer,
                split='exposed' if known in EXPOSED else 'unexposed',
                valid=valid, exact=exact, recall=recall, selectivity=selectivity))
    return rows

if __name__ == '__main__':
    print(json.dumps(evaluate(), indent=2))
