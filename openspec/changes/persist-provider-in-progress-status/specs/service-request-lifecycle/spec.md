## Purpose

Defines the authorized transition that records when the assigned provider begins a service request and lets the customer observe that persisted state.

## ADDED Requirements

### Requirement: Assigned provider can start an accepted service request
The system SHALL allow only the authenticated provider assigned to an `accepted` service request to transition it to `in_progress`. The provider interface SHALL show “Atendendo” only after the transition is confirmed by the backend. Repeating the transition for the same assigned request SHALL return its current `in_progress` state without creating a conflicting transition.

#### Scenario: Assigned provider starts service
- **WHEN** the provider assigned to an `accepted` request confirms “Iniciar atendimento”
- **THEN** the request is persisted as `in_progress` before the provider interface advances to “Atendendo”

#### Scenario: Provider retries an already persisted start
- **WHEN** the assigned provider repeats the start operation for a request already `in_progress`
- **THEN** the system returns the current request as `in_progress` and the provider interface remains in “Atendendo”

#### Scenario: Unassigned user attempts to start service
- **WHEN** a user who is not the assigned provider, or a user who is not a provider, attempts the transition
- **THEN** the system rejects the operation and leaves the request unchanged

#### Scenario: Start operation fails
- **WHEN** the backend cannot persist the transition
- **THEN** the provider interface remains at the prior phase and reports that the operation failed

### Requirement: Customer sees the persisted in-progress state
The customer dashboard SHALL display “Atendimento em andamento” after polling observes the request status `in_progress`, while preserving the existing conversation and request details.

#### Scenario: Provider starts service while customer is viewing the request
- **WHEN** the assigned provider's request changes to `in_progress`
- **THEN** the customer's existing polling updates the status card to “Atendimento em andamento” without clearing the request or conversation state
