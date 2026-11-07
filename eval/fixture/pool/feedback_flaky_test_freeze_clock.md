---
name: flaky-test-freeze-clock
description: Flaky date tests: freeze the clock
metadata:
  type: feedback
---

Date tests that fail near midnight: freeze the clock to a fixed morning time in the test setup.

**Why:** the suite failed only between 23:00 and 01:00. Freezing the clock fixed 4 of 4 runs. Verified 2025-02-11.
