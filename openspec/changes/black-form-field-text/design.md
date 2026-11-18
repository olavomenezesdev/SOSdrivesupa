## Context

The requested behavior is limited to frontend presentation. Existing Reflex
forms and their shared style definitions should be reused, while the
selectors must be scoped so unrelated screens retain their current colors.
No domain entity, authorization rule, API, or persistence behavior is
affected.

## Goals / Non-Goals

**Goals:**

- Identify the three existing form containers and apply a shared, scoped text
  color rule to their field controls.
- Cover entered values, placeholders, select content, prefills, and browser
  autofill.
- Preserve every visual property other than field text color and preserve all
  existing event wiring.

**Non-Goals:**

- No backend, database, model, endpoint, route, authentication, validation,
  mask, handler, or business-rule changes.
- No global field selector that could affect other screens.
- No redesign, refactor, dependency, or typography change.

## Decisions

1. Reuse the existing stylesheet/style definitions as the primary location
   for the rules. Add narrowly scoped form-container classes only if the
   existing markup does not provide stable selectors.
2. Set `color: #000000 !important` on `input`, `textarea`, and `select` inside
   each requested form. Set opaque black placeholder color on `input` and
   `textarea`, and black `-webkit-text-fill-color` for autofill. The
   specificity and `!important` usage are limited to these form containers so
   existing component defaults cannot override the requested color.
3. If a form cannot be uniquely identified through existing classes, add only
   a CSS class to its existing visual container in `sosdrive.py`; do not
   replace components or alter their properties, events, or handlers.
4. Validate by inspecting the rendered login and both registration forms,
   checking placeholders, typed values, prefilled/autofilled values, and
   confirming an unrelated screen remains unchanged.

## Risks / Trade-offs

- [Risk] A shared form component may be reused by an unrelated screen →
  [Mitigation] Scope selectors to explicit screen/form classes and verify an
  unrelated field.
- [Risk] Browser autofill styling can override ordinary text color →
  [Mitigation] Include the autofill text-fill rule with the same scoped
  selector and `!important`.
