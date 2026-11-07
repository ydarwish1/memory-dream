"""Shared helpers for memory-dream. Python 3.8+, standard library only, no network, no model calls.

A "pool" is a folder of markdown notes plus one index file (MEMORY.md by default).
Notes may carry YAML-ish frontmatter (name, description, type). Sub-folders whose name starts
with "_archive" are archives and are never read as live notes. "topics/" holds topic pages.
"""
import os
import re
import json
import hashlib

INDEX_LINE_BUDGET = 200
INDEX_BYTE_BUDGET = 25 * 1024  # Claude Code loads the first 200 lines or 25 KB of MEMORY.md

STOP = set('the a an is are was what whats which who when where how do does did i my we our of for to in on at and or '
           'with about it this that you your me one thing things current new best main use get set'.split())

CONFLICT_RE = re.compile(r'(\.sync-conflict-\d{8}-\d{6}-[A-Z0-9]+|\(conflicted copy[^)]*\)|\.conflict\d*\b|-conflict-)', re.I)
LINK_WIKI_RE = re.compile(r'\[\[([^\]\n]+)\]\]')
LINK_MD_RE = re.compile(r'\[([^\]\n]*)\]\(([^)\s]+\.md)\)')
RULE_RE = re.compile(r"\*\*Why:\*\*|\*\*How to apply|\b(never|always|must|do not|don't|rule|trap|gotcha|lesson|pitfall|instead of|prefer|avoid)\b", re.I)
STRONG_RE = re.compile(r"\*\*Why:\*\*|\*\*How to apply|\b(never|do not|don't|must not|always)\b", re.I)
STATE_RE = re.compile(r'\b(is live|went live|now live|deployed|merged|shipped|is running|running on|currently|as of|installed|'
                      r'is up|is down|offline|online|GB free|% full|commit [0-9a-f]{7,}|v?\d+\.\d+\.\d+|port \d{2,5}|:\d{4,5}\b|'
                      r'listens on)', re.I)
HIST_RE = re.compile(r'\b(built|applied|updated|saved|edited|set up|installed|deployed|shipped|merged|created|launched|moved|'
                     r'renamed|added|removed|done|finished|live)\b[^\n]{0,40}\d{4}-\d\d-\d\d|\d{4}-\d\d-\d\d[^\n]{0,40}'
                     r'\b(built|applied|updated|saved|edited|set up|installed|deployed|shipped|merged|created|launched|done|live)\b', re.I)
DECIDE_RE = re.compile(r'(decided|decision|chose|picked|chosen|root cause|the cause is|fails? (when|because)|diagnos)', re.I)
EXT_RE = re.compile(r'(/home/|/Users/|/opt/|/srv/|/var/|~/|https?://|\bssh\b|localhost|127\.0\.0\.1|port \d+|:\d{4,5}\b|'
                    r'github\.com|docker|container|server|staging|production|\bVPS\b|cron|deploy)', re.I)
MARK_RE = re.compile(r'\b(verified|not re-checked|unconfirmed|unverified)\b|Checked \d{4}-\d\d-\d\d', re.I)
SUPERSEDE_RE = re.compile(r'(supersed\w*|replaces?|obsolete|no longer (true|valid|used)|was wrong|is wrong|outdated|stale)[^\n]{0,80}', re.I)
SERIES_RE = re.compile(r'^(.*?)(?:_v|_p|_phase_?|_round_?|_pr)(\d{1,4})(?:_\d+)*\.md$')


def words(s, keep_stop=False):
    return [w for w in re.sub(r'[^a-z0-9\s-]', ' ', s.lower()).split() if len(w) > 2 and (keep_stop or w not in STOP)]


