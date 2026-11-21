## Why

The shared profile screen currently presents vehicle-management content to service providers, even though their profile focuses on contact information and specialties. A role-specific layout will reduce clutter for providers while keeping the customer profile unchanged and the existing save flow intact.

## What Changes

- Hide the "Cadastre seu veículo" completion-checklist item for service providers.
- Hide the vehicle section, including its heading, subtitle, add-vehicle button, and registered vehicle list, from service providers.
- Keep the unsaved-changes notice and "Salvar alterações" button at the bottom of the provider profile, preserving its existing click handler and loading/disabled behavior.
- Preserve the customer profile UI and existing profile-completion calculation.
- Make no backend, state, database, or API changes.

## Capabilities

### New Capabilities
- `provider-profile-ui`: Role-specific presentation of vehicle-related content on the profile screen.

### Modified Capabilities
- None.

## Impact

- Affects the shared Reflex profile UI in `sosdrive.py`, using the existing user-role value to conditionally render provider-only presentation.
- Reuses current profile components, state values, and save behavior; introduces no new dependencies or APIs.
- This is within the SOS Drive MVP and does not change domain entities (Motorista, Prestador, Tipo de Socorro, Chamado, Avaliação, or Localização).
- No data rollback is needed because no persisted data or business logic changes.
