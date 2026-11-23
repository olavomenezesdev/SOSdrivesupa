## 1. Persist the provider transition

- [ ] 1.1 Add a Supabase migration for an authenticated, provider-assigned `accepted` → `in_progress` RPC; reject other actors/states and verify authorized, unauthorized, invalid-state, and idempotent calls.
- [x] 1.2 Add a typed `supabase_backend.py` wrapper for the new RPC and verify it calls the correct function, returns the persisted row, and surfaces backend errors.
- [x] 1.3 Update the provider's “Iniciar atendimento” transition to persist first and set `ATENDENDO` only after a confirmed `in_progress` response; verify failures retain `NO_LOCAL` and show an error.

## 2. Verify customer synchronization

- [x] 2.1 Add a regression test that polling an active request after the provider transition updates the customer to `in_progress` without clearing request or chat state.
- [ ] 2.2 Apply the migration in the configured Supabase project and manually verify with separate provider and customer sessions that starting service updates the customer's status on the next poll.

## 3. Run validation

- [x] 3.1 Run focused provider/customer/backend tests, `python -m reflex compile`, and `openspec validate --strict`; confirm no direct table UPDATE grant or unrelated RLS change was introduced.