def md5(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def read(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        return f.read()


def split_frontmatter(text):
    """Return (frontmatter_text, fields, body)."""
    if text.startswith('---'):
        end = text.find('\n---', 3)
        if end > 0:
            nl = text.find('\n', end + 4)
            fm = text[:nl + 1] if nl > 0 else text
            body = text[nl + 1:] if nl > 0 else ''
            fields = {}
            for line in fm.splitlines():
                m = re.match(r'\s*([A-Za-z_]+):\s*(.*)', line)
                if m:
                    fields[m.group(1)] = m.group(2).strip().strip('"\'')
            return fm, fields, body
    return '', {}, text


class Note(object):
    def __init__(self, pool, fname):
        self.fname = fname
        self.path = os.path.join(pool, fname)
        self.text = read(self.path)
        self.fm, self.fields, self.body = split_frontmatter(self.text)
        self.type = self.fields.get('type', '')
        self.name = self.fields.get('name', fname[:-3])
        self.description = self.fields.get('description', '')


def is_conflict_copy(fname):
    return bool(CONFLICT_RE.search(fname))


def load_pool(pool, index='MEMORY.md'):
    """Live notes at the top level of the pool (no index, no conflict copies)."""
    notes = {}
    for f in sorted(os.listdir(pool)):
        p = os.path.join(pool, f)
        if not f.endswith('.md') or f == index or not os.path.isfile(p) or is_conflict_copy(f):
            continue
        notes[f] = Note(pool, f)
    return notes


def conflict_copies(pool):
    out = []
    for dp, dn, fn in os.walk(pool):
        dn[:] = [d for d in dn if not d.startswith('_archive') and not d.startswith('.')]
        out += [os.path.relpath(os.path.join(dp, f), pool) for f in fn if is_conflict_copy(f)]
    return sorted(out)


def index_lines(pool, index='MEMORY.md'):
    p = os.path.join(pool, index)
    if not os.path.exists(p):
        return []
    out = []
    for line in read(p).splitlines():
        m = re.search(r'\[([^\]]+)\]\(([^)]+)\)', line)
        if m:
            desc = line[m.end():].strip().lstrip('—-: ').strip()
            out.append(dict(title=m.group(1), target=m.group(2), desc=desc, line=line))
    return out


def index_size(pool, index='MEMORY.md'):
    p = os.path.join(pool, index)
    if not os.path.exists(p):
        return 0, 0
    b = open(p, 'rb').read()
    return b.count(b'\n') + (0 if b.endswith(b'\n') or not b else 1), len(b)


def shingles(s, n=5):
    w = re.findall(r'[a-z0-9]+', s.lower())
    return set(' '.join(w[i:i + n]) for i in range(max(0, len(w) - n + 1)))


def duplicate_pairs(notes, threshold=0.5):
    sh = dict((f, shingles(n.body)) for f, n in notes.items())
    files = sorted(sh)
    pairs = []
    for i, a in enumerate(files):
        for b in files[i + 1:]:
            if not sh[a] or not sh[b]:
                continue
            j = len(sh[a] & sh[b]) / float(len(sh[a] | sh[b]))
            if j >= threshold:
                keep, dup = (a, b) if len(notes[a].text) >= len(notes[b].text) else (b, a)
                pairs.append(dict(keep=keep, duplicate=dup, jaccard=round(j, 2)))
    return pairs


def series_old(notes):
    groups = {}
    for f in notes:
        m = SERIES_RE.match(f)
        if m:
            groups.setdefault(m.group(1), []).append((int(m.group(2)), f))
    out = {}
    for stem, xs in groups.items():
        if len(xs) < 3:
            continue
        xs.sort()
        for _, f in xs[:-1]:
            out[f] = xs[-1][1]
    return out


def names_map(pool, notes):
    m = {}
    for f, n in notes.items():
        m[f[:-3].lower()] = f
        m[n.name.lower()] = f
    tdir = os.path.join(pool, 'topics')
    if os.path.isdir(tdir):
        for f in os.listdir(tdir):
            if f.endswith('.md'):
                m['topics/' + f[:-3]] = 'topics/' + f
    return m


def resolve_wiki(target, nmap):
    k = target.split('|')[0].strip().lower()
    if k.endswith('.md'):
        k = k[:-3]
    for cand in (k, k.replace('_', '-'), k.replace('-', '_')):
        if cand in nmap:
            return nmap[cand]
    return None


def broken_links(pool, notes):
    nmap = names_map(pool, notes)
    out = []
    for f, n in notes.items():
        for m in LINK_WIKI_RE.finditer(n.text):
            if not resolve_wiki(m.group(1), nmap):
                out.append(dict(note=f, link='[[%s]]' % m.group(1)))
        for m in LINK_MD_RE.finditer(n.text):
            t = m.group(2)
            if t.startswith('http'):
                continue
            if not os.path.exists(os.path.normpath(os.path.join(pool, os.path.dirname(f), t))):
                out.append(dict(note=f, link='(%s)' % t))
    return out


def classify(f, n, dups, olds, named_stale, findings):
    """rule = tested rule / trap / decision / preference / how-to (keep)
    state = copy of live state (convert to how-to-check, or mark verified / not re-checked)
    duplicate = near-identical to another note, or an older entry of a numbered series (merge)
    contradicted = a finding, another note, or a live check says it is wrong (fix)"""
    fd = findings.get(f) or {}
    if fd.get('verdict') == 'stale':
        if re.search(r'\*\*Checked \d{4}-\d\d-\d\d: stale', n.text):
            return 'state', 'flagged stale (banner present); rewrite it when you know what is true now'
        return 'contradicted', 'finding: ' + fd.get('evidence', '')[:120]
    if f in named_stale:
        return 'contradicted', 'named stale by ' + ', '.join(named_stale[f][:3])
    if f in dups:
        return 'duplicate', 'duplicate of ' + dups[f]
    if f in olds:
        return 'duplicate', 'older entry of a series; newest is ' + olds[f]
    body = n.body
    rule, state = len(RULE_RE.findall(body)), len(STATE_RE.findall(body))
    if DECIDE_RE.search(body) and n.type != 'feedback':
        return 'rule', 'decision or diagnosis'
    if n.type == 'project' and (HIST_RE.search(body[:400]) or state >= 2) and len(STRONG_RE.findall(body)) < 2:
        return 'state', 'project history or live state'
    if n.type in ('feedback', 'user') or rule >= 1:
        return 'rule', 'rule words: %d' % rule
    if state >= 1:
        return 'state', 'state words: %d' % state
    return 'rule', 'reference'


def named_stale_map(notes):
    out = {}
    for f, n in notes.items():
        for m in SUPERSEDE_RE.finditer(n.text):
            for r in re.findall(r'([\w-]+\.md)\b', m.group(0)) + LINK_WIKI_RE.findall(m.group(0)):
                r = r if r.endswith('.md') else r + '.md'
                if r in notes and r != f:
                    out.setdefault(r, []).append(f)
    return out


def load_findings(path):
    if not path:
        return {}
    data = json.load(open(path))
    if isinstance(data, list):
        return dict((d['note'], d) for d in data)
    return data


def manifest(root, skip_dirs=('.git', '.stversions', '.stfolder')):
    out = {}
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in skip_dirs]
        for f in fn:
            if f.startswith('._') or f == '.DS_Store':
                continue
            p = os.path.join(dp, f)
            out[os.path.relpath(p, root)] = md5(p)
    return out
