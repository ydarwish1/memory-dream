#!/usr/bin/env python3
"""score: the eval judge. Runs recall.py on every question and grades it. No model calls.

usage: python3 score.py POOL QUESTIONS.json [--split dev|heldout|all] [--kind transcript|note|all] [--k 3] [--json OUT] [--quiet]

QUESTIONS.json is a list of {id, q, query, keys, split, proof}. "keys" are strings that must ALL
appear in what recall prints; a key may be a list of alternatives. Grades:
  accuracy = share of questions where every key is in the printed lookup
  hit@3    = share where one of the top-3 files holds every key
  tokens   = printed characters / 4 (an estimate; same rule for every run)"""
import os
import sys
import json
import argparse
sys.dont_write_bytecode = True  # keep the skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memlib as M
from recall import recall, render


def has(text, key):
    keys = key if isinstance(key, list) else [key]
    return any(k.lower() in text for k in keys)


def score(pool, questions, split='all', k=3, kind='all'):
    qs = [q for q in questions if (split == 'all' or q.get('split', 'dev') == split)
          and (kind == 'all' or q.get('kind', 'transcript') == kind)]
    files = [f for f in os.listdir(pool) if f.endswith('.md') and not M.is_conflict_copy(f)]
    if os.path.isdir(os.path.join(pool, 'topics')):
        files += ['topics/' + f for f in os.listdir(os.path.join(pool, 'topics')) if f.endswith('.md')]
    bodies = dict((f, M.read(os.path.join(pool, f)).lower()) for f in files)
    rows = []
    for q in qs:
        hits = recall(pool, q['query'], k)
        out = render(hits).lower()
        gold = [f for f in files if all(has(bodies[f], key) for key in q['keys'])]
        top = [h['file'] for h in hits][:3]
        rows.append(dict(id=q['id'], correct=all(has(out, key) for key in q['keys']),
                         hit3=any(t in gold for t in top), tokens=len(out) // 4, top=top))
    n = max(1, len(rows))
    summary = dict(n=len(rows), split=split,
                   accuracy=round(100.0 * sum(r['correct'] for r in rows) / n, 1),
                   hit3=round(100.0 * sum(r['hit3'] for r in rows) / n, 1),
                   tokens_mean=int(round(sum(r['tokens'] for r in rows) / float(n))))
    return summary, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pool')
    ap.add_argument('questions')
    ap.add_argument('--split', default='all', choices=['all', 'dev', 'heldout'])
    ap.add_argument('--kind', default='all', choices=['all', 'transcript', 'note'],
                    help='transcript = proven by a session; note = a regression question proven by a note')
    ap.add_argument('--k', type=int, default=3)
    ap.add_argument('--json')
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    summary, rows = score(a.pool, json.load(open(a.questions)), a.split, a.k, a.kind)
    if a.json:
        json.dump(dict(summary=summary, rows=rows), open(a.json, 'w'), indent=1)
    print(json.dumps(summary))
    if not a.quiet:
        for r in rows:
            print('%s %s %s  top=%s' % ('OK  ' if r['correct'] else 'MISS', 'h3' if r['hit3'] else '--', r['id'], ','.join(r['top'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
