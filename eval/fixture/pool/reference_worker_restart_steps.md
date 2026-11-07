---
name: worker-restart-steps
description: How to restart the background worker
metadata:
  type: reference
---

To restart the background worker run systemctl restart acme-worker on the app server, then check systemctl status acme-worker shows active.
