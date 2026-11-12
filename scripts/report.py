#!/usr/bin/env python3
"""Turn an audit into one interactive HTML page: a map of the memory, every note as a square,
a map of the broken links, and a fix cart that writes one prompt for a dream pass.

    python3 report.py POOL [--transcripts DIR] [--extras extras.json] --out report.html

The page is one self-contained file (no scripts from other sites; fonts load from Google Fonts
when online and fall back to system fonts offline). Open it in a browser, or publish it anywhere
that serves a plain HTML file. It reads the live pool and writes only the --out file.

--extras (optional JSON, format in references/formats.md):
  machines   the machines that share the pool, each {name, status ok|warn|bad|unknown, detail, good[], issues[]}
  links      your verdicts on broken links, keyed "note.md -> [[target]]": {verdict: false|missing|renamed|archived, why}
  fixes      extra fix items for the cart: {label, text}
"""
import argparse
import datetime
import difflib
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memlib as M  # noqa: E402
import audit as A  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def norm(s):
    s = s.strip('[]()').split('|')[0].strip().lower()
    if s.endswith('.md'):
        s = s[:-3]
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def archived_names(pool):
    out = {}
    for d in sorted(os.listdir(pool)):
        p = os.path.join(pool, d)
        if d.startswith('_archive') and os.path.isdir(p):
            for dp, _, fn in os.walk(p):
                for f in fn:
                    if f.endswith('.md'):
                        out.setdefault(norm(f), os.path.relpath(os.path.join(dp, f), pool))
    return out


def classify_link(target, live, archived):
    """Return (category, suggestion). live: {norm(stem): file}."""
    k = norm(target)
    if not k:
        return 'missing', None
    if k in archived:
        return 'archived', archived[k]
    starts = sorted(set(f for n, f in live.items() if n.startswith(k + '-') or n.endswith('-' + k))) if len(k) >= 6 else []
    if 1 <= len(starts) <= 3:
        return 'renamed', starts
    close = sorted(set(live[c] for c in difflib.get_close_matches(k, list(live), n=3, cutoff=0.85)))
    if close:
        return 'renamed', close[:2]
    return 'missing', None


