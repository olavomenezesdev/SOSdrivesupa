## Context

See `proposal.md` for motivation and `specs/profile/input-contrast/spec.md` for visible requirements. The four fields use Reflex inputs inside Radix wrappers. Browser inspection shows the native input's current text color is inherited as dark navy, while CPF and Phone placeholders are very pale and disabled Email text is translucent.

## Goals / Non-Goals

**Goals:**
- Make the actual native input text black and placeholders a readable, distinct gray.
- Keep Email disabled and preserve all current handlers and values.

**Non-Goals:**
- Change saved field values, validation, masking, state, persistence, APIs, or any other screen.
- Change the field backgrounds, borders, spacing, or layout.

## Decisions

- Add the requested `color` and `_placeholder` presentation props to all four existing Reflex input components.
- Add `Digite seu nome completo` and `E-mail cadastrado` as placeholders only; preserve existing field values, bindings, and the disabled Email state.
- Reuse the `profile-input-control` wrapper class and add narrowly scoped CSS targeting its nested native input and `::placeholder`; the class is on the Radix wrapper, not on the native `input`, so props alone may not reliably override the observed native placeholder and disabled text colors.
- Keep the CSS scoped under the basic-information card so other forms remain unchanged.
- Verify computed native input and placeholder colors in the browser, then run the profile rendering test and Reflex compilation.
- No domain entities or authorization rules are affected.

## Risks / Trade-offs

- [Radix generated styles can override wrapper-level styling] → Target the nested native input and placeholder with a profile-card-scoped selector and verify computed colors in the browser.
