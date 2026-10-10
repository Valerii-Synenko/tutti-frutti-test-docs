---
name: review-story
description: Review a user story written by a person and suggest improvements (vague wording, gaps, untestable ACs) as ready-to-paste proposals under "## Suggested improvements"; also applies the proposals the user accepts. Use when asked to review, analyse or improve a story ("review the story", "проаналізуй сторі", "застосуй пропозиції").
argument-hint: <story name> | apply <items>
---

# Review a user story

Review comes before test design. The goal is a story that can be tested without guessing.
A good story needs no suggestions: say so instead of inventing some.

## 1. Read

- The story file in `user-stories/<area>/<name>.md`, and the stories in its `related` list.
- The product code in `.product/tutti-frutti` only where a rule needs checking (page names,
  existing behaviour). Mismatches with the code are open questions, not suggestions.

## 2. Check

- **Description:** a real role, one user goal, a value that explains why (INVEST: independent,
  valuable, small enough for one Qase sub-suite, testable). Several goals → suggest a split.
- **Each AC:** one observable behaviour with a concrete outcome: exact texts, limits, statuses,
  pages. Flag vague words ("valid", "secure", "fast", "properly", "etc.", "user-friendly").
- **Gaps:** negative paths, boundaries, empty and error states, roles and permissions, what
  happens to related data, behaviour on server errors.
- **Consistency:** page and element names as in the UI (routes table in `CLAUDE.md`), terms and
  rules shared with related stories, no contradictions between ACs.
- **Testability:** every AC can be verified by a test; if not, propose a measurable wording.

## 3. Write the suggestions

Add a `## Suggested improvements` section right after `## Acceptance Criteria` (before any
`## Test cases` and `## Open questions`). One numbered item per suggestion:

```markdown
## Suggested improvements

1. **AC-4** (should): "valid email format" doesn't say which formats count.
   Proposed: "The `Email` field accepts addresses of the form `name@domain.tld`; otherwise the
   error _"Please enter a valid email address"_ is shown under the field."
2. **New AC** (must): nothing covers a server error on submit.
   Proposed: "**AC-12:** If the server fails, the form shows _"Something went wrong. Please try
   again."_ and keeps the entered data."
```

- Weight: `must` (the story can't be tested or is wrong without it), `should` (removes ambiguity
  or a likely gap), `nice` (wording, structure).
- A proposal is ready-to-paste text in the story's style, not advice like "make it clearer".
- A question only the author can answer (a business decision, a mismatch with the code) goes to
  `## Open questions` with a file and line reference, not here.
- Don't touch the story text, the status or `test_cases_approved` in this step.

Reply with a short summary: how many items per weight and the `must` ones in one line each.

## 4. Apply (only on the user's command)

When the user accepts items ("apply 1 and 3", "застосуй усі must"):
- Edit the story text exactly as proposed. Renumber ACs only if asked.
- Remove the applied items from `## Suggested improvements`; remove rejected ones if the user
  says so. Delete the section when it's empty.
- If the story already has draft test cases, say which ones the change affects. If it's already
  in Qase (`qase_cases` not empty), say that the cases there may need updating too.
- Never apply suggestions on your own, and leave `status` to the user (`draft` → `ready`).
