## Why

The customer dashboard stops polling as soon as a provider accepts a request, so the customer cannot reliably see later persisted status changes or terminal outcomes. The provider's detailed arrival phases and live coordinates currently exist only in the provider's Reflex session, so the client must not imply that it can see a route or stage that Supabase does not expose.

## What Changes

- Keep polling the customer's existing request while it is active and render its status from the values already stored in Supabase.
- Present pending, accepted, in-progress, completed, and cancelled requests distinctly, retaining the existing price, distance, and messaging behavior where applicable.
- Preserve the customer's own map marker and controls; do not draw a provider marker or route without authorized, shared provider coordinates.
- Keep provider-specific arrival phases out of the customer progress display unless a persisted status already represents them.
- Do not change database schema, migrations, RLS policies, or provider workflow.

## Capabilities

### New Capabilities

- `customer-request-tracking`: Poll and present the customer-owned service request using only existing Supabase fields and status values.

### Modified Capabilities

None.

## Impact

- Affects client polling, request-state rendering, and the status card in `sosdrive.py`, request retrieval in `supabase_backend.py`, customer-scoped styles in `styles.py`, and focused tests.
- Reuses the existing participant-scoped `fetch_service_request` query and request lifecycle.
- Database fields and authorization remain unchanged. Current persistable states are `pending`, `accepted`, `in_progress` (recognized by active-request queries, though no current provider action writes it), `completed`, and `cancelled`. Provider profile names and current coordinates are not available to the customer under the existing RLS and schema, so the UI must use a generic provider label and omit the live route.
- This is within the MVP's request tracking and location scope. It changes no persisted data, so rollback consists of reverting the application changes; no data rollback is required.
