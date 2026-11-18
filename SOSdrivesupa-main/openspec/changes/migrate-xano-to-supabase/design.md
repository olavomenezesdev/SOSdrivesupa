# Design

## Context

See `proposal.md` for motivation and scope. The Reflex application currently calls Xano directly from helpers in `sosdrive.py`; the repository contains Xano definitions for authentication, profiles, profile-photo upload, vehicles, service requests, acceptance, messages, and event logs. Supabase will start with an empty application dataset. Existing Xano accounts, records, event logs, and stored photos remain untouched and are not imported by this change.

The migration must preserve Python/Reflex, current client/provider flows, and backend-enforced authorization. Credentials for a real Xano or Supabase workspace are not included in the repository and must not be requested in chat or committed.

## Goals / Non-Goals

**Goals:**

- Replace runtime Xano dependencies with Supabase Auth, PostgreSQL, and Storage while preserving the existing application contract and user journeys.
- Start the new Supabase application with no historical or fabricated records; create new records only through authenticated application flows.
- Support profile-photo uploads to owner-scoped Supabase Storage for newly registered users.
- Enforce user ownership, participant visibility, provider role, and request state transitions in the database/backend.
- Keep credentials and migration administration isolated from the browser and normal user requests.
- Provide verification and rollback steps that prevent silent data loss or an unsafe switch back after new writes.

**Non-Goals:**

- Add product features or change the client/provider UX.
- Add payments, advanced history, or a new rating workflow. The repository documents ratings in the domain model but has no Xano rating table definition; any live rating data must be discovered and included in migration scope rather than silently discarded.
- Delete the Xano workspace or its data as part of initial cutover.
- Use dual-write as a default migration strategy; it risks inconsistent authorization and divergent records.

## Decisions

### Use Supabase Auth, PostgreSQL, and Storage behind the existing Reflex app

Keep the UI and Python/Reflex application structure. Replace the Xano transport helpers with a small backend Supabase integration/repository boundary, and use the official Python Supabase client for Auth, PostgREST, and Storage rather than moving application logic into a new frontend or a second backend framework. Keep environment configuration in the backend.

**Alternatives considered:** keeping Xano as a compatibility proxy would retain the current rate-limit and operational dependency; calling Supabase from browser components would expose credentials and bypass the project's backend authorization rule.

### Use Auth UUIDs and native generated IDs for new application records

Use `auth.users.id` as the stable identity referenced by a `profiles` row. Put the business role (`cliente` or `prestador`) and profile fields on that user-linked profile. Use PostgreSQL identity columns for vehicles, requests, acceptances, and messages created after signup. Do not create legacy-ID mappings or import existing event logs because this change starts with an empty Supabase application dataset.

**Alternatives considered:** importing Xano IDs and maintaining identity maps would add migration complexity for records explicitly excluded from this change; using Auth UUIDs as all business-record keys would require broader UI changes without a product benefit.

### Enforce authorization with per-user JWTs and PostgreSQL RLS

Create per-request or per-session Supabase clients using the public anon key and the authenticated user's access token. Do not mutate one global client with different users' tokens, because concurrent Reflex sessions could cross identities. Enable RLS for all user data. Policies and narrowly scoped database functions must enforce:

- Users can read and update only their own profile and vehicles.
- Clients can access their own requests; assigned providers can access requests they serve; providers can discover pending requests using a safe projection that excludes unrelated private profile fields.
- Only a user with the provider role can accept a pending request; acceptance is atomic, is bound to one provider, and cannot overwrite an existing claim.
- Only the assigned provider can release or complete a request, with the existing allowed state transitions.
- Only the request owner and assigned provider can read or create its messages, and message sender identity always comes from `auth.uid()`.
- Event-log reads/writes follow an explicit least-privilege policy; no table is made public merely to simplify migration.

Use a narrowly granted PostgreSQL function/transaction for atomic acceptance and release where row-level policies alone cannot safely arbitrate concurrent updates. Any `SECURITY DEFINER` function must pin `search_path`, derive identity from `auth.uid()`, validate role and state, and grant execution only to authenticated users. The service-role key bypasses RLS and is therefore restricted to a separate migration/admin process, never a normal request path or browser configuration.

**Alternatives considered:** a runtime service-role client is simpler but bypasses RLS; relying only on Reflex UI checks is insufficient; independent read-then-write acceptance calls permit race conditions.

### Store profile photos in a dedicated Supabase Storage bucket

Create a private `profile-photos` bucket and use deterministic owner-scoped object paths, such as `profiles/{auth-user-uuid}/{safe-filename}`. Store Supabase object paths in the profile and generate access URLs through the authenticated Storage client. Limit upload, replacement, and deletion to the owning user, validate MIME type and file size, and do not place image bytes or credentials in application source or logs. Existing Xano photos are not migrated.

**Alternatives considered:** leaving photos in Xano would leave a runtime dependency after database cutover; embedding base64 images in PostgreSQL increases row size and is not appropriate object storage.

### Start Supabase without importing historical or demo data

1. Apply the versioned schema, RLS policies, RPC functions, and private Storage bucket to the configured Supabase project.
2. Route signup/login, profile, photo, vehicle, request, status, and messaging operations through Supabase Auth and the caller's user-scoped JWT.
3. Validate behavior with unit tests and isolated disposable accounts. Remove test-created users and records after remote integration checks; never reuse personal accounts or seed invented sample data into the project.
4. Switch runtime configuration to Supabase only after signup, request lifecycle, authorization denial, photo upload, and chat checks pass.
5. Retain Xano unchanged as a legacy source. Since Supabase starts empty and no dual-write is used, communicate that existing Xano accounts must sign up again and that rollback after new Supabase writes requires a separately planned reconciliation.

## Risks / Trade-offs

- **Existing users expect their Xano account or data to appear in Supabase** → State clearly that historical data and credentials are not migrated; require new Supabase registration and handle any later import in a separately approved change.
- **Incorrect RLS exposes PII or blocks legitimate workflows** → Add automated positive and negative policy tests for owners, assigned providers, other providers, and non-participants before production data is imported.
- **Concurrent providers claim one request** → Use a database transaction/function with a unique reservation constraint and concurrency tests.
- **Rollback after Supabase receives writes creates divergent records** → Do not switch back silently; define a reverse-sync and reconciliation plan before any rollback.
- **Supabase limits are reached by frequent polling** → Measure query volume during two-user integration tests and retain bounded polling; consider realtime only as a later, separately scoped change.

## Migration Plan

The startup sequence is defined under Decisions. Runtime cutover is blocked unless schema and RLS tests pass and signup, profile/photo, vehicle, request lifecycle, and client/provider chat flows work with disposable accounts. Keep Xano unchanged as the legacy source; no Xano records or account credentials are copied.

## Open Questions

Historical Xano data import is explicitly out of scope. Reconsidering it requires a separate approved change and migration plan with a full inventory, source backups, password recovery decisions, and reconciliation gates.
