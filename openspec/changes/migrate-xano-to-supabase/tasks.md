# Tasks

## 1. Supabase foundation and backend authorization

- [x] 1.1 Add the Supabase Python dependency, backend-only configuration validation, and secret-free `.env.example`/setup docs; verify dependency installation and missing/invalid configuration tests.
- [x] 1.2 Create and apply versioned PostgreSQL migrations for the empty application schema, relationships, constraints, indexes, RLS, RPC operations, and private Storage bucket; verify the schema on the configured Supabase project.
- [x] 1.3 Implement Supabase Auth signup/login/session recovery and profile identity mapping; verify role loading, refresh, invalid credentials, unsupported roles, and fresh account behavior without exposing tokens.
- [x] 1.4 Complete backend/database RLS and narrowly scoped operations for profile/vehicle ownership, pending provider requests, request participation, status transitions, and message authorship; verify positive and denied cases with disposable client/provider/non-participant accounts.
- [x] 1.5 Verify atomic provider acceptance and release functions; test concurrent providers produce exactly one assignment and that release permits a later valid acceptance.
- [x] 1.6 Implement owner-scoped profile-photo upload/read/delete with MIME and size validation; verify Storage authorization and checksums using disposable images.

## 2. Replace Xano-backed application flows

- [x] 2.1 Replace Xano auth/profile helpers in `sosdrive.py` with the Supabase backend adapter and preserve Reflex routes/error UX; verify focused auth/profile tests, session restoration, role navigation, and fresh signup.
- [x] 2.2 Replace vehicle and service-request operations with Supabase repositories while preserving ownership, provider polling, and request statuses; verify owner isolation and client-to-provider lifecycle.
- [x] 2.3 Replace service-message reads/writes with participant-scoped Supabase operations while retaining two-second open-panel polling; verify client/provider exchange, no duplicate appends, and denial for non-participants.
- [x] 2.4 Update runtime environment examples and README to remove Xano runtime requirements, explain fresh Supabase registration and non-imported legacy Xano data, and document local setup; verify every documented step.

## 3. Empty-dataset startup and verification

- [x] 3.1 Verify empty-dataset startup and complete client/provider flows against Supabase with disposable accounts; clean up test-created accounts and records and verify authorization denials.
- [x] 3.2 Document and verify the one-time transition: no historical Xano accounts/data are copied, existing users register again, Xano remains unchanged, and rollback after Supabase writes requires separate reconciliation.
- [x] 3.3 Confirm no runtime Xano calls remain and record focused test/build results; keep Supabase production data free of test/demo rows after validation.

## Workflow follow-up

- Importing Xano records, accounts, event logs, or existing photos requires a separate approved change and migration plan.
- Archive this change only after all implementation tasks and verification gates pass.
- Keep the Xano workspace and its source data unchanged as a legacy reference.
