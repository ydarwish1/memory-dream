# File formats

## topics.json (you write it; `dream.py --topics`)

```json
{
  "goals": ["Ship the board redesign."],
  "topics": [
    {
      "id": "servers",
      "title": "Servers and access",
      "purpose": "How to reach the servers and what runs where.",
      "words": ["staging", "server", "ssh", "port", "api", "logs"],
      "facts": ["Reach staging with `ssh staging`. LIVE check: `ssh staging hostname` printed staging-1 (2025-03-10)."]
    }
  ]
}
```

- `words` file a note under a topic: each word in the note's file name scores 2, in its description 1. Highest score wins; no match goes to "Other notes".
- `facts` are the short "current facts" block on top of the topic page. Each should name the check that proved it and the date: a live command you ran today, or a LIVE transcript line (say which, for example "transcript 2025-03-12, command result"). Leave it empty if nothing for that topic was checked.
- `goals` (optional) go into the index under "Current goals". Mark them as inferred if the user did not state them.

## findings.json (you write it after checking notes; `dream.py --findings`, `audit.py --findings`)

A list, one entry per note you checked:

```json
[
  {"note": "reference_staging_access.md", "verdict": "stale",
   "evidence": "transcripts/session-2025-03-10.jsonl:3 (LIVE): `ssh staging hostname` printed staging-1.",
   "now": "Reach staging with `ssh staging`."},
  {"note": "project_api_port.md", "verdict": "rewrite",
   "replacement": "The API listens on port 9090 since 2025-03-11. Verified 2025-03-12: health check ok on 9090.",
   "evidence": "the user said it moved (session-2025-03-12.jsonl:1); health ok on 9090 (:3)."},
  {"note": "reference_check_disk.md", "verdict": "verified", "check": "`df -h /` ran on the app server."}
]
```

- `stale` adds a dated banner on top of the note. Use it when you know it is wrong but not the full replacement.
- `rewrite` replaces the body (the old text is archived). Use it when you know what is true now.
- `verified` appends "Verified <date>: <check>". Add `"date": "2025-03-10"` when the proof is older than today (a transcript line); otherwise the dream date is used.
- `unconfirmed` appends "Unconfirmed <date>: <evidence>". Use it when the only support is the assistant's own words or nothing at all.
- `rewrite` also updates the note's `description` and its line on the topic page, tagged "[rewritten <date>]", so the old fact does not stay visible there.

## questions.json (the eval; `score.py`)

```json
[
  {"id": "api-port", "q": "Which port does the API use?", "query": "api port health check",
   "keys": ["9090"], "split": "heldout", "proof": "transcripts/session-2025-03-12.jsonl:3"}
]
```

- `query` is what a session would look up (often the words it actually searched for).
- `keys` must all appear in the lookup output; a key can be a list of alternatives: `[["port 9090", "9090/tcp"]]`.
- `split` is `dev` (you may look at it while improving memory) or `heldout` (you may not).
- `proof` is the transcript line (or note) that shows the answer is true.
- `kind` (optional): `transcript` (default, proven by a session) or `note` (a regression question proven by a note). Score them apart with `score.py --kind`.

## extras.json (optional; `report.py --extras`)

What the audit cannot know on its own: your verdicts on broken links, the machines that share the pool, and extra fixes.
`eval/fixture/example-extras.json` is a full example.

```json
{
  "machines": [
    {"name": "Laptop", "status": "ok", "detail": "synced 09:12",
     "good": ["Pulled and pushed the pool at 09:12"], "issues": []}
  ],
  "links": {
    "notes_page.md -> [[wikilinks]]": {"verdict": "false", "why": "example text, not a link"}
  },
  "fixes": [
    {"label": "Give the index one writer", "text": "Make one machine the only writer of MEMORY.md."}
  ]
}
```

- `machines`: up to four, drawn on top of the map. `status` is `ok`, `warn`, `bad` or `unknown`; `detail` is the short line under the name (about 20 characters).
- `links`: keyed by the note and the link exactly as the audit prints them (`note.md -> [[target]]` or `note.md -> (target.md)`). `verdict` is `false`, `missing`, `renamed` or `archived`; `why` is shown when someone hovers the link.
- `fixes`: extra items for the cart, each a short `label` and the `text` that goes into the prompt.
