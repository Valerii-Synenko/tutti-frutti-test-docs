---
name: generate-cases
description: Design test cases for a user story - check the story against the product code, apply test design techniques along the test pyramid, and write draft cases into the story's "## Test cases" section in the repo format. Use when asked to generate, write, add or fix test cases for a story ("generate test cases for <story>").
argument-hint: <story name>
---

# Generate test cases for a story

## 1. Before you start

- Read the story and its `related` stories.
- If the story has `## Suggested improvements` with `must` items still open, stop and ask the
  user to decide on them first (see the `review-story` skill).
- If the story already has cases in Qase (`qase_cases` not empty), Qase is the source of truth:
  add only new cases as drafts and say so; never re-create the existing ones.

## 2. Check against the code

Look in `.product/tutti-frutti` at how each AC is actually implemented: endpoints, validation
rules (e.g. pydantic `Field` limits), exact error messages, status codes, redirects, visible
texts and labels in the UI, `data-testid`s. Record every mismatch and every untestable AC under
`## Open questions` with a file and line reference (`services/users-service/app/main.py:104`).
The story text itself stays unchanged.

## 3. Design

- **Techniques:** equivalence partitioning, boundary values (e.g. password length 7/8/9),
  decision tables for combinations of rules, state transitions for listing and order statuses.
  Cover positive and negative scenarios.
- **Traceability:** every case references the AC(s) it verifies; every AC has at least one case.
- **Level:** `API` (via the gateway, `http://localhost:8080`), `UI` (Playwright) or `both`. Check
  JWT contents (roles, claims) at the API level.
- **Test pyramid:** most cases at the API level (business rules, validation, status codes, error
  messages, permissions, data combinations), fewer at the UI level. Don't repeat at the UI what
  an API case already proves; a UI case checks what only the browser shows: page flow and
  redirects, what's visible on the page, form behaviour, browser storage, navigation. It's a
  guideline, not a quota: write an important UI case (key user journey, security-relevant screen
  state, UI-only rule). Unit tests are out of scope.
- **Requirement vs code:** the expected result follows the story. Where the code does something
  else today, say "Expected to fail today: ..." and point to the open question. Where the story is
  silent and only current behaviour can be checked, say "current behaviour; see Open questions".

## 4. Write

Put the cases in a `## Test cases` section before `## Open questions`, in exactly this format
(`scripts/qase_sync.py` parses it):

```markdown
### TC: <Short imperative title>
- [ ] Approved
- [ ] Not relevant
- **Description:** Checks that <condition> leads to <expected behaviour>.
- **AC:** AC-2
- **Level:** API | UI | both
- **Severity:** blocker | critical | major | normal | minor
- **Priority:** high | medium | low
- **Type:** functional | smoke | regression | security | usability | performance | acceptance | compatibility | integration | exploratory | other
- **Behavior:** positive | negative | destructive
- **Preconditions:** A registered user exists with full name `Jane Tester`.
- **Steps:**
  1. Login as the user
     Data:
     email: `jane-<timestamp>@example.com`
     password: `Password1!`
     Expected:
     1. The user is redirected to the Market page.
     2. The NavBar shows "Jane Tester".
  2. Log out
     Expected:
     1. The `Log in` link is visible.
```

The steps are written the way the autotests are (`with qase.step("Login as the user"):`), so a
step title can be copied into `qase.step(...)` as is:

```python
@qase.id(37)
def test_login(self, login_page, user):
    with qase.step("Login as the user"):
        market_page = login_page.goto().login(user.email, user.password)
        expect(market_page.nav_bar.user_link).to_have_text(user.full_name)
```

Rules:
- **Title:** short, imperative, unique within the suite (the Qase case is matched by it).
- **Checkboxes:** every draft starts with both unticked, right under the title. They are the
  user's decision; never tick them. If you rewrite a draft the user already approved, untick
  `Approved`.
- **Description:** one or two plain sentences for a human: what the case checks and why it
  matters; no steps or IDs (story, AC and level go to tags).
- **Severity** = impact of a failure. **Priority** = how soon it must run (high = smoke-level core
  flow, low = edge cases). **Behavior:** `positive` valid flow, `negative` invalid input or an
  unauthorised/unexpected action, `destructive` attempts to break the system.
- **Steps** are business-level actions, one per `qase.step`: "Login as the user", "Log out",
  "Register via the API with an invalid email" — not single clicks ("open / type / click" is one
  step). A step title is a short imperative phrase with no concrete values.
- **Data** (optional, per step): every concrete value the step uses — endpoint, fields, inputs,
  browser. One `key: value` per line; alternative values as a bullet list with a heading line
  ("Emails:", "Passwords:"). Never put the values in the step title.
- **Expected** (per step, at least one step has it): what is checked right after that step, as a
  numbered list, one check per item, even for a single check. Phrase it from the user's side ("The
  user is redirected to the Market page", "The response status is `201`") with concrete values
  (exact message, status, field value), never "an error is displayed". No separate "Check that..."
  steps: checks go into the Expected block of the step they follow.
- **UI elements:** named as the user sees them, by visible text or label, in backticks: the
  `Log out` button, the `Email` field, the `Cart` link; elements without text are described ("the
  user's name in the NavBar", "the cart counter on the `Cart` link"). Never `data-testid`s.
- **Pages, not routes,** in steps, preconditions and data: "Open the My Orders page" (Market,
  Fruit detail, Login, Registration, Cart, My Orders, Cabinet). A URL only where the URL itself is
  checked: "The URL is `/login`".
- **Code formatting** for technical values: URLs, status codes, `localStorage` keys, JSON, claims.

## 5. Finish

- Record the code baseline for the `code-impact` skill: `code_commit` = the product commit you
  checked (`git -C .product/tutti-frutti rev-parse --short HEAD`), `code_paths` = the files the
  story depends on (endpoints, schemas, config, pages, hooks, components), as a block list.
- Validate: `python3 scripts/qase_sync.py "<story path>" --dry-run` must parse every case.
- Reply with: number of cases and the API/UI split, a coverage table per AC, cases that are
  expected to fail today or document current behaviour, and new open questions. End with: review
  the drafts, edit them if needed, tick `Approved` or `Not relevant` on each, then ask to push
  (the `qase-push` skill).
