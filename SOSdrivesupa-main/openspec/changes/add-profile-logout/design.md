## Context

See `proposal.md` for the user need and `specs/authentication/logout/spec.md` for the observable behavior. `AuthState` already provides `logout()` and `clear_session()`: logout clears the current state and redirects to `/login`; the profile header currently offers only role-aware “Voltar” navigation.

## Goals / Non-Goals

**Goals:**
- Reuse the existing authenticated-state cleanup and redirect behavior.
- Make “Sair” available from the profile header without confusing it with “Voltar”.
- Preserve profile, vehicle, and service data in Supabase.

**Non-Goals:**
- Add a logout endpoint, change authentication providers, revoke other sessions, or modify database schema/data.
- Change how role-specific “Voltar” navigation works.

## Decisions

- Bind the profile “Sair” button directly to `AuthState.logout`. This uses the established `clear_session()` path to clear current Reflex session credentials and user data before redirecting. A new handler would duplicate existing behavior and risk incomplete cleanup.
- Place “Sair” at the opposite end of the existing profile header from “Voltar”; use a logout icon and a restrained destructive/outline treatment so the actions remain visually distinct.
- Verify state cleanup and redirect through focused unit tests, and verify that the profile page renders both actions. No API or database test is required because the flow does not call either system.

## Risks / Trade-offs

- [The existing logout clears the current Reflex state but does not revoke refresh tokens for other sessions] → Keep this change scoped to the current session as requested; global session revocation would require a separate authentication/security decision.
- [A header layout could crowd on narrow screens] → Allow the header action group to wrap or retain adequate spacing at mobile widths.

## Migration Plan

No data migration is required. Rollback consists of removing the profile “Sair” button and its presentation styles; the existing `AuthState.logout()` behavior remains available to other callers.
