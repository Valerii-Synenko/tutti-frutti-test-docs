---
id: US-1
status: analyzed
qase_suite: User & Auth.Registration
qase_cases:
  - TF-40
  - TF-41
  - TF-42
  - TF-43
  - TF-44
  - TF-45
  - TF-46
  - TF-47
  - TF-48
  - TF-49
  - TF-50
  - TF-51
  - TF-52
  - TF-53
  - TF-54
  - TF-55
  - TF-56
  - TF-57
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
  - ui/src/pages/RegisterPage.tsx
related:
  - "[[Registered user login]]"
---

## Description

**As an** unregistered visitor,  
**I want to** create an account using my email and a secure password,  
**So that** I can become a registered user and access personalised features of the system.

## Acceptance Criteria

### Form layout

- **AC-1:** The registration form contains the mandatory fields `Full Name`, `Email` and `Password`, and the `Create account` button.
- **AC-2:** The form contains a link/button that takes already registered users to the Login page.

### Full Name and Email validation

- **AC-3:** The `Full Name` field cannot be empty.
- **AC-4:** The `Email` field accepts only a valid email format (e.g. `name@domain.com`). If the format is invalid (e.g. missing `@` or domain), the error _"Please enter a valid email address"_ is shown under the field.
- **AC-5:** The email address must be unique. If a user submits an email that is already registered, the error _"An account with this email already exists"_ is shown after submission.

### Password requirements

- **AC-6:** The password must meet all of the following:
    - at least 8 characters long;
    - at least one uppercase letter (A–Z);
    - at least one lowercase letter (a–z);
    - at least one digit (0–9);
    - at least one special character (e.g. `@`, `#`, `$`, `%`).
- **AC-7:** If any rule from AC-6 is not met while the user is typing, the dynamic hint/error _"Password does not meet complexity requirements"_ is shown.
- **AC-8:** Characters in the `Password` field are masked by default.

### Successful registration

- **AC-9:** When the user clicks the active `Create account` button with valid data, the user account is created in the database.
- **AC-10:** The user is logged in automatically and redirected to the Market page (`/`).
- **AC-11:** An authorisation (session) token containing the new user's default role (buyer) is generated in the background.

## Open questions

- **AC-4:** The UI relies on native browser validation (`type="email"`), so the browser shows its own tooltip instead of _"Please enter a valid email address"_ under the field (`ui/src/pages/RegisterPage.tsx`). Which behaviour is expected?
- **AC-5:** The API returns `409` with _"Email already registered"_, not _"An account with this email already exists"_ (`services/users-service/app/main.py:88`). Which text is correct?
- **AC-5:** Is the uniqueness check case-insensitive (`User@x.com` vs `user@x.com`)? Are leading/trailing spaces trimmed?
- **AC-6:** Only the length is enforced (8–128, `services/users-service/app/schemas.py:8`; UI `minLength={8}`). The uppercase, lowercase, digit and special-character rules are not implemented.
- **AC-6:** The story has no maximum password length. The code limits it to 128 characters.
- **AC-7:** There is no dynamic hint in the UI. When exactly should it appear (while typing, on blur, on submit), and where?
- **AC-3:** Is a name made only of spaces valid? The code currently accepts it. The maximum length (255 in the code) is not in the story.
- **AC-9:** "Active `Create account` button" implies the button can be inactive. When should it be disabled? Today it is disabled only while the request is in progress.
- **AC-8:** "Password fields" was plural in the original text, but the form has a single password field. Is a "Confirm password" field expected?
- **AC-11:** There is no "buyer" role in the code. The access token carries `is_admin` and `is_seller` flags, both `false` for a new user (`services/users-service/app/security.py:33`). Should the story describe these claims instead?
- **AC-10 / AC-11:** `POST /auth/register` returns no tokens; the UI logs in with a second call right after it (`ui/src/hooks/useAuth.tsx:76`). If that second call fails, the account exists but the user is not logged in and sees an error on the registration form. Is that acceptable, or should registration return the tokens itself?
