## Context

See `proposal.md` for the user-visible problem and `specs/service-request-lifecycle/spec.md` for the behavior contract. The authenticated role currently has SELECT but not UPDATE on `service_requests`; existing status changes use authenticated RPCs that validate the actor and request assignment. The customer already polls `service_requests.status` and presents `in_progress`.

## Goals / Non-Goals

**Goals:**
- Reuse the current request status field and authenticated RPC pattern.
- Persist the start transition before changing the provider's local phase.
- Keep the operation safe to retry if the database committed but the client did not receive the response.
- Avoid granting direct table UPDATE or broadening RLS.

**Non-Goals:**
- Add request columns, alter customer polling, expose provider coordinates, or change arrival/chat behavior.
- Change the existing acceptance, release, cancellation, or completion transitions.

## Decisions

1. **Add one provider-scoped RPC in a migration.** The function checks `auth.uid()`, verifies that the actor's profile role is `prestador`, and updates only a request assigned to that actor. It transitions `accepted` to `in_progress`; if the same assigned request is already `in_progress`, it returns that row unchanged. Other states or assignments are rejected. This follows the existing `SECURITY DEFINER` RPC pattern instead of granting table updates.

2. **Call the RPC at the local “No local” → “Atendendo” transition.** Add a small Python wrapper using the existing authenticated transition helper. The Reflex state changes to `ATENDENDO` only after the returned row confirms `in_progress`; on failure, it remains `NO_LOCAL` and reports the error. This prevents the provider screen from claiming a transition that the database did not confirm.

3. **Reuse customer polling as-is.** The client already polls active requests and maps `in_progress` to “Atendimento em andamento”. No new status, endpoint, or additional polling loop is needed.

## Risks / Trade-offs

- [A lost RPC response can leave the provider unsure whether start succeeded] → Make the operation idempotent for the assigned request already in `in_progress`.
- [A privileged RPC could allow an unauthorized status change if its checks are incomplete] → Require an authenticated `prestador`, enforce matching `provider_id` and valid status in the database, use an empty `search_path`, revoke default execution, and grant execution only to `authenticated`.
- [A deployment without the migration would reject the RPC call] → Apply the migration before deploying the Python change; surface the failure and leave the provider phase unchanged.

## Migration Plan

1. Apply the migration that creates and grants the narrowly scoped RPC.
2. Deploy the Python wrapper and provider-state call.
3. Verify that starting an assigned request produces `in_progress` in Supabase and that the customer sees “Atendimento em andamento” on the next poll.
4. To roll back, revert the Python changes and revoke/drop the RPC. Existing `in_progress` rows remain compatible with current release and completion RPCs; no data backfill is required.
