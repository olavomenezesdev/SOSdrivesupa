## 1. Active Request Polling

- [x] 1.1 Reuse the participant-authorized request lookup to keep polling while status is `pending`, `accepted`, or `in_progress`, refresh only request fields that changed, and stop on `completed`, `cancelled`, or explicit clear; verify with focused State tests for each transition and fetch errors.
- [x] 1.2 Preserve the request ID, loaded messages, open chat panel, and unsent draft during status refresh; verify a polling test leaves those chat values unchanged.

## 2. Customer Status and Map Presentation

- [x] 2.1 Map existing persisted statuses to searching, accepted/on-the-way, in-progress, completed summary, cancelled notice, and neutral unknown status; verify each rendered status and its available actions in focused UI tests.
- [x] 2.2 Keep messaging available during active requests and show cancellation only for pending requests that the existing cancellation RPC accepts; verify accepted/in-progress states cannot invoke the invalid cancellation action.
- [x] 2.3 Preserve the current customer Leaflet marker, geolocation updates, recenter action, and responsive cards without rendering a provider marker or route from session-local/mock coordinates; verify map callbacks and absence of fabricated provider coordinates.

## 3. Verification

- [x] 3.1 Run focused customer request and chat tests plus `python -m reflex compile`; verify the change does not modify migrations, schema, RLS policies, or provider workflow.
- [x] 3.2 Manually inspect pending, active, terminal, and unknown status presentations and confirm the map remains usable on desktop and mobile without horizontal overflow.
