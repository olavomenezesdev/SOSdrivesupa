## 1. Profile Logout Action

- [x] 1.1 Add a “Sair” button to the profile header, bind it to the existing `AuthState.logout` flow, and verify both “Voltar” and “Sair” render as distinct actions.
- [x] 1.2 Style the logout action and header layout for desktop and mobile, then verify the button remains visible and distinguishable at narrow widths.

## 2. Session and Route Verification

- [x] 2.1 Add a focused backend-state test for the existing logout flow, verifying auth tokens and user data are cleared and the event redirects to `/login`.
- [x] 2.2 Run the focused profile/auth tests and Reflex compilation, verifying the profile logout interaction does not modify persisted profile or vehicle data.
