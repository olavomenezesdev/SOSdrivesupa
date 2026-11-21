## Purpose

Define the role-specific profile presentation so service providers can focus on their profile information and specialties without customer vehicle-management content.

## ADDED Requirements

### Requirement: Provider profile omits vehicle-management content
The system SHALL omit vehicle-related profile checklist and management content when displaying the profile to a service provider.

#### Scenario: Provider views profile completion checklist
- **WHEN** a service provider views the profile
- **THEN** the checklist does not display the "Cadastre seu veículo" item
- **AND** the other profile checklist items remain visible

#### Scenario: Provider views profile footer
- **WHEN** a service provider views the bottom of the profile
- **THEN** the "Meus veículos" heading, its subtitle, the "Adicionar veículo" button, and the registered vehicle list are not displayed
- **AND** the unsaved-changes notice and "Salvar alterações" button remain visible
- **AND** the save button retains its existing save action and loading/disabled behavior

#### Scenario: Driver views profile
- **WHEN** a driver views the profile
- **THEN** the existing vehicle checklist item and vehicle-management content remain visible
- **AND** the profile UI remains unchanged
