## Purpose

Allows a customer to follow the persisted lifecycle of their own service request after submission without claiming provider location or progress data that the current schema and authorization do not expose.

## ADDED Requirements

### Requirement: Customer polling follows an active request through terminal status
The customer dashboard SHALL continue refreshing the authenticated customer's request while its status is `pending`, `accepted`, or `in_progress`. The client SHALL stop active polling when the request becomes `completed` or `cancelled`, or when the customer explicitly clears the request. A provider release that returns the request to `pending` SHALL keep the request visible and polling.

#### Scenario: Provider accepts a pending request
- **WHEN** a request changes from `pending` to `accepted`
- **THEN** the customer dashboard continues polling that request and updates its displayed status

#### Scenario: Request remains active or is released
- **WHEN** a request has status `in_progress` or an accepted request is released back to `pending`
- **THEN** the customer dashboard continues polling and presents the latest persisted status

#### Scenario: Request reaches a terminal status
- **WHEN** the request status becomes `completed` or `cancelled`
- **THEN** the dashboard stops polling that request and presents the corresponding terminal notice

#### Scenario: Request lookup is unavailable
- **WHEN** a fetch fails or the authenticated user cannot read the request
- **THEN** the dashboard preserves the last known request and chat state, reports the polling error through the existing notification pattern, and does not fabricate a new status

### Requirement: Customer status presentation reflects only persisted lifecycle values
The customer request card SHALL map `pending` to a searching state, `accepted` to a provider-on-the-way state, `in_progress` to an in-service state, `completed` to a completion summary with a clear action, and `cancelled` to a cancellation notice that permits a new request. The card SHALL retain the existing estimated price and distance when available. It SHALL NOT present `NO_LOCAL` or another provider-only phase as confirmed unless that phase is represented by a persisted status.

#### Scenario: Request is pending
- **WHEN** the latest request status is `pending`
- **THEN** the card shows that the system is searching for a provider and offers cancellation only when the existing backend permits it

#### Scenario: Request is accepted or in progress
- **WHEN** the latest request status is `accepted` or `in_progress`
- **THEN** the card shows the corresponding active status, keeps request messaging available, and hides cancellation when the backend no longer permits it

#### Scenario: Request is completed
- **WHEN** the latest request status is `completed`
- **THEN** the card shows a completed summary and a control that clears the request presentation for a new request

#### Scenario: Request is cancelled
- **WHEN** the latest request status is `cancelled`
- **THEN** the card informs the customer and releases the active request state so another request can be started

#### Scenario: Status is unknown
- **WHEN** Supabase returns a status not recognized by the current client
- **THEN** the card retains a neutral status and does not mislabel the request as completed, cancelled, or at a specific provider phase

### Requirement: Customer map does not imply unavailable provider tracking
The customer dashboard SHALL preserve its existing Leaflet map, customer marker, geolocation updates, and recenter control. It SHALL display a provider marker or route only when valid provider coordinates are available through an authorized shared source. Without such coordinates, it SHALL keep the existing customer map and SHALL NOT use mock coordinates or the provider's session-local state as a real provider position.

#### Scenario: No shared provider coordinates exist
- **WHEN** the request is active but no authorized provider coordinates are available to the customer
- **THEN** the map continues to show the customer location and controls without a provider marker or route

#### Scenario: Map initialization or location updates fail
- **WHEN** map setup or location retrieval fails
- **THEN** the request status card and request messaging remain usable and the dashboard does not fail as a whole

### Requirement: Request messaging remains independent from status polling
Status refreshes SHALL update request details without clearing an open conversation, its draft, or already loaded messages. The existing message action SHALL remain available while the request is active.

#### Scenario: Status changes while customer is messaging
- **WHEN** a status refresh occurs while the customer has an open message panel or unsent draft
- **THEN** the request status updates without closing the panel or discarding the draft and messages
