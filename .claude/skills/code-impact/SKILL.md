---
name: code-impact
description: Check which user stories and Qase test cases are affected by changes in the Tutti Frutti product code since each story was analysed (code_commit), and report what to update - open questions that got resolved, ACs or cases whose expected results changed, line references that moved. Use when the user asks what changed in the product, whether stories or cases are still up to date, or after the product repo got new commits ("what changed in the code?", "are the stories still up to date?").
---

# Code impact: which stories and cases does a product change affect?

Each analysed story records the product commit it was checked against (`code_commit`) and the
code it depends on (`code_paths` plus every `path:line` reference in its text). The script does
the mechanical part; your job is to judge what the changes mean.

## 1. Find the changes

```bash
python3 scripts/code_impact.py
```

It pulls `.product/tutti-frutti`, then for every story prints one of:
- `up to date` — nothing to do;
- `none touch its code → code_commit = <HEAD>` — new commits elsewhere; already marked as checked;
- `changed since <commit>` — the changed files (`+added -removed`), the story's line references in
  them, and the commits. Only these need your review;
- `no code_commit` / `no code_paths` — the story has no baseline; say so and suggest filling it on
  the next analysis.

## 2. Review each affected story

For every changed file, read only the relevant part of the diff:

```bash
git -C .product/tutti-frutti diff <code_commit>..HEAD -- <file>
```

and the story's cases in Qase, if it has any:

```bash
python3 scripts/qase_sync.py "<story path>" --show </dev/null
```

Then sort the findings:
- **Resolved open questions:** the code now does what the story asked (e.g. password complexity
  is enforced, the error text matches). Cases marked "Expected to fail today" may pass now.
- **Changed behaviour:** texts, statuses, limits, redirects, field names that cases or ACs rely
  on. Name the affected cases by key (`TF-48`) and say what their expected result should become.
- **New behaviour without coverage:** a new rule, endpoint or UI state in the story's area with no
  AC or case.
- **Moved line references:** `file:line` in Open questions that now point elsewhere. Find the new
  line.
- **Irrelevant:** changes in a shared file (e.g. `services/gateway/app/main.py`) that don't touch
  the story's endpoints or screens. Say "not relevant" in one line.

## 3. Apply what's safe, propose the rest

- You may update `file:line` references in `## Open questions` to their new lines.
- Everything else is a proposal in the reply: AC wording (the author decides, see `review-story`),
  open questions to close, cases to update in Qase (the user edits them there, or asks you to;
  then run `sync-cases`), new cases (draft them with `generate-cases`).
- Never change Qase, the story text or `status` on your own in this skill.

## 4. Mark as checked

When the user has seen the report and agrees (or says to skip a story), move its baseline:

```bash
python3 scripts/code_impact.py --mark "<story path>" ...
```

If the review found work that is still open, leave `code_commit` as is, so the next run shows
the same changes again.

## Report

Per affected story: product commits in one line, then the findings grouped as above with the case
keys and file references, then a short "to do" list. Unaffected stories: one line in total
("2 stories unchanged").
