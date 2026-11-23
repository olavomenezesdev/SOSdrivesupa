## Context

See `proposal.md` for motivation and `specs/customer-request-tracking/spec.md` for the user-visible contract. The customer currently polls `fetch_service_request` every five seconds only while its local status is `searching`, then switches to `matched` after seeing a `provider_id`. The request row already contains `status`, `estimated_price`, and `distance_km`, and participant RLS permits the request owner to read it.

The current database lifecycle writes `pending` on creation and provider release, `accepted` on provider acceptance, `completed` on completion, and `cancelled` when the customer cancels a still-pending request. `in_progress` is accepted by existing active-request queries and release/completion RPC guards, but the current provider UI does not write it. `A_CAMINHO`, `NO_LOCAL`, and `ATENDENDO` are provider-session state; arrival currently sends a chat message rather than persisting a status. Provider coordinates are also kept only in the provider's Reflex session. The profiles SELECT policy is owner-only, so the customer cannot fetch the provider's profile name.

## Goals / Non-Goals

**Goals:**
- Keep the existing participant-authorized request fetch running through active persisted states and stop at terminal states.
- Derive the customer status presentation from the row, preserving request price, distance, and the independent chat state.
- Keep cancellation available only while the existing cancellation RPC can succeed.
- Preserve the client map, marker, recenter action, responsive layout, and provider workflow without implying access to unavailable data.

**Non-Goals:**
- Persist new provider lifecycle phases, provider coordinates, or provider names.
- Add a provider marker or route from mock/session-local coordinates.
- Change Supabase schema, migrations, RLS policies, or RPCs.
- Infer arrival or service progress by parsing chat messages.

## Decisions

1. **Use the existing authenticated request lookup as the source of truth.** Refresh the same request by ID while it is `pending`, `accepted`, or `in_progress`; treat `completed` and `cancelled` as terminal. A provider release returns the row to `pending`, so the customer continues polling and sees the searching state. Unknown values retain a neutral status rather than being coerced into a known phase. This reuses the existing backend query and participant RLS instead of introducing a second access path.

2. **Separate server status from local presentation state.** Keep the request ID and the existing chat state intact while active. Update only the current server status and returned price/distance when a poll succeeds. Completion retains a dismissible summary; cancellation clears the active request state while showing the cancellation outcome. A fetch error keeps the last known request values and reports an error without treating the request as terminal.

3. **Map only statuses that the row can express.** `pending` means searching, `accepted` means a provider has accepted and is on the way, `in_progress` means service is in progress, `completed` is the completed summary, and `cancelled` is cancellation. Do not claim a separate “No local” stage: the current provider action does not persist one. The compact progress indicator must not imply more granular progression than the persisted value supports.

4. **Do not fetch provider identity or position through an unauthorized or fabricated source.** Keep the customer's current map behavior unchanged. The existing provider position is session-local and has no shared database field; profiles are readable only by their owner. Therefore no provider marker, route, or provider name is rendered in this change. A future route requires a separately approved, authorized source for provider coordinates.

5. **Align controls with existing server rules.** Keep messaging available while the request is active. Show cancellation only for a pending request with no assigned provider, matching the current cancellation RPC; an accepted or in-progress request must not present a cancellation action that the backend rejects.

## Risks / Trade-offs

- [Polling adds reads while a request remains active] → Keep the existing five-second interval, issue at most one lookup per poll cycle, and stop on terminal state or explicit clear.
- [Provider progress is coarser than the requested visual steps] → Show only persisted phases and explicitly omit a confirmed arrival phase until the provider flow persists one.
- [Provider release changes an active row back to `pending`] → Present it as searching again and continue polling instead of treating release as cancellation.
- [The customer cannot see provider name or live coordinates under current RLS/schema] → Use a generic status message and leave the customer map unchanged; do not broaden access or invent coordinates.

## Migration Plan

No database migration or data migration is required. Rollback by reverting the application and test changes; there are no persistent writes or new fields to reverse.
