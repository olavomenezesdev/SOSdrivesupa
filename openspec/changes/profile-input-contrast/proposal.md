## Why

The Name, CPF, Phone, and Email fields in the profile's basic-information card are difficult to read against their light backgrounds. Improving value and placeholder contrast makes profile editing clearer without changing how those fields work.

## What Changes

- Render entered and prefilled text in the four basic-information fields in black.
- Give any placeholders in those fields a readable, distinct gray appearance.
- Show `Digite seu nome completo` and `E-mail cadastrado` when the Name and Email values are empty.
- Preserve the current field values, handlers, disabled state, layout, and all other profile behavior.

## Capabilities

### New Capabilities

- `profile/input-contrast`: defines readable value and placeholder colors for the profile information fields.

### Modified Capabilities

None.

## Impact

- **MVP:** within scope; improves readability of existing profile editing.
- **Code:** presentation properties for the four `rx.input` components in `sosdrive.py`; reuse the existing field classes.
- **Systems and data:** no backend, state logic, database, API, or domain-entity changes.
- **Technology:** uses the existing Reflex UI.
- **Verification:** inspect computed input and placeholder colors in the profile card and run the relevant profile test and Reflex compilation.
