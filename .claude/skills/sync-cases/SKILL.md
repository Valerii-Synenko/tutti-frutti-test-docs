---
name: sync-cases
description: Sync the qase_cases lists in the user stories with Qase - remove keys of cases deleted in Qase and add cases created by hand in a story's Qase suite. Read-only towards Qase. Use when the user asks to sync stories with Qase or says they added or deleted cases in Qase ("синхронізуй з Qase", "sync cases", "я видалив кейс у Qase").
---

# Sync qase_cases with Qase

After a push, Qase is the source of truth for the cases; the stories only keep their keys in
`qase_cases`. This skill brings those lists back in line when cases change in Qase by hand.

## Run

```bash
python3 scripts/qase_sync.py --sync </dev/null
```

What it does, for every story in `user-stories/`:
- **Deleted in Qase** → the key is removed from the story's `qase_cases`.
- **Created by hand in the story's suite** (the suite named in `qase_suite`, e.g.
  `User & Auth.Logout`) → the key is appended to `qase_cases`.
- Cases in a parent suite (`User & Auth`) or in a suite no story points to are ignored: there's no
  way to tell which story they belong to. Mention them if the user expects them to be picked up.

It makes two read requests (all cases, all suites) and changes nothing in Qase. In the stories it
rewrites only `qase_cases`, as a block list (`- TF-2` lines), so Obsidian doesn't reformat it.

## Report

Relay the script's lines as is, e.g.
`User logout.md: removed TF-5, TF-9 (deleted in Qase); added TF-30 (new in the suite); 20 in total`,
or "in sync" when nothing changed. Then:
- If a story lost all its cases, say so: its ACs are no longer covered in Qase.
- If keys were added, the new cases have no AC link in the story; suggest checking which AC they
  cover.
- Don't commit; the user asks for that separately.

If the token is missing or rejected, handle it as in the `qase-push` skill (the user runs the
command once in a terminal; never touch `.env`).
