---
name: qase-push
description: Push the draft test cases the user ticked Approved to Qase with scripts/qase_sync.py (creates suites and cases, appends case keys to qase_cases, removes approved and Not relevant drafts from the story, marks it analyzed when no drafts are left). Use only when the user asks to push or upload cases to Qase ("push the approved ones", "upload the cases to Qase").
argument-hint: [story name]
---

# Push approved test cases to Qase

Pushing changes Qase, so run it only on the user's request. Use `scripts/qase_sync.py` only,
never hand-written API calls or the Qase MCP server (that's a deliberate token-saving choice,
see README).

## 1. Check what will be pushed

- Each draft in `## Test cases` has two checkboxes the user ticks: `- [x] Approved` → pushed
  (with any edits the user made to the draft), `- [x] Not relevant` → removed from the story,
  never pushed. Undecided drafts stay. A draft with both ticked is left as is with a warning.
  Never tick the checkboxes yourself.
- An approved draft whose title already exists in Qase (in `qase_cases` or the suite) updates
  that case (fields, steps, suite). If the user may have edited it in Qase, warn and offer
  `--no-update`, which only creates the missing cases.
- Optional sanity check: `python3 scripts/qase_sync.py "<story path>" --dry-run`.

## 2. Push

```bash
python3 scripts/qase_sync.py --approved </dev/null          # every story with ticked drafts
python3 scripts/qase_sync.py "<story path>" </dev/null      # one story (refuses if nothing is ticked)
```

Add `--no-update` when existing cases must stay untouched.

What the script does per story: finds or creates the suite from `qase_suite`
(`User & Auth.Logout` = parent `User & Auth`, child `Logout`; creates the project `TF` if needed),
creates the approved cases in one bulk request, updates the ones already in Qase, appends the keys
to `qase_cases` (block list), removes approved and not relevant drafts from the story, and when
no drafts are left removes `## Test cases` and sets `status: analyzed`.

Field mapping: Severity, Priority, Type, Behavior → Qase fields of the same name (option IDs looked
up via `GET /system_field`); Level → layer (`API` → api, `UI`/`both` → e2e); Description →
description; Preconditions → preconditions; each step → a Qase step with its own Data and Expected
result; story ID, AC and Level → tags (`US-3`, `AC-6`, `api`).

## 3. If it fails

- **No token:** the script asks for `QASE_API_TOKEN` interactively, which doesn't work from
  Claude Code. Ask the user to run the same command once in a terminal or Thonny and paste the
  token; it's saved to `.env`. Never read, print or edit `.env`.
- **`401`:** the token is wrong or revoked; the user fixes it in `.env`.
- **Other API error:** show the script's error line and stop; don't retry with other tools.

## 4. Report

One line per story: suite, created / updated counts, key range (`TF-23 … TF-38`), how many
not relevant drafts were removed and how many drafts are still undecided; relay conflict
warnings. Then remind:
from now on the cases live in Qase; after editing or deleting them there, run the `sync-cases`
skill. Case keys map to automation as `TF-11` → `@qase.id(11)`.
