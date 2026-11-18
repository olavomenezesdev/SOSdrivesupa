# Proposal

## Why

The SOS Drive backend currently depends on Xano for authentication, application data, and profile-photo uploads. Xano rate limits have already interrupted authenticated session restoration and vehicle loading; replacing this dependency with Supabase should make the demo and normal user flows more reliable while preserving the current product behavior.

## What Changes

- Replace the Xano-backed authentication, profile, photo, vehicle, service-request, acceptance, status, and messaging calls with Supabase Auth, PostgreSQL, and Storage, keeping Python and Reflex as the application stack.
- Start with an empty Supabase application database. Do not import Xano accounts, records, event logs, or stored photos in this change; users create fresh Supabase accounts.
- Support new profile-photo uploads in Supabase Storage; existing Xano photos remain in Xano and are not copied.
- Do not seed demo accounts or sample records automatically; validate account flows with disposable test accounts and keep the live application database empty of invented data.
- Enforce ownership, participant, and provider-role authorization in PostgreSQL row-level security and narrowly scoped database operations, including atomic single-provider acceptance.
- Preserve the Xano workspace and its data unchanged as a legacy reference. The application switches to Supabase with no historical records; rollback to Xano would not include writes made in Supabase and therefore requires a separately planned reverse migration.
- Preserve current client/provider journeys and user-visible behavior; do not add payment, advanced history, or unrelated product features.

## Capabilities

### New Capabilities

None. This change replaces backend infrastructure without introducing new user-visible behavior.

### Modified Capabilities

None. The repository currently has no main OpenSpec capability specs, and the intended contract is behavioral parity with the existing application. This change opts out of delta specs using `skip_specs: true`.

## Impact

- **Application code:** Xano helpers and their callers in `sosdrive.py`; environment loading and example configuration; focused unit and integration tests.
- **Supabase:** project configuration, PostgreSQL schema and migrations, Auth user/profile relationship, row-level security policies, atomic request acceptance, and a profile-photo Storage bucket.
- **Data:** no Xano records, credentials, event logs, or existing photos are imported. Supabase tables begin empty; new users and data are created through the application.
- **Credentials:** the Supabase project URL and public anon key may be configured for the backend client; any service-role key is restricted to a controlled migration/admin process and must never reach the browser or be committed.
- **Scope:** within the existing MVP. Preserve the client/provider journeys, profile, vehicle, request, and conversation behavior on Supabase without migrating historical Xano records or creating demo records.
- **Account transition:** existing Xano accounts are not transferred; users must register in Supabase. Existing Xano records remain available only in the source workspace unless a later, separately scoped import is approved.
- **Rollback:** keep Xano data unchanged. Because this change does not dual-write or migrate Supabase writes back to Xano, switching back after users create new records requires a separate reconciliation plan.
