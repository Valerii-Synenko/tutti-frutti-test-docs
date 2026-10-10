---
id: US-3
status: analyzed
qase_suite: User & Auth.Logout
qase_cases:
  - TF-2
  - TF-3
  - TF-4
  - TF-5
  - TF-6
  - TF-7
  - TF-8
  - TF-9
  - TF-10
  - TF-11
  - TF-12
  - TF-13
  - TF-14
  - TF-15
  - TF-16
  - TF-17
  - TF-18
  - TF-19
  - TF-20
  - TF-21
  - TF-22
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
  - ui/src/hooks/useCart.tsx
  - ui/src/pages/CabinetPage.tsx
  - ui/src/pages/OrdersPage.tsx
related:
  - "[[Registered user login]]"
  - "[[User registration]]"
---

## Description

**As a** logged-in user,  
**I want to** log out of my account,  
**So that** nobody else using this browser can act on my behalf or see my personal data.

## Acceptance Criteria

### Logout control

- **AC-1:** The `Log out` button is shown in the NavBar on every page only while the user is logged in. A logged-out visitor sees the `Log in` link instead.

### Successful logout

- **AC-2:** After clicking `Log out`, the user is redirected to the Market page (`/`).
- **AC-3:** After logout, the NavBar no longer shows the user's name, the `My Orders` link or the `Log out` button, and shows the `Log in` link.
- **AC-4:** After logout, the cart is cleared, so the next person who logs in on this browser does not inherit it.
- **AC-5:** After logout, the browser `Back` button does not return the user to a page that was rendered while they were logged in.

### Session termination

- **AC-6:** Logout revokes the user's refresh token on the server. A revoked refresh token can no longer be exchanged for a new access token.
- **AC-7:** After logout, opening a page that requires authentication (e.g. `/cabinet`) redirects the user to the Login page (`/login`).
- **AC-8:** The logout endpoint requires a valid access token. A request without one is rejected with `401`.

## Open questions

- **AC-6:** Only the refresh token is revoked. The access token stays valid until it expires (15 min by default) and is not tracked server-side (`services/users-service/app/main.py:197`). If the access token has leaked, it can still be used for up to 15 minutes after logout. Is that acceptable?
- **AC-6:** The refresh token in the request body is optional, and an invalid or malformed one is silently ignored with `204` (`services/users-service/app/main.py:202`). Should the API reject a malformed refresh token instead?
- **AC-6:** The API does not check that the refresh token belongs to the user whose access token authenticates the call (`services/users-service/app/main.py:200`). User A can revoke user B's refresh token. Is this intended?
- **AC-6:** Logging out on one device does not end sessions on other devices (no "log out everywhere"). Is that in scope?
- **AC-2 / AC-6:** The UI fires the logout request without waiting for it and ignores errors (`ui/src/hooks/useAuth.tsx:86`). If the request fails (network error, expired access token), the user is logged out locally but the refresh token stays valid. Is this acceptable?
- **AC-8:** If the access token has already expired, the logout call returns `401`, so the refresh token is never revoked, although the UI still logs the user out locally.
- **AC-7:** `/cabinet` redirects to `/login` (`ui/src/pages/CabinetPage.tsx:76`), but `/orders` has no such redirect: the page calls `GET /orders`, ignores the `401` and shows `empty-orders-message` "No orders yet." (`ui/src/pages/OrdersPage.tsx:13`). What should a logged-out user see on `/orders`?
- **AC-4:** The cart is cleared only by the `Log out` button (`ui/src/components/Navbar.tsx:14`). Should it also be cleared when the session ends in another way (e.g. tokens expire)?
- **AC-6:** Logout invalidates the session only through the client: an attacker who has the access token can still call `GET /auth/me` and other endpoints after logout. TC "Accept access token after logout until it expires" documents this; should it become a negative case instead?
- Is a confirmation dialog expected before logout? None exists today.
- Is any message (e.g. "You have been logged out") expected after logout? None is shown today.
