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
  qase_sync.py             ← pushes test cases to Qase, syncs qase_cases
  code_impact.py           ← finds stories whose product code changed since code_commit
.claude/skills/            ← workflows: new-story, review-story, generate-cases, qase-push,
                             sync-cases, code-impact
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
code_commit: 4e3851b     # product commit the story was analysed against
code_paths: []           # product files the story depends on (for code-impact)
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
- Change `status` only when told to. `analyzed` is set by the sync script once no draft cases are
  left in the story.

## Working with stories

- **Don't rewrite requirements.** The story text belongs to its author. Unclear points,
  contradictions and mismatches with the code go under `## Open questions` (with a file and line
  reference); the text changes only when the user accepts a suggested improvement.
- **Workflows are skills** in `.claude/skills/`; follow the matching one:

| Skill | When |
|---|---|
| `new-story` | create a story from the template |
| `review-story` | review a story written by a person, suggest and apply improvements |
| `generate-cases` | design draft test cases (test design rules and the case format live here) |
| `qase-push` | push approved cases to Qase |
| `sync-cases` | bring `qase_cases` in line with Qase after manual changes there |
| `code-impact` | find stories and cases affected by product code changes since `code_commit` |

## Qase

- Suites have two levels: `<folder name>.<sub-suite>` in `qase_suite`, e.g. `User & Auth.Logout`
  (one story = one sub-suite).
- Case lifecycle: drafts in the story's `## Test cases`, each with two checkboxes:
  `- [ ] Approved` and `- [ ] Not relevant`. The user ticks them (and may edit a draft before
  approving it). `qase-push` pushes the approved drafts with the user's edits, appends their keys
  to `qase_cases` and removes them from the story; not relevant drafts are removed without
  pushing; undecided ones stay. When no drafts are left, `status` becomes `analyzed`. Pushed
  cases live in Qase from then on.
- The checkboxes belong to the user: never tick them. When you rewrite a draft, untick
  `Approved` so it gets reviewed again.
- Automated tests reference cases by the key's number: `TF-11` → `@qase.id(11)`.
- Change Qase only through `scripts/qase_sync.py` and only when the user asks (ticking `Approved`
  doesn't push by itself). Never use hand-written API calls or the Qase MCP server.
- `.env` holds the user's Qase token (gitignored): never read, print or edit it, and never write
  the token anywhere else.

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
