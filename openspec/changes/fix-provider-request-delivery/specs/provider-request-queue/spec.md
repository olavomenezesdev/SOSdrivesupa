## Purpose

Define how the authenticated Prestador receives available Chamados in the provider area, including initial loading, periodic updates, and clear recovery when the queue cannot be loaded.

## ADDED Requirements

### Requirement: Prestador receives available pending Chamados
The system MUST show each Chamado returned as pending and unassigned by the authorized backend in the available-requests list for an authenticated Prestador whose availability is enabled.

#### Scenario: Prestador opens the area with pending Chamados
- **GIVEN** an authenticated Prestador with availability enabled and pending Chamados without an assigned Prestador
- **WHEN** the Prestador opens the provider area
- **THEN** the area loads and displays those Chamados so they can be opened and accepted

#### Scenario: Prestador has active Chamados and pending Chamados
- **GIVEN** an authenticated Prestador with an active Chamado and one or more pending Chamados
- **WHEN** the provider area loads or refreshes its queue
- **THEN** active Chamados remain visible with their active status and pending Chamados remain available to accept

### Requirement: Provider queue stays current
The system MUST refresh the provider queue while the provider area remains open, without requiring a manual page reload or interrupting an active Chamado.

#### Scenario: New pending Chamado arrives while the area is open
- **GIVEN** the provider area is open and a new unassigned pending Chamado becomes available
- **WHEN** the next queue refresh completes
- **THEN** the new Chamado appears in the available-requests list

#### Scenario: A pending Chamado is accepted
- **GIVEN** a pending Chamado is visible in the provider area
- **WHEN** that Chamado is accepted and the queue refreshes
- **THEN** it is no longer offered as pending and its active Chamado representation remains visible

### Requirement: Queue errors are distinct from an empty queue
The system MUST distinguish a successful empty result from a failed initial load or refresh, and MUST provide a clear retry action after a failure.

#### Scenario: Queue loads successfully with no pending Chamados
- **GIVEN** the authorized backend successfully returns no pending Chamados
- **WHEN** the provider queue finishes loading
- **THEN** the area displays its empty state

#### Scenario: Initial load or refresh fails
- **GIVEN** the provider queue cannot be loaded because of an event, authentication, or backend error
- **WHEN** the load attempt finishes
- **THEN** the area presents an error state and retry action instead of presenting the failure as an empty queue

### Requirement: Incomplete location data does not hide an otherwise available Chamado
The system MUST keep a pending Chamado visible when the authorized backend returns it but its optional coordinates are missing or invalid; unavailable distance or map details MUST NOT make the entire queue appear empty.

#### Scenario: Pending Chamado has no usable coordinates
- **GIVEN** the authorized backend returns a pending Chamado without usable coordinates
- **WHEN** the provider queue is mapped for display
- **THEN** the Chamado remains available to open and accept, and unavailable location details are represented without failing the queue

### Requirement: Pending Chamado data remains protected
The system MUST return pending Chamado details only through backend authorization for the authenticated Prestador and MUST NOT expose authentication tokens or private location details in diagnostic logs.

#### Scenario: Non-provider requests the pending queue
- **GIVEN** an authenticated user whose profile is not a Prestador
- **WHEN** the user attempts to load pending Chamados
- **THEN** the backend denies access and returns no pending Chamado details
