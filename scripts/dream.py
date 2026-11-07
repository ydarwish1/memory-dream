#!/usr/bin/env python3
"""dream: one dreaming pass, on a COPY of the pool. The live pool is only read.

usage: python3 dream.py POOL OUT --topics topics.json [--findings findings.json] [--date YYYY-MM-DD] [--index MEMORY.md]

OUT must not exist. Steps (all deterministic; the judgement lives in findings.json, which the agent
writes after checking notes against transcripts and one live read-only command):
 1. copy POOL to OUT
 2. move conflict copies and the old index into OUT/_archive-dream-DATE/ (nothing is deleted)
 3. merge duplicates: the shorter copy and older series entries move to the archive; the kept note says so
 4. apply findings: stale -> a dated banner on top; verified -> a dated "Verified" line; rewrite -> new body, old copy archived
 5. mark machine-state notes that carry no marker: "Status: not re-checked since it was written"
 6. repair [[links]] that are one typo away from a real note; list the rest
 7. write one topic page per topic (title, what it is for, checked facts, one line per note)
 8. write a small MEMORY.md: what memory is for, goals, one line per topic page; fail if over budget
Next to OUT it writes OUT.summary.md (read this first), OUT.diff (changed notes; archived files are
listed, not diffed), OUT.report.json, and OUT.base.json (the live pool's checksums, for apply.py)."""
import os
import re
import sys
import json
import shutil
import difflib
import argparse
import datetime
sys.dont_write_bytecode = True  # keep the skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memlib as M


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pool')
    ap.add_argument('out')
    ap.add_argument('--topics', required=True)
    ap.add_argument('--findings')
    ap.add_argument('--date', default=datetime.date.today().isoformat())
    ap.add_argument('--index', default='MEMORY.md')
    a = ap.parse_args()
    pool, out, D, IDX = os.path.abspath(a.pool), os.path.abspath(a.out), a.date, a.index
    if os.path.exists(out):
        print('refusing: %s already exists (use a fresh folder name)' % out)
        return 2
    topics = json.load(open(a.topics))
    findings = M.load_findings(a.findings)
    rep = dict(date=D, archived=[], merged=[], findings_applied=[], marked_not_rechecked=[], links_repaired=[],
               links_left=[], topics={}, conflict_copies=[])
    base = M.manifest(pool)
    old_index = dict((os.path.basename(i['target']), i) for i in M.index_lines(pool, IDX))

    # 1. copy
    shutil.copytree(pool, out, ignore=shutil.ignore_patterns('.git', '.stversions', '.stfolder', '._*', '.DS_Store'))
    arc = os.path.join(out, '_archive-dream-' + D)
    for sub in ('conflicts', 'merged', 'originals'):
        os.makedirs(os.path.join(arc, sub), exist_ok=True)

    def move(rel, sub):
        dst = os.path.join(arc, sub, os.path.basename(rel))
        os.replace(os.path.join(out, rel), dst)
        rep['archived'].append('%s -> %s' % (rel, os.path.relpath(dst, out)))

    # 2. conflict copies, old index
    rep['conflict_differences'] = []
    for rel in M.conflict_copies(out):
        if not rel.startswith('_archive'):
            live_rel = M.CONFLICT_RE.sub('', rel)
            if os.path.exists(os.path.join(out, live_rel)) and live_rel != rel:
                a_ = M.read(os.path.join(out, live_rel)).splitlines()
                b_ = M.read(os.path.join(out, rel)).splitlines()
                d_ = [l for l in difflib.unified_diff(a_, b_, lineterm='', n=0) if l[:1] in '+-' and l[:3] not in ('+++', '---')]
                rep['conflict_differences'].append(dict(copy=rel, live=live_rel, differing_lines=d_[:8], total=len(d_)))
            move(rel, 'conflicts'); rep['conflict_copies'].append(rel)
    if os.path.exists(os.path.join(out, IDX)):
        shutil.copy2(os.path.join(out, IDX), os.path.join(arc, 'originals', IDX[:-3] + '.pre-dream.md'))

    # 3. duplicates and older series entries
    notes = M.load_pool(out, IDX)
    merged_into = {}
    for p in M.duplicate_pairs(notes):
        merged_into.setdefault(p['keep'], []).append(p['duplicate'])
    for old, newest in M.series_old(notes).items():
        merged_into.setdefault(newest, []).append(old)
    done = set()
    for keep, dups in sorted(merged_into.items()):
        dups = [d for d in dups if d not in done and d != keep and os.path.exists(os.path.join(out, d))]
        if not dups or keep in done:
            continue
        for d in dups:
            move(d, 'merged'); done.add(d)
        with open(os.path.join(out, keep), 'a', encoding='utf-8') as f:
            f.write('\n\nMerged on %s: %s (moved to _archive-dream-%s/merged/).\n' % (D, ', '.join(d[:-3] for d in sorted(dups)), D))
        rep['merged'].append(dict(keep=keep, moved=sorted(dups)))
    notes = M.load_pool(out, IDX)

    # 4. findings
    rewritten = {}
    for f, fd in sorted(findings.items()):
        if f not in notes:
            continue
        n = notes[f]
        v = fd.get('verdict')
        if v == 'stale':
            text = n.fm + '\n> **Checked %s: stale.** %s %s\n' % (D, fd.get('evidence', ''), ('Now: ' + fd['now']) if fd.get('now') else '') + n.body
        elif v == 'verified':
            text = n.text.rstrip('\n') + '\n\nVerified %s: %s\n' % (fd.get('date', D), fd.get('check', fd.get('evidence', '')))
        elif v == 'unconfirmed':
            text = n.text.rstrip('\n') + '\n\nUnconfirmed %s: %s\n' % (D, fd.get('evidence', 'no live check and no LIVE transcript line found'))
        elif v == 'rewrite' and fd.get('replacement'):
            shutil.copy2(n.path, os.path.join(arc, 'originals', f))
            new_desc = re.split(r'(?<=[.!?])\s', fd['replacement'].strip(), 1)[0][:150].replace('"', "'")
            fm = re.sub(r'(?m)^description:.*$', lambda m_: 'description: ' + new_desc, n.fm, count=1) if n.fm else n.fm
            rewritten[f] = new_desc
            text = fm + '\n' + fd['replacement'].rstrip('\n') + '\n\nRewritten %s by the dream pass: %s The old text is in _archive-dream-%s/originals/.\n' % (D, fd.get('evidence', ''), D)
        else:
            continue
        open(n.path, 'w', encoding='utf-8').write(text)
        rep['findings_applied'].append('%s: %s' % (f, v))
    notes = M.load_pool(out, IDX)

    # 5. markers on machine-state notes
    for f, n in notes.items():
        if M.EXT_RE.search(n.body) and not M.MARK_RE.search(n.text):
            open(n.path, 'a', encoding='utf-8').write('\nStatus: not re-checked since it was written (dream pass %s).\n' % D)
            rep['marked_not_rechecked'].append(f)
    notes = M.load_pool(out, IDX)

    # 6. links one typo away from a real note
    nmap = M.names_map(out, notes)
    keys = list(nmap)
    for f, n in notes.items():
        def fix(m):
            raw = m.group(1)
            if M.resolve_wiki(raw, nmap):
                return m.group(0)
            cand = difflib.get_close_matches(raw.split('|')[0].strip().lower(), keys, n=1, cutoff=0.86)
            if cand:
                new = nmap[cand[0]][:-3]
                rep['links_repaired'].append('%s: [[%s]] -> [[%s]]' % (f, raw, new))
                return '[[%s]]' % new
            rep['links_left'].append('%s: [[%s]]' % (f, raw))
            return m.group(0)
        t2 = M.LINK_WIKI_RE.sub(fix, n.text)
        if t2 != n.text:
            open(n.path, 'w', encoding='utf-8').write(t2)
    notes = M.load_pool(out, IDX)

    # 7. topic pages
    tlist = list(topics.get('topics', []))
    if not any(t['id'] == 'other' for t in tlist):
        tlist.append(dict(id='other', title='Other notes', purpose='Notes no other topic claimed.', words=[], facts=[]))
    by = dict((t['id'], []) for t in tlist)
    for f, n in notes.items():
        oi = old_index.get(f, {})
        title = oi.get('title') or n.name.replace('-', ' ').replace('_', ' ')
        desc = (oi.get('desc') or n.description or n.body.strip().split('\n')[0])[:220]
        fw, dw = M.words(f[:-3].replace('_', ' ')), M.words(desc)
        best, bs = 'other', 0
        for t in tlist:
            s = 2 * sum(1 for w in fw if w in t.get('words', [])) + sum(1 for w in dw[:40] if w in t.get('words', []))
            if s > bs:
                best, bs = t['id'], s
        stale = ' [checked stale %s]' % D if ('Checked %s: stale' % D) in n.text else ''
        if f in rewritten:
            desc, stale = rewritten[f], ' [rewritten %s]' % D
        by[best].append((f, title, desc, stale))
    os.makedirs(os.path.join(out, 'topics'), exist_ok=True)
    for t in tlist:
        items = sorted(by[t['id']])
        if not items and not t.get('facts'):
            continue
        L = ['# ' + t['title'], '', 'What this page is for: ' + t.get('purpose', ''), '']
        if t.get('facts'):
            L += ['## Current facts (each names its own check and date)', ''] + ['- ' + x for x in t['facts']] + ['']
        L += ['## Notes (%d)' % len(items), '']
        L += ['- [%s](../%s) — %s%s' % (title, f, desc, stale) for f, title, desc, stale in items]
        open(os.path.join(out, 'topics', t['id'] + '.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        rep['topics'][t['id']] = len(items)

    # 8. the index
    I = ['# Memory index', '', '## What this memory is for', '',
         '- To keep what a session worked out and cannot read off the machine again: tested rules, traps, decisions, how to check a thing, and how the user likes to work.',
         '- Live state (ports, versions, deploys, "X is done") changes. A note about it is worth most when it says how and when it was checked.',
         '- Transcripts are the ground truth. When a note and a live check disagree, the live check wins and the note gets fixed.', '']
    if topics.get('goals'):
        I += ['## Current goals', ''] + ['- ' + g for g in topics['goals']] + ['']
    I += ['## Topic pages', '']
    for t in tlist:
        if t['id'] in rep['topics']:
            I.append('- [%s](topics/%s.md) — %s %d notes. Covers: %s.' % (t['title'], t['id'], t.get('purpose', ''), rep['topics'][t['id']],
                                                                       ', '.join(t.get('words', [])[:12]) or 'anything else'))
    I += ['', '## Archive (not read as live notes)', '', '- _archive-dream-%s/: what this pass moved out, and the old index.' % D, '']
    open(os.path.join(out, IDX), 'w', encoding='utf-8').write('\n'.join(I))
    lines, size = M.index_size(out, IDX)
    rep['index'] = dict(lines=lines, bytes=size, in_budget=lines <= M.INDEX_LINE_BUDGET and size <= M.INDEX_BYTE_BUDGET)

    # reports for review and for apply.py
    json.dump(rep, open(out + '.report.json', 'w'), indent=1)
    json.dump(base, open(out + '.base.json', 'w'))
    after = M.manifest(out)
    with open(out + '.diff', 'w', encoding='utf-8') as df:
        for rel in sorted(set(base) | set(after)):
            if base.get(rel) == after.get(rel) or rel.startswith('_archive-dream-'):
                continue  # archived files are listed in the summary, not diffed
            pa, pb = os.path.join(pool, rel), os.path.join(out, rel)
            ta = M.read(pa).splitlines(True) if os.path.exists(pa) and rel.endswith('.md') else []
            tb = M.read(pb).splitlines(True) if os.path.exists(pb) and rel.endswith('.md') else []
            df.writelines(difflib.unified_diff(ta, tb, 'live/' + rel, 'dream/' + rel))
    S = ['# Dream pass %s' % D, '', 'Index: %d lines, %d bytes (%s).' % (lines, size, 'in budget' if rep['index']['in_budget'] else 'OVER BUDGET'), '',
         '## Moved to the archive (%d)' % len(rep['archived']), ''] + ['- ' + x for x in rep['archived']]
    S += ['', '## Findings applied (%d)' % len(rep['findings_applied']), ''] + ['- ' + x for x in rep['findings_applied']]
    S += ['', '## Conflict copies that differ from the live note (decide with the user)', '']
    for c in rep['conflict_differences']:
        S += ['- %s vs %s: %d differing lines' % (c['copy'], c['live'], c['total'])] + ['    ' + l for l in c['differing_lines']]
    S += ['', '## Links', ''] + ['- repaired ' + x for x in rep['links_repaired']] + ['- left for a person ' + x for x in rep['links_left']]
    S += ['', '## Marked "not re-checked" (%d)' % len(rep['marked_not_rechecked']), ''] + ['- ' + x for x in rep['marked_not_rechecked']]
    S += ['', '## Topic pages', ''] + ['- %s: %d notes' % kv for kv in sorted(rep['topics'].items())]
    open(out + '.summary.md', 'w', encoding='utf-8').write('\n'.join(S) + '\n')
    print(json.dumps(dict(index=rep['index'], archived=len(rep['archived']), merged=len(rep['merged']),
                          findings_applied=len(rep['findings_applied']), marked_not_rechecked=len(rep['marked_not_rechecked']),
                          links_repaired=len(rep['links_repaired']), links_left=len(rep['links_left']), topics=rep['topics'])))
    print('review: %s.summary.md (short)  %s.diff (full)  %s.report.json' % (out, out, out))
    return 0 if rep['index']['in_budget'] else 3


if __name__ == '__main__':
    sys.exit(main())
