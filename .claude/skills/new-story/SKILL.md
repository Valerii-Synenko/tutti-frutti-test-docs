---
name: new-story
description: Create a new user story file from templates/user-story.md with the next free US-<n> id, the Qase sub-suite and wikilinks to related stories. Use when the user asks to create or write a new user story ("створи юзер сторі", "new story for ...").
argument-hint: <feature area> / <story name or topic>
---

# Create a new user story

1. **Area and name.** The folder under `user-stories/` is the feature area and the parent Qase
   suite (e.g. `User & Auth`). The file name is the story name (`User logout.md`); one story per
   file. If the topic is ambiguous (e.g. "user" covers registration, login, profile...), check
   which stories already exist and ask which flow to describe.
2. **Id.** The next free number across all folders: find the highest `id: US-<n>` and add 1. No
   leading zeros.
3. **Frontmatter** from `templates/user-story.md`:
   - `status: draft`
   - `qase_suite: <area>.<short feature name>`, e.g. `User & Auth.Logout`
   - `qase_cases: []`, `test_cases_approved: false`
   - `related:` wikilinks to related stories as a block list (`  - "[[Registered user login]]"`)
4. **Body:** Description (As a / I want to / So that) and numbered ACs, grouped under `###`
   headings when there are many. Base them on how the product actually behaves
   (`.product/tutti-frutti`): exact texts, limits, pages, so the story is testable. Name pages and
   elements as the UI shows them.
5. **Open questions:** whatever the code leaves unclear or does questionably, with file and line
   references.

Write in English. Since you wrote this story yourself, say so in the reply and suggest the user
reviews the AC wording before moving it to `ready`; offer test cases next (the
`generate-cases` skill).
