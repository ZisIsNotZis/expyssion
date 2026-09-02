---
id: 012
title: "Handler tagging and effect identity"
labels: [wayfinder:grilling]
status: closed
assignee: z
blocked-by: ["010"]
---

## Question

Generators are airtight (a yielder's greenlet-parent is its driver), but user-level effects will want identity: should Result messages carry effect tags (so a handler only catches what it means to), is a single untagged yield kind enough for v1, and what does the spec say about action-at-a-distance (behavior depending on the dynamic handler stack)? Decide now what v1 fixes and what it leaves as a documented sharp edge.

**Resolution (closed 2025-09-01, auto-run):** v1 ships a single untagged `Yield` kind with the handler whitelist of ticket 002 (collectors + generator); no user-defined `handle`. The channel's message struct reserves a tag field for forward compatibility: when user handlers arrive, handlers match on tag and the builtins use a private tag so they can never cross-consume. Meanwhile the documented sharp edge stands: nested collectors — the nearest active handler wins, dynamically; generators remain airtight regardless (a yielder's greenlet-parent is its driver, so no wrong-handler capture is possible for generator-style consumption).
