---
id: US-2
status: analyzed
qase_suite: User & Auth.Login
qase_cases:
  - TF-23
  - TF-24
  - TF-25
  - TF-26
  - TF-27
  - TF-28
  - TF-29
  - TF-30
  - TF-31
  - TF-32
  - TF-33
  - TF-34
  - TF-35
  - TF-36
  - TF-37
  - TF-38
test_cases_approved: true
code_commit: 4e3851b
code_paths:
  - services/users-service/app/main.py
  - services/users-service/app/security.py
  - services/users-service/app/schemas.py
  - services/users-service/app/config.py
  - services/gateway/app/main.py
  - ui/src/hooks/useAuth.tsx
  - ui/src/api/client.ts
  - ui/src/components/Navbar.tsx
  - ui/src/pages/LoginPage.tsx
related:
  - "[[User registration]]"
---

## Description

**As an** already registered user,  
**I want to** log in to the system using my email and password,  
**So that** I can access my personal account and secure data.

## Acceptance Criteria

- **AC-1:** The `Email` field accepts only a valid email format.
- **AC-2:** If the credentials are wrong, the error message _"Invalid email or password"_ is shown.
- **AC-3:** On successful login, an access token is generated, and it contains the user's roles.
- **AC-4:** Characters in the `Password` field are masked by default.
- **AC-5:** After successful login, the user is redirected to the Market page (`/`) and sees their name in the NavBar.

## Open questions

- **AC-2:** Does "wrong credentials" cover both an unregistered email and a wrong password for an existing email? Both currently return `401` _"Invalid email or password"_ (`services/users-service/app/main.py:107`).
- **AC-3:** "User roles" are the `is_admin` and `is_seller` claims in the token (`services/users-service/app/security.py:33`). Should the story name them explicitly? A refresh token is also issued, but the story doesn't mention it.
- **AC-1:** Validation is native to the browser (`type="email"`). Is a custom error message expected?
- **AC-5:** The NavBar shows the user's full name (`nav-user-name`, `ui/src/components/Navbar.tsx:45`). Is this the expected name format?
- What should happen when an already logged-in user opens `/login`?
- Is the email case-insensitive at login?
- **AC-1:** The browser's `type="email"` check accepts `user@domain` (no top-level domain) and silently trims surrounding spaces, while the API doesn't validate the format at login at all (any `username` gives `401`). Which values count as a "valid email format"?
- **AC-2:** There is no rate limiting or lockout after repeated failed logins. Is brute-force protection in scope?
- **AC-5:** After login the user always goes to `/` (`ui/src/pages/LoginPage.tsx:21`), even when they were sent to `/login` from a protected page such as `/cabinet`. Should they return to the page they came from?
