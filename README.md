# Tutti Frutti — test documentation

Test design for [**Tutti Frutti**](https://github.com/Valerii-Synenko/tutti-frutti), a training fruit
shop built on microservices (users, catalogue, inventory, orders, AI assistant, gateway, React UI).

This repository holds the QA side of the project: user stories, their analysis against the real
code, and test cases that are pushed to [Qase](https://qase.io) and later referenced from the
automated tests. It is an [Obsidian](https://obsidian.md) vault, so it reads like a set of linked
notes, but every file is plain Markdown and renders on GitHub as well.

## Workflow

```
 user story          analysis              test design            Qase               automation
 (draft/ready) ──► against the code ──► test cases in the ──► suite + cases ──► @qase.id(...) in
                   → Open questions      story file            → qase_cases       API / UI tests
```

1. **Story.** Each story has a description and numbered acceptance criteria (`AC-1`, `AC-2`, ...).
   A story written by a person is reviewed first: vague wording, gaps (negative paths, limits,
   error states) and untestable ACs come back as ready-to-paste proposals under
   `## Suggested improvements`, weighted `must` / `should` / `nice`. The author decides which to
   apply.
2. **Analysis.** The story is checked against the product source code: validation rules, error
   messages, HTTP statuses, redirects, `data-testid`s. Every gap, contradiction or untestable AC is
   recorded under `## Open questions` with a file and line reference. The requirement text itself
   is never rewritten.
3. **Test design.** Cases are derived per AC with equivalence partitioning, boundary values,
   decision tables and state transitions. Every case traces back to an AC, every AC has at least
   one case, and every case states where it is best automated: `API`, `UI` (Playwright) or `both`.
4. **Approval and Qase.** Draft cases are reviewed in the story. Setting
   `test_cases_approved: true` approves them; `scripts/qase_sync.py` then pushes them to Qase,
   writes the case keys (`TF-2`, `TF-3`, ...) into the frontmatter, marks the story `analyzed` and
   removes the drafts from the story. From then on Qase is the source of truth for the cases.
5. **Automation.** The case numbers are used as `@qase.id(...)` in the automated tests
   (`TF-11` → `@qase.id(11)`), so results are reported against the right cases.

## Repository layout

```
user-stories/
  User & Auth/                 ← folder = Qase suite
    User registration.md
    Registered user login.md
    User logout.md
templates/
  user-story.md                ← template for new stories
scripts/
  qase_sync.py                 ← pushes test cases to Qase
CLAUDE.md                      ← rules that always apply (product, formats, conventions)
.claude/skills/                ← workflows: story review, test design, Qase push and sync
.env.example                   ← Qase settings template (.env is created on the first push)
```

The product code is not part of this repository. Locally it is cloned into `.product/tutti-frutti`
(gitignored) and used as the source of truth for the analysis.

## Story format

```markdown
---
id: US-3
status: draft            # draft → ready → analyzed
qase_suite: User & Auth.Logout
qase_cases: []           # case keys (TF-2, TF-3, ...), filled in by scripts/qase_sync.py
test_cases_approved: false  # set to true to push the draft cases
related: ["[[Registered user login]]"]
---

## Description
**As a** logged-in user, **I want to** log out, **So that** ...

## Acceptance Criteria
- **AC-1:** ...

## Test cases               ← drafts; removed once pushed to Qase
### TC: Revoke refresh token on logout
- **Description:** Checks that logout revokes the refresh token on the server, so it can no
  longer be used to get a new access token.
- **AC:** AC-6
- **Level:** API
- **Severity:** critical
- **Priority:** high
- **Type:** security
- **Behavior:** positive
- **Preconditions:** ...
- **Steps:**
  1. ...
- **Expected result:**
  1. `POST /auth/logout` returns `204`.
  2. `POST /auth/refresh` returns `401` "Refresh token has been revoked".
- **Test data:** ...

## Open questions
- **AC-6:** ... (`services/users-service/app/main.py:197`)
```

The story format is in [CLAUDE.md](CLAUDE.md); the test case format and the test design rules are in
[`.claude/skills/generate-cases`](.claude/skills/generate-cases/SKILL.md).

## Setup

Requirements: Python 3.10+ (standard library only), optionally Obsidian.

```bash
git clone <this repo> tutti-frutti-test-docs
cd tutti-frutti-test-docs

# product code used for the analysis (read-only)
git clone https://github.com/Valerii-Synenko/tutti-frutti .product/tutti-frutti
```

**Qase: the only thing you need is an API token** (Qase → Workspace settings → API tokens).
On the first push the script asks for it, saves it to `.env` in the repo root (gitignored, never
committed) and doesn't ask again. If the Qase project `TF` doesn't exist in your workspace yet, the
script creates it. To use another project, set `QASE_PROJECT` in `.env` (see `.env.example`).

`.env` starts with a dot, so Finder and Obsidian hide it. You normally don't need to open it; if
you do (e.g. to replace the token), press `Cmd + Shift + .` in Finder or open the folder in a code
editor.

Open the folder as a vault in Obsidian to browse stories with backlinks and the graph view.

### Working with the scripts

Obsidian can't open or edit `.py` files, so `scripts/` looks empty there. To view, edit and run
the scripts, I recommend [Thonny](https://thonny.org), a free, lightweight Python editor that
ships with its own Python, so there is nothing else to install. To see the `.py` files in the
Obsidian file list as well, turn on **Settings → Files & links → Detect all file extensions**.

`qase_sync.py` needs the story path as an argument, so pressing **Run** in Thonny without one
stops with `error: the following arguments are required: story`. To pass it:

1. Turn on **View → Program arguments**. A text field appears in the toolbar.
2. Enter the story path, relative to `scripts/` (Thonny runs a script from its own folder), plus
   `--dry-run` for a check without sending anything:
   ```
   "../user-stories/User & Auth/User logout.md" --dry-run
   ```
3. Press **Run**. To push, approve the story (`test_cases_approved: true`) and replace the
   arguments with `--approved`.

## Pushing test cases to Qase

1. Review the draft cases in the story and set `test_cases_approved: true` (in Obsidian it's a
   checkbox in the story's Properties).
2. Push:

```bash
# validate a story's drafts and print the payload, nothing is sent (no approval needed)
python3 scripts/qase_sync.py "user-stories/User & Auth/User logout.md" --dry-run

# push every approved story that still has drafts
python3 scripts/qase_sync.py --approved

# or push one approved story
python3 scripts/qase_sync.py "user-stories/User & Auth/User logout.md"
```

After a push the story gets the case keys in `qase_cases` (`TF-2`, `TF-3`, ...) and `status: analyzed`, and its
`## Test cases` section is removed. Further edits to those cases are made in Qase.

If you add or delete cases in Qase by hand, bring the stories in line with:

```bash
python3 scripts/qase_sync.py --sync
```

- A case deleted in Qase is removed from the story's `qase_cases`.
- A case created in the story's suite (e.g. `User & Auth.Logout`) is added to it. Cases in a parent
  suite or in a suite that belongs to no story are left alone.

It reads the case and suite lists once and only changes `qase_cases`; nothing in Qase is
modified.

- Suites have two levels, written with a dot in `qase_suite`: the feature area (story folder) and
  the story's sub-suite, e.g. `User & Auth.Logout`.
- All cases are created in a single bulk request.
- A story that isn't approved is never pushed (except as `--dry-run`).
- Cases already in Qase (by the keys in `qase_cases`, or by title in the suite) are updated from
  the story instead of duplicated. `--no-update` only creates the missing cases.
- Field mapping: Severity, Priority, Type, Behavior → the Qase fields of the same name; Level →
  layer (`API` → api, `UI`/`both` → e2e); Preconditions → preconditions; each step → a Qase step;
  Expected result and Test data → the last step; Description → description; story ID, AC and Level
  → tags (`US-3`, `AC-6`, `api`).
  Option IDs are read from Qase at push time, not hardcoded.

### Why a script and not the Qase MCP server

Qase has an official [MCP server](https://github.com/qase-tms/qase-mcp-server) that would let
Claude Code create cases directly. I chose not to use it here, on purpose, to keep token usage low:

- **No re-typing.** The cases already exist in the story file. Through MCP the model would have to
  output every case again as tool arguments. The script reads the file itself, and output tokens
  are the most expensive ones.
- **One call instead of many.** MCP usually means one tool call per case, and every call re-sends
  the whole conversation context to the model. The script sends everything in one bulk request,
  and the model runs a single command.
- **Small responses.** The model only sees a one-line summary
  (`created 12, already existed 0; qase_cases = [...]`), not full JSON objects from the API.

Rough estimate for one story with 12 cases: about 10–20k tokens through MCP, a few hundred with the
script. The script costs a few thousand tokens once, to write it.

It also has side benefits: the sync gives the same result every time, `--dry-run` shows the
payload before anything is sent, and it works without an AI assistant at all.

## AI-assisted

The vault is set up for [Claude Code](https://claude.com/claude-code). `CLAUDE.md` holds only the
rules that always apply (product, vault structure, story format, Qase basics); each workflow is a
[skill](https://docs.claude.com/en/docs/claude-code/skills) in `.claude/skills/`, loaded only when
it's needed, which keeps every session's context small:

| Skill | What it does |
|---|---|
| `/new-story` | creates a story from the template with the next free `US-<n>` id |
| `/review-story` | reviews a story written by a person and proposes ready-to-paste improvements |
| `/generate-cases` | checks the story against the code and designs draft test cases |
| `/qase-push` | pushes approved cases to Qase |
| `/sync-cases` | updates `qase_cases` after cases are added or deleted in Qase by hand |

A session start hook pulls the latest product code before each session. Story analysis and case
drafts are produced with Claude's help and reviewed by hand.

Vault content is always written in English, but the chat language is personal: on the first
session, Claude asks which language you prefer and saves it to `CLAUDE.local.md` (gitignored).
The vault user can change it manually at any time in `CLAUDE.local.md`.
