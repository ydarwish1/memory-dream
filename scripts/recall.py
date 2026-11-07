#!/usr/bin/env python3
"""recall: a cheap, deterministic, index-first lookup over a memory pool. No model calls.

usage: python3 recall.py POOL "question words" [--k 3] [--index MEMORY.md]

It plays the part of an agent that reads the index first, then opens the best few files.
Pointer lines come from the index AND the topic pages (topics/*.md): a link line points at its
note, a plain "- fact" line points at the topic page. File names score too. The top k files are
opened; a note prints a window around its best line, a topic page prints its 5 best lines.
The eval scorer uses this same lookup, so a better-organised pool scores higher."""
import os
import re
import sys
import argparse
sys.dont_write_bytecode = True  # keep the skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memlib as M


def _score(qw, lw):
    s = 0
    for w in qw:
        if w in lw:
            s += 3
        elif any(x.startswith(w) or w.startswith(x) for x in lw):
            s += 1
    return s


def recall(pool, query, k=3, index='MEMORY.md'):
    qw = M.words(query)
    qraw = M.words(query, keep_stop=True)
    ptr = []
    hub = os.path.join(pool, index)
    if os.path.exists(hub):
        for line in M.read(hub).splitlines():
            m = re.search(r'\[([^\]]+)\]\(([^)]+)\)', line)
            if m:
                s = _score(qw, M.words(line))
                if s:
                    ptr.append((s, os.path.normpath(os.path.join(pool, m.group(2)))))
    tdir = os.path.join(pool, 'topics')
    if os.path.isdir(tdir):
        for tf in sorted(os.listdir(tdir)):
            if not tf.endswith('.md'):
                continue
            tp = os.path.join(tdir, tf)
            body = M.read(tp)
            tm = re.search(r'^# (.*)$', body, re.M)
            title = tm.group(1) if tm else ''
            for line in body.splitlines():
                m = re.search(r'\[([^\]]+)\]\(([^)]+)\)', line)
                if not m and not line.startswith('- '):
                    continue
                s = _score(qw, M.words(line if m else line + ' ' + title))
                if s:
                    ptr.append((s, os.path.normpath(os.path.join(tdir, m.group(2))) if m else tp))
    for f in os.listdir(pool):
        if f.endswith('.md') and f != index and not M.is_conflict_copy(f):
            fw = M.words(f[:-3].replace('_', ' '))
            s = sum(4 if w in fw else (1 if any(w in x or x in w for x in fw) else 0) for w in qw)
            if s:
                ptr.append((s, os.path.join(pool, f)))
    ptr.sort(key=lambda t: -t[0])
    seen, top = set(), []
    for s, p in ptr:
        if p in seen or not os.path.exists(p):
            continue
        seen.add(p)
        top.append((s, p))
        if len(top) >= k:
            break
    hits = []
    for s, p in top:
        body = M.read(p)
        is_topic = os.path.basename(os.path.dirname(p)) == 'topics'
        hits.append(dict(file=os.path.relpath(p, pool), score=s, slice=_topic_slice(body, qw) if is_topic else _slice(body, qw, qraw)))
    return hits


def _slice(body, qw, qraw):
    lines = body.split('\n')
    best_h, h_at = 0, -1
    for i, line in enumerate(lines):
        if re.match(r'^#{2,4}\s', line):
            s = len([w for w in qraw if w in M.words(line, keep_stop=True)])
            if s > best_h:
                best_h, h_at = s, i
    if h_at >= 0:
        return '\n'.join(lines[h_at:h_at + 26])
    best_i, best_s = 0, -1
    for i, line in enumerate(lines):
        low = line.lower()
        s = sum(1 for w in qw if w in low)
        if s > best_s:
            best_s, best_i = s, i
    return '\n'.join(lines[max(0, best_i - 10):best_i + 16])


def _topic_slice(body, qw):
    lines = body.split('\n')
    title = lines[0][2:] if lines and lines[0].startswith('# ') else ''
    scored = []
    for i, line in enumerate(lines):
        if not line.startswith('- '):
            continue
        is_link = '](' in line
        s = _score(qw, M.words(line if is_link else line + ' ' + title))
        if s:
            scored.append((-s, i))
    keep = sorted(i for _, i in sorted(scored)[:5])
    out = [lines[0]] if lines else []
    for i in keep:
        l = lines[i]
        out.append(l[:197] + '...' if '](' in l and len(l) > 200 else l)
    return '\n'.join(out)


def render(hits):
    return ''.join('\n=== %s  (score %d)\n%s\n' % (h['file'], h['score'], h['slice']) for h in hits)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pool')
    ap.add_argument('query', nargs='+')
    ap.add_argument('--k', type=int, default=3)
    ap.add_argument('--index', default='MEMORY.md')
    a = ap.parse_args()
    print(render(recall(a.pool, ' '.join(a.query), a.k, a.index)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
