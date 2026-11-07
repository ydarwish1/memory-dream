# What makes a note worth keeping

This is a description of value, not a writing rule. Write notes however you like; these are the
parts a later session can use, and the parts the dream pass looks for.

A useful note holds:

1. **The thing worked out.** A tested rule, a trap, a decision and its reason, a how-to, or a
   preference the user stated. Something a later session could not read off the machine.
2. **How it was verified.** The command, the test, or the person who said it. "Ran
   `ssh staging hostname`, got `staging-1`" is worth more than "SSH works".
3. **The date it was last true.** State changes; a date tells the next session how far to trust it.
4. **Verified or unconfirmed.** "Verified 2025-03-12 (health check on 9090)" or
   "Not re-checked since 2025-02-20". Unconfirmed is fine. Unlabelled is the problem.

What tends to go wrong:

- **A copy of live state with no check.** "The API listens on 8080" is true until the day it is
  not. Better: what to run to find out, plus the last result and its date.
- **The same fact in two notes.** One gets fixed, the other keeps misleading.
- **Detail in the index.** The index is loaded every session (Claude Code: first 200 lines or
  25 KB). Detail belongs in topic pages and notes; the index points at them.

Example (made-up):

```markdown
---
name: staging-access
description: Reach staging over SSH with `ssh staging`
metadata:
  type: reference
---

Reach staging with `ssh staging` (host alias in ~/.ssh/config).
Verified 2025-03-10: `ssh staging hostname` printed staging-1.
How to check again: run the same command; if it fails, check the VPN first.
```
