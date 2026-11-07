#!/usr/bin/env python3
"""fixture_judge: grade audit + dream on the shipped fixture against its answer key.

usage: python3 fixture_judge.py FIXTURE_DIR DREAMED_DIR

FIXTURE_DIR holds pool/, answer-key.json and questions.json (see eval/fixture/).
DREAMED_DIR is the output of dream.py run on FIXTURE_DIR/pool.
Prints one line per check and "hits / total". Exit 0 only when every check passes."""
import os
import sys
import json
sys.dont_write_bytecode = True  # keep the skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memlib as M
from audit import audit
from score import score


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    fx, dd = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    key = json.load(open(os.path.join(fx, 'answer-key.json')))
    pool = os.path.join(fx, 'pool')
    a = audit(pool)
    checks = []

    def check(name, ok, detail=''):
        checks.append(ok)
        print('%s %s %s' % ('PASS' if ok else 'FAIL', name, detail))

    # audit must see every planted defect
    check('audit: index over budget', a['index']['over_budget'] == key['index_over_budget'], '(%d lines)' % a['index']['lines'])
    check('audit: conflict copies', sorted(a['conflict_copies']) == sorted(key['conflict_copies']), str(a['conflict_copies']))
    found_dups = set(p['duplicate'] for p in a['duplicates']) | set(a['series_older'])
    for d in key['duplicates']:
        check('audit: duplicate %s' % d['duplicate'], d['duplicate'] in found_dups)
    for s in key['series_older']:
        check('audit: older series entry %s' % s, s in found_dups)
    bl = set((b['note'], b['link']) for b in a['broken_links'])
    for b in key['broken_links_fixable'] + key['broken_links_unfixable']:
        check('audit: broken link %s in %s' % (b['link'], b['note']), (b['note'], b['link']) in bl)
    check('audit: orphans', sorted(a['orphans']) == sorted(key['orphans']), str(a['orphans']))
    um = set(a['external_state_unmarked']) - found_dups  # duplicates leave the pool, so they need no marker
    check('audit: unmarked machine-state notes', um == set(key['state_unmarked']),
          'missing %s extra %s' % (sorted(set(key['state_unmarked']) - um), sorted(um - set(key['state_unmarked']))))

    # dream output
    lines, size = M.index_size(dd)
    check('dream: index in budget', lines <= M.INDEX_LINE_BUDGET and size <= M.INDEX_BYTE_BUDGET, '(%d lines, %d bytes)' % (lines, size))
    check('dream: conflict copies moved out', not M.conflict_copies(dd))
    for d in key['duplicates']:
        check('dream: duplicate merged %s' % d['duplicate'], not os.path.exists(os.path.join(dd, d['duplicate'])) and os.path.exists(os.path.join(dd, d['keep'])))
    for s in key['series_older']:
        check('dream: older series entry archived %s' % s, not os.path.exists(os.path.join(dd, s)))
    for c in key['contradicted']:
        t = M.read(os.path.join(dd, c['note'])) if os.path.exists(os.path.join(dd, c['note'])) else ''
        check('dream: contradicted note fixed %s' % c['note'], ': stale.**' in t or 'Rewritten ' in t)
    for b in key['broken_links_fixable']:
        t = M.read(os.path.join(dd, b['note']))
        check('dream: link repaired %s' % b['link'], b['link'] not in t and ('[[%s]]' % b['to']) in t)
    for b in key['broken_links_unfixable']:
        t = M.read(os.path.join(dd, b['note']))
        check('dream: unfixable link left for a person %s' % b['link'], b['link'] in t)
    for f in key['state_unmarked']:
        p = os.path.join(dd, f)
        check('dream: marker on %s' % f, os.path.exists(p) and bool(M.MARK_RE.search(M.read(p))))
    for f in key['good_notes_unchanged']:
        check('dream: good note unchanged %s' % f, M.md5(os.path.join(pool, f)) == M.md5(os.path.join(dd, f)))
    linked = set()
    for tf in os.listdir(os.path.join(dd, 'topics')):
        linked |= set(os.path.basename(i['target']) for i in M.index_lines(os.path.join(dd, 'topics'), tf))
    live = M.load_pool(dd)
    check('dream: every live note is on a topic page', set(live) <= linked, str(sorted(set(live) - linked)))

    qs = json.load(open(os.path.join(fx, 'questions.json')))
    for split in ('dev', 'heldout'):
        b, _ = score(pool, qs, split)
        d, _ = score(dd, qs, split)
        print('eval %-7s before acc %5.1f hit3 %5.1f tok %4d  ->  after acc %5.1f hit3 %5.1f tok %4d' % (
            split, b['accuracy'], b['hit3'], b['tokens_mean'], d['accuracy'], d['hit3'], d['tokens_mean']))
    print('fixture judge: %d / %d checks pass' % (sum(checks), len(checks)))
    return 0 if all(checks) else 1


if __name__ == '__main__':
    sys.exit(main())
