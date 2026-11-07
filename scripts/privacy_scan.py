#!/usr/bin/env python3
"""privacy_scan: fail if a folder holds personal or secret-looking text. Run it before you publish.

usage: python3 privacy_scan.py PATH [--words WORDS.txt] [--allow ALLOW.txt] [--allow-user NAME ...]

--words: a private word list kept OUTSIDE the folder (your name, email, usernames, host and machine
names, project and client names, tool names that exist only on your machines). One per line,
case-insensitive; a line "re:<regex>" is a regular expression. Built-in checks run always:
  - email addresses (except example.com / example.org / example.net)
  - IPv4 addresses (except 127.0.0.1, 0.0.0.0 and the documentation ranges 192.0.2.x, 198.51.100.x, 203.0.113.x)
  - absolute home paths /Users/<name>, /home/<name>, C:\\Users\\<name> (except --allow-user, default: alex)
  - key- or token-shaped strings (sk-..., ghp_/gho_/github_pat_, AKIA..., xoxb-, private key blocks)
--allow: exact strings that may appear (for example the public URL of the repo itself); they are
removed from each line before the checks. Keep it outside the folder too, and say what it allowed.
Exit 0 = no hits, 1 = hits (each printed as file:line: kind: match)."""
import os
import re
import sys
import argparse

EMAIL = re.compile(r'[\w.+-]+@([\w-]+\.)+[a-z]{2,}', re.I)
IPV4 = re.compile(r'\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b')
HOME = re.compile(r'(/Users/|/home/|C:\\\\?Users\\\\?)([A-Za-z0-9._-]+)')
TOKENS = re.compile(r'(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|xox[abposr]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)')
DOC_NETS = ('192.0.2.', '198.51.100.', '203.0.113.')
SKIP_DIRS = {'.git', '__pycache__'}


def scan(root, words, allow_users, allowed=()):
    pats = []
    for w in words:
        w = w.strip()
        if not w or w.startswith('#'):
            continue
        pats.append((w, re.compile(w[3:] if w.startswith('re:') else re.escape(w), re.I)))
    hits = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root)
            for w, rx in pats:  # file names count too
                if rx.search(rel):
                    hits.append('%s:0: word in file name: %s' % (rel, w))
            try:
                text = open(p, encoding='utf-8').read()
            except (UnicodeDecodeError, OSError):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                for al in allowed:
                    line = line.replace(al, '')
                for w, rx in pats:
                    if rx.search(line):
                        hits.append('%s:%d: private word: %s' % (rel, i, w))
                for m in EMAIL.finditer(line):
                    if not re.search(r'@example\.(com|org|net)$', m.group(0), re.I):
                        hits.append('%s:%d: email: %s' % (rel, i, m.group(0)))
                for m in IPV4.finditer(line):
                    ip = m.group(0)
                    if all(int(x) <= 255 for x in m.groups()) and ip not in ('127.0.0.1', '0.0.0.0') and not ip.startswith(DOC_NETS):
                        hits.append('%s:%d: ip address: %s' % (rel, i, ip))
                for m in HOME.finditer(line):
                    if m.group(2).lower() not in allow_users:
                        hits.append('%s:%d: home path: %s%s' % (rel, i, m.group(1), m.group(2)))
                for m in TOKENS.finditer(line):
                    hits.append('%s:%d: token-shaped: %s...' % (rel, i, m.group(0)[:8]))
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('path')
    ap.add_argument('--words')
    ap.add_argument('--allow-user', nargs='*', default=['alex'])
    ap.add_argument('--allow')
    a = ap.parse_args()
    words = open(a.words, encoding='utf-8').read().splitlines() if a.words else []
    allow = set(u.lower() for u in a.allow_user) | {'<name>', '<you>', 'you', 'name', 'user', 'username', 'shared'}
    allowed = [l.strip() for l in open(a.allow, encoding='utf-8')] if a.allow else []
    allowed = [l for l in allowed if l and not l.startswith('#')]
    hits = scan(a.path, words, allow, allowed)
    for h in hits:
        print(h)
    print('privacy_scan: %d hit(s) in %s (%d private words checked, %d allowed strings: %s)' % (
        len(hits), a.path, len([w for w in words if w.strip() and not w.startswith('#')]), len(allowed), ', '.join(allowed)))
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main())
