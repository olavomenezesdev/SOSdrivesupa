## Why

When a provider starts the service, the UI changes to “Atendendo” only in that provider's Reflex session. The request remains `accepted` in Supabase, so the customer's existing polling cannot display the in-progress status.

## What Changes

- Add a narrowly scoped, authenticated Supabase RPC that changes an assigned provider's request from `accepted` to `in_progress`.
- Call that RPC when the provider advances from “No local” to “Atendendo”; update the local phase only after persistence succeeds.
- Use the customer's existing polling and status presentation to show `in_progress`.
- Keep direct table updates disabled and validate provider role, assignment, and current request status in the RPC.

## Capabilities

### New Capabilities

- `service-request-lifecycle`: Persist and expose the provider's transition into active service.

### Modified Capabilities

None.

## Impact

- Affects a Supabase migration, the RPC wrapper in `supabase_backend.py`, the provider transition in `sosdrive.py`, and focused tests.
- Reuses the existing `service_requests.status` field, provider assignment, and customer polling; no new table or column is needed.
- Changes the `Chamado` lifecycle and the `Prestador` action, both within the SOS Drive MVP.
- Rollback can remove the RPC and revert the application changes. Existing `in_progress` rows remain valid because current release and completion transitions already accept that status.
