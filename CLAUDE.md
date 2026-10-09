# Tutti Frutti — test documentation (Obsidian vault)

This vault holds the user stories for the **Tutti Frutti** product and everything needed for
test design: story analysis, test cases, glossary. No product code is written here. The product code is
cloned into `.product/tutti-frutti` (GitHub: https://github.com/Valerii-Synenko/tutti-frutti);
read it whenever you need to check behaviour against the requirements.

- A SessionStart hook runs `git pull` there on every start and reports the current commit.
- The clone is a read-only mirror: never edit, commit or check out branches in `.product/`.
- `.product/` is a hidden folder, so Obsidian doesn't index it.

Product README (loaded into context on every start):
@.product/tutti-frutti/README.md

## Product

Tutti Frutti is a training fruit shop built on microservices (a Sock Shop alternative). It exists
as a "guinea pig" project for practising API and UI test automation.

| Component | What it does |
|---|---|
| `users-service` | Registration, login, JWT (access + refresh), profile, roles |
| `catalogue-service` | Fruit catalogue, moderation of seller listings |
| `inventory-service` (Go, gRPC) | Stock and prices. Internal service; the UI never calls it directly |
| `orders-service` | Cart, orders, per-seller sales stats |
| `fruit-assistant-service` | AI chat assistant with guardrails (stays on the topic of fruit) |
| `gateway` (BFF) | Single entry point for the UI: `http://localhost:8080` |
| `ui` (React) | `http://localhost:4173`. Every interactive element has a `data-testid` |

### Roles

- **Buyer**: the default role for every new account.
- **Seller** (`is_seller`): enabled in the cabinet with the **Become a seller** button. Unlocks
  **My listings** and **Sales calculator**.
- **Admin** (`is_admin`, seeded account `admin@admin.com` / `admin`): has the **Moderation queue**.

Roles are carried as claims in the JWT.

### Key flows

- **Seller listing**: `pending` (hidden from the market), then admin approve gives `approved`
  (the gateway registers stock in inventory, so the fruit becomes orderable) or reject gives
  `rejected`. A listing can be deleted by its seller or by any admin, whatever its status.
- **Checkout**: `POST /orders` takes the cart, `contact` (name, phone), `shipping_address` and
  `payment` (card number, `MM/YY`, CVC). Payment is simulated: any card that passes the Luhn check
  and isn't expired is charged. The test card `4000 0000 0000 0002` is always declined with `402`,
  and nothing is reserved. Only the card brand and last 4 digits are stored.

### UI pages (routes)

| Name in the story | Route | Component |
|---|---|---|
| Market page / Catalogue | `/` | `CataloguePage` |
| Fruit detail | `/fruits/:slug` | `FruitDetailPage` |
| Login | `/login` | `LoginPage` |
| Registration | `/register` | `RegisterPage` |
| Cart | `/cart` | `CartPage` |
| Orders | `/orders` | `OrdersPage` |
| Cabinet | `/cabinet` | `CabinetPage` |
| NavBar | on every page | `Navbar` |

## Vault structure

```
user-stories/
  <Feature area>/          ← folder name = suite in Qase (e.g. "User & Auth")
    <Story name>.md
.product/
  tutti-frutti/            ← read-only clone of the product repo (hidden from Obsidian)
templates/
  user-story.md            ← template for the core Templates plugin
scripts/
  qase_sync.py             ← pushes a story's test cases to Qase
.env                       ← Qase credentials (gitignored; template: .env.example)
CLAUDE.md
```

- One story = one file. The file name matches the story name.
- Link stories with wikilinks such as `[[Registered user login]]`, not markdown links, so Obsidian
  tracks backlinks and the graph.
- Don't rename or move files unless asked; it breaks wikilinks.
- Don't touch `.obsidian/`.

## User story format

New stories are created from `templates/user-story.md`.

```markdown
---
id: US-1
status: draft            # draft → ready → analyzed
qase_suite: User & Auth.Login
qase_cases: []           # Qase case keys (TF-2, TF-3, ...), filled in by the sync script
test_cases_approved: false  # the user sets true to push the draft cases
related: ["[[Registered user login]]"]
---

## Description
**As a** <role>,
**I want to** <action>,
**So that** <value>.

## Acceptance Criteria
- **AC-1:** ...

## Open questions
```

- Story IDs are `US-<n>` without leading zeros (`US-1`, `US-12`). A new story takes the next free
  number across all folders.
- Edit the frontmatter as YAML properties (Obsidian Properties). Don't duplicate these values in
  the body.
- Write non-empty lists in block style (`key:` then `  - item` lines), the way Obsidian saves them;
  an empty list stays `[]`. When changing a list, replace the whole entry, including its `- item`
  lines, or the YAML ends up with two values.
- If an older story has no frontmatter, add it when you work on that story, without changing the
  story text.
- Change `status` only when told to. `analyzed` is set by the sync script once the approved cases
  are in Qase.
- `test_cases_approved` belongs to the user: never set it to `true`. Set it to `false` whenever you
  add or rewrite draft cases in a story, so they get reviewed before the next push.

## Working with stories

1. **Don't rewrite requirements.** The story text belongs to its author. If something is unclear,
   contradicts itself or contradicts the code, record it under `## Open questions` at the end of
   the file. Leave the story text itself unchanged.
2. **Check against the code.** Before generating cases, look in `.product/tutti-frutti` at how the
   behaviour is actually implemented: error messages, validation rules, redirects, `data-testid`s.
   Record every mismatch under `Open questions` with a file and line reference.
3. **Test design.** For each acceptance criterion, apply the techniques that fit: equivalence
   partitioning, boundary values (e.g. password length 7/8/9), decision tables for combinations
   of rules, state transitions for listing and order statuses. Cover both positive and negative
   scenarios.
4. **Traceability.** Every case references the AC number it verifies. Every AC has at least one
   case. If an AC can't be tested (e.g. "secure data"), flag it under `Open questions`.
5. **Test level.** For each case, state where it is best automated: `API` (via the gateway), `UI`
   (Playwright) or `both`. Check JWT contents (roles, claims) at the API level.
6. **Test pyramid.** Design the set of cases for a story along the test pyramid: most cases at the
   API level (business rules, validation, status codes, error messages, permissions, data
   combinations), fewer at the UI level. Don't repeat at the UI what an API case already proves;
   a UI case checks what only the browser shows: page flow and redirects, what's visible on the
   page, form behaviour, browser storage and navigation. This is a guideline, not a quota: when a
   UI case is important (a key user journey, a security-relevant screen state, a UI-only rule),
   write it. Unit tests are out of scope for this vault (they live in the product repo).

## Test case format

```markdown
### TC: <Short imperative title>
- **Description:** Checks that <condition> leads to <expected behaviour>.
- **AC:** AC-2
- **Level:** API | UI | both
- **Severity:** blocker | critical | major | normal | minor
- **Priority:** high | medium | low
- **Type:** functional | smoke | regression | security | usability | performance | acceptance | compatibility | integration | exploratory | other
- **Behavior:** positive | negative | destructive
- **Preconditions:** ...
- **Steps:**
  1. ...
- **Expected result:** ...
- **Test data:** ...
```

- The title is short and unique within the suite. The Qase case is created from it.
- Description is one or two plain sentences for a human reader: what the case checks and why it
  matters, without steps or IDs (the story, AC and level are already in the tags).
- Severity is the impact of a failure; Priority is how soon the case must run (high = smoke-level
  core flow, low = edge cases). Behavior: `positive` for a valid flow, `negative` for invalid input
  or an unauthorised/unexpected action, `destructive` for attempts to break the system.
- The expected result states concrete values (exact error message, HTTP status, URL), not
  "an error is displayed".

## Qase

- Suites are two levels: `<folder name>.<sub-suite>` in `qase_suite`, e.g. `User & Auth.Logout`.
  The parent suite is the story's folder; the sub-suite is a short name of the story's feature
  (one story = one sub-suite), so a feature area with many cases stays readable.
- Case lifecycle:
  1. **Draft.** Generated cases go into a `## Test cases` section of the story, before
     `## Open questions`, in the exact format above (the sync script parses it).
  2. **Approval.** The user reviews the drafts and sets `test_cases_approved: true`.
  3. **Push.** `scripts/qase_sync.py` pushes the cases of approved stories, writes their keys into
     `qase_cases` (`[TF-2, TF-3]`), sets `status: analyzed` and removes the `## Test cases`
     section. From then on Qase is the source of truth for those cases; change them there.
- Automated tests reference cases by the number of the key: `TF-11` → `@qase.id(11)`.
- Don't create or change anything in Qase unless explicitly asked, or unless the user approved the
  story (`test_cases_approved: true`), which counts as the request to push it.
- Push to Qase only with `scripts/qase_sync.py`, never with hand-written API calls or MCP:
  - `python3 scripts/qase_sync.py "<story path>" --dry-run`: validates the drafts and prints the
    payload, sends nothing. Works on stories that are not approved yet.
  - `python3 scripts/qase_sync.py --approved`: pushes every approved story that still has drafts.
  - `python3 scripts/qase_sync.py "<story path>"`: pushes one story; refuses if it isn't approved.
  - `python3 scripts/qase_sync.py --sync`: brings every story's `qase_cases` in line with Qase:
    drops the cases deleted there and adds the ones created by hand in the story's `qase_suite`
    (cases in a parent or unrelated suite are ignored). Read-only towards Qase; run it when the
    user asks to sync.
- Pushing is manual: run `--approved` when the user asks to push the approved stories (e.g.
  "push the approved ones"). Nothing runs automatically.
  - Cases already in Qase (by the keys in `qase_cases`, or by title in the target suite) are
    updated instead of duplicated: fields, steps and suite. `--no-update` only creates the missing
    ones. Renaming a case's title creates a new case.
- The script reads `QASE_API_TOKEN` and `QASE_PROJECT` (default `TF`) from `.env` in the vault
  root (template: `.env.example`); real environment variables override it. If the token is
  missing, the script asks for it interactively and saves it to `.env`. If the project doesn't
  exist in Qase, the script creates it. `.env` is the user's file: never read, print or edit it,
  and never write the token anywhere else.
- When running the script from Claude Code there is no interactive input, so a missing token makes
  it exit with an error. Then ask the user to run it once themselves in a terminal or in Thonny and
  paste the token.
- Qase field mapping: Severity, Priority, Type, Behavior → the same system fields; Level → layer
  (`API` → api, `UI` and `both` → e2e) and a tag; Preconditions → preconditions; each step → a
  step; Expected result and Test data → the last step; Description → description; story ID, AC
  and Level → tags (`US-3`, `AC-6`, `api`). Option IDs are looked up in Qase (`GET /system_field`), not hardcoded.

## Language

Talk to me in the chat language set in `CLAUDE.local.md` (personal and gitignored, so each user
of the repo has their own; read the file if it isn't already in context). If the file or the
`Chat language:` line is missing, ask at the start of the session which language I prefer, then
create the file with:

```markdown
# Personal settings (gitignored)

Chat language: <language>
```

To change the language later, I can just say so; update the line in `CLAUDE.local.md`.

Write all vault content (stories, test cases, frontmatter) in English.
