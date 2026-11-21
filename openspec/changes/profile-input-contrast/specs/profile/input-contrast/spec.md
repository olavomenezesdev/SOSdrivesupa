## Purpose

Ensure profile information remains readable by rendering entered values in black and placeholder hints in a contrasting gray without changing how profile fields behave.

## ADDED Requirements

### Requirement: Basic profile values use black text
The Name, CPF, Phone, and Email fields in the basic-information card MUST render their current, prefilled, and user-entered values in `#000000`, including the disabled Email field.

#### Scenario: Profile field displays a value
- **WHEN** any of the four basic-information fields displays a value
- **THEN** the displayed text is rendered in `#000000`

### Requirement: Basic profile placeholders remain legible
Any placeholder displayed in the Name, CPF, Phone, or Email fields MUST use a readable gray color distinct from the black field value.

#### Scenario: An empty profile field displays a placeholder
- **WHEN** one of the basic-information fields is empty and has a placeholder
- **THEN** the placeholder is rendered in readable gray text distinct from `#000000`

### Requirement: Empty Name and Email fields provide guidance
When the Name or Email value is empty, the basic-information card MUST show a helpful placeholder in that field without changing its value or editability.

#### Scenario: Name has no value
- **WHEN** the Name field is empty
- **THEN** it displays the placeholder `Digite seu nome completo`

#### Scenario: Email has no value
- **WHEN** the Email field is empty
- **THEN** it displays the placeholder `E-mail cadastrado` and remains disabled

### Requirement: Profile field behavior is preserved
Changing the visual text colors MUST NOT change profile field values, handlers, disabled state, layout, or behavior outside the basic-information card.

#### Scenario: User edits an editable profile field
- **WHEN** the user types into Name, CPF, or Phone
- **THEN** the existing value binding and change handler continue to work unchanged

#### Scenario: Email remains read-only
- **WHEN** the basic-information card is displayed
- **THEN** Email remains disabled and its existing value is displayed in `#000000`
