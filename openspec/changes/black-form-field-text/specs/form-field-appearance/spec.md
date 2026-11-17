## Purpose

Define consistent, readable text rendering for the fields used by the login,
driver/customer registration, and service-provider registration forms.

## ADDED Requirements

### Requirement: Form field text is black on the three requested screens

The login, driver/customer registration, and service-provider registration
forms SHALL render the text content of their input, textarea, and select
fields as `#000000`, including user-entered, prefilled, and automatically
loaded values.

#### Scenario: User enters text in a requested form field

- **WHEN** a user types into any input or textarea on one of the three
  requested screens
- **THEN** the entered characters are rendered as `#000000`

#### Scenario: A requested form field contains a prefilled value

- **WHEN** a field on one of the three requested screens has a value before
  or during display
- **THEN** the displayed value is rendered as `#000000`

#### Scenario: A select field displays content

- **WHEN** a select field on one of the three requested screens displays its
  current option or other field text
- **THEN** that displayed text is rendered as `#000000`

### Requirement: Placeholders and autofill text are black

The requested forms SHALL render placeholder text and browser autofill text
as `#000000` with full placeholder opacity.

#### Scenario: Empty field displays a placeholder

- **WHEN** an input or textarea on one of the three requested screens is
  empty and has a placeholder
- **THEN** the placeholder is rendered as opaque `#000000` text

#### Scenario: Browser autofills a field

- **WHEN** the browser autofills an input on one of the three requested
  screens
- **THEN** the autofilled text is rendered as `#000000`

### Requirement: Field color styling is scoped to the requested forms

The text color rules SHALL apply only to fields within the login,
driver/customer registration, and service-provider registration forms and
SHALL NOT change fields on other screens.

#### Scenario: Another screen contains a field

- **WHEN** a field outside the three requested forms is rendered
- **THEN** its existing text color behavior remains unchanged

### Requirement: Other visual and functional behavior is preserved

The change SHALL leave field backgrounds, borders, dimensions, spacing,
typography, buttons, layout, events, validation, masking, authentication,
registration handlers, routes, and business rules unchanged.

#### Scenario: User interacts with a styled field

- **WHEN** a user focuses, edits, submits, or clears a field on one of the
  requested forms
- **THEN** the existing interaction and functional behavior is preserved