def build(pool, transcripts=None, extras=None, findings=None, index='MEMORY.md', label=None):
    rep = A.audit(pool, index, findings, transcripts)
    notes = M.load_pool(pool, index)
    ex = extras or {}
    judged = ex.get('links', {})
    reads = rep.get('reads', {})
    live = {}
    for f, n in notes.items():  # match a link against the file name, the name without its type word, and the frontmatter name
        for k in (norm(f), re.sub(r'^(feedback|project|reference|user)-', '', norm(f)), norm(n.name or '')):
            if k:
                live.setdefault(k, f)
    arch = archived_names(pool)
    fixes = {}

    links = []
    for i, b in enumerate(rep['broken_links']):
        s, t = b['note'], b['link']
        cat, sug = classify_link(t, live, arch)
        why = None
        j = judged.get('%s -> %s' % (s, t))
        if j:
            cat, why = j.get('verdict', cat), j.get('why')
        if cat == 'false':
            why = 'Not a real link%s. Link checks flag it anyway.' % (': ' + why if why else '')
            fix = 'In %s: put %s in backticks so link checks stop flagging it (optional).' % (s, t)
            short = t + '  (not a link)'
        elif cat == 'renamed':
            names = ' or '.join(x[:-3] for x in sug) if sug else 'the right note'
            why = why or 'The target looks renamed or misspelled. Close match: %s.' % names
            fix = 'In %s: change %s to [[%s]] if that is the note it means.' % (s, t, names)
            short = '%s  →  %s' % (t, names)
        elif cat == 'archived':
            why = why or 'The target is in %s, so it is not a live note.' % (os.path.dirname(sug) if sug else 'an archive folder')
            fix = 'In %s: %s points at an archived note. Drop the link or say in the text that it is retired.' % (s, t)
            short = norm(t) + '  (archived)'
        else:
            cat = 'missing'
            why = why or 'No note with this name exists in the pool or in any archive folder.'
            fix = 'In %s: remove the link %s or point it at the note that holds that fact now.' % (s, t)
            short = t
        fid = 'link:%d' % i
        fixes[fid] = dict(label=('Quiet false alarm ' if cat == 'false' else 'Fix link ') + t, text=fix)
        links.append(dict(src=s, tgt=t, cat=cat, why=why, short=short, m=reads.get(s, 0)))

    dup_of = dict((p['duplicate'], p['keep']) for p in rep['duplicates'])
    older = rep['series_older']
    contra = dict((f, rep['reason_of'][f]) for f, c in rep['class_of'].items() if c == 'contradicted')
    ext = set(rep['external_state_unmarked'])
    unmarked = sorted(f for f, c in rep['class_of'].items() if c == 'state' and not M.MARK_RE.search(notes[f].text))
    for f, k in dup_of.items():
        fixes['dup:' + f] = dict(label='Merge ' + f, text='Merge %s into %s, then archive the copy.' % (f, k))
    for f, k in older.items():
        fixes['old:' + f] = dict(label='Archive ' + f, text='Archive %s. %s is the newer entry in the same series.' % (f, k))
    for f, why in contra.items():
        fixes['con:' + f] = dict(label='Settle ' + f, text='%s is %s. Check which note is right, move any fact the other lacks, then archive or fix it.' % (f, why))
    for f in unmarked:
        fixes['re:' + f] = dict(label='Re-check ' + f, text='Re-check %s with one live command or a LIVE transcript line, then mark it verified or stale.%s' % (
            f, ' It names a machine or a service.' if f in ext else ''))
    for c in rep['conflict_copies']:
        fixes['cc:' + c] = dict(label='Resolve ' + c, text='Compare the conflict copy %s with its live note, keep the right text, and archive the copy.' % c)
    for f in rep['orphans']:
        fixes['orph:' + f] = dict(label='Link ' + f, text='Nothing links to %s. Add it to the index or a topic page, or archive it if it is no longer useful.' % f)
    lo = rep.get('sync_leftovers') or {}  # {folder: file count}, e.g. {'.stversions': 88}
    leftovers = sum(lo.values())
    if leftovers:
        where = ', '.join('%s (%d)' % (d, c) for d, c in sorted(lo.items()))
        fixes['leftovers'] = dict(label='Clear %d sync leftovers' % leftovers, text='Move the old copies the sync tool kept in %s out of the live pool into an archive folder. They are not notes.' % where)
    if rep['index']['over_budget']:
        fixes['index'] = dict(label='Shrink the index', text='%s is %d lines and %d bytes; only the first %d lines or %d bytes load. Move detail onto topic pages and keep one line per topic.' % (
            index, rep['index']['lines'], rep['index']['bytes'], rep['index']['line_budget'], rep['index']['byte_budget']))
    for k, x in enumerate(ex.get('fixes', [])):
        fixes['extra:%d' % k] = dict(label=x['label'], text=x['text'])

    src_bad = {}
    for i, l in enumerate(links):
        src_bad.setdefault(l['src'], []).append(i)
    grid = []
    for f, c in rep['class_of'].items():
        issues, fx = [], []
        real = [i for i in src_bad.get(f, []) if links[i]['cat'] != 'false']
        if real:
            issues.append('%d broken link%s' % (len(real), '' if len(real) == 1 else 's'))
        fx += ['link:%d' % i for i in src_bad.get(f, [])]
        if f in dup_of:
            issues.append('Repeats ' + dup_of[f]); fx.append('dup:' + f)
        if f in older:
            issues.append('Older entry; newer is ' + older[f]); fx.append('old:' + f)
        if f in contra:
            issues.append(contra[f][:1].upper() + contra[f][1:]); fx.append('con:' + f)
        if f in unmarked:
            issues.append('State note with no "verified" marker' + (', names a machine or service' if f in ext else '')); fx.append('re:' + f)
        if f in rep['orphans']:
            issues.append('Nothing links to it'); fx.append('orph:' + f)
        g = 0 if real else 1 if (f in dup_of or f in older or f in contra) else 2 if f in unmarked else 3 if c == 'state' else 4
        grid.append(dict(f=f, c='state' if c == 'state' else 'rule', g=g, m=reads.get(f, 0), i=issues, fx=fx))
    grid.sort(key=lambda n: (n['g'], -n['m'], n['f']))

    tcount = len(glob.glob(os.path.join(transcripts, '**', '*.jsonl'), recursive=True)) if transcripts else None
    return dict(
        pool=label or rep['pool'], date=datetime.date.today().isoformat(),
        index=rep['index'], notes=rep['notes'], classes=rep['classes'],
        orphans=rep['orphans'], conflicts=rep['conflict_copies'], marked=rep['verified_marked'], leftovers=leftovers,
        transcripts=tcount, used=sum(1 for v in reads.values() if v) if reads else None,
        links=links, grid=grid, unmarked=unmarked, fixes=fixes,
        machines=ex.get('machines', []),
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pool')
    ap.add_argument('--out', required=True)
    ap.add_argument('--transcripts')
    ap.add_argument('--extras')
    ap.add_argument('--findings')
    ap.add_argument('--index', default='MEMORY.md')
    ap.add_argument('--label', help='name shown on the page (default: the pool folder name)')
    a = ap.parse_args()
    extras = json.load(open(a.extras, encoding='utf-8')) if a.extras else None
    data = build(a.pool, a.transcripts, extras, a.findings, a.index, a.label)
    tpl = open(os.path.join(HERE, 'report_template.html'), encoding='utf-8').read()
    blob = json.dumps(data, separators=(',', ':')).replace('</', '<\\/')
    with open(a.out, 'w', encoding='utf-8') as f:
        f.write(tpl.replace('/*DATA*/null', blob))
    real = sum(1 for l in data['links'] if l['cat'] != 'false')
    print('report: %s (%d notes, %d broken links, %d real, %d fixes available)' % (a.out, data['notes'], len(data['links']), real, len(data['fixes'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
