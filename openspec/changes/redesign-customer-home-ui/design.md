## Context

See proposal.md for the motivation and specs/customer-home-ui/spec.md for observable requirements. The `/customer` dashboard already uses a branded header, map and request cards, service grid, and state-driven request feedback. This refinement addresses remaining unused viewport space and the availability badge layout. Preserve all component callbacks, state conditions, map mount script, provider-count binding, and DOM map identifier.

## Goals / Non-Goals

**Goals:**
- Reuse the current customer avatar, online-provider count, map, vehicle selector, service cards, request status/error feedback, and message/cancel actions.
- Expand the existing page and content region to use the available viewport height and width while retaining responsive stacking.
- Correct the availability badge spacing and increase service-card prominence without changing state or behavior.
- Scope presentation rules to the customer dashboard so the provider screen and shared flows remain unaffected.

**Non-Goals:**
- Change State classes or variables, polling, service submission/cancellation, message flow, navigation, map/geolocation scripts, API calls, or database behavior.
- Add dependencies or change shared dashboard routes.

## Decisions

1. **Let the dashboard own viewport sizing, then let its content grid grow.** Use a wide maximum (approximately 1680px/96vw), desktop viewport height, and responsive page padding. Give the map/request region the remaining height and a map-favoring two-column ratio. At widths below 1024px, return to automatic page height and stack the cards with a fixed, comfortable map height. Fixed-width sidebars were rejected because they waste space on large displays and can squeeze tablet layouts.
2. **Keep the provider badge as a single normal-flow horizontal row.** Use one fixed-size green dot followed by the existing dynamic count text, with no absolute positioning or duplicate indicator. This fixes overlap while preserving the current count source; a hardcoded value or new availability query is out of scope.
3. **Make the service grid flex into unused panel space while respecting a minimum card size.** Use 48px icon containers, larger labels, and cards at least 120px high. Let the grid take spare space when no request feedback is visible and yield naturally when status/actions appear; use responsive wrapping and panel overflow only if the viewport cannot accommodate the active controls. A fixed-height grid was rejected because it either leaves blank space when idle or crowds active-call controls.
4. **Retain the Leaflet map element ID, initialization callback, and map event scripts.** Keep the map at 100% width and height of its sized parent, and keep the recenter control anchored inside the clipped card. Replacing map initialization or its callbacks was rejected because the request is strictly presentational.
5. **Use customer-dashboard-specific CSS selectors and responsive props.** This isolates sizing and breakpoint changes from provider and shared styles. Use the existing 1024px breakpoint for stacking and smaller breakpoint rules for header wrapping and badge fit instead of introducing a dependency or shared style changes.

## Risks / Trade-offs

- [Expanded content sizing could cover map controls or leave blank space at some viewport heights] → Size the cards against the viewport, keep the recenter control inside the map card, and verify desktop/tablet/mobile layouts.
- [Active status content could exceed the side panel height] → Let the service grid yield to the active status/actions and permit panel scrolling only when required; verify searching and matched states at shorter desktop heights.
- [A visual wrapper change could lose a conditional action] → Preserve every existing conditional branch and event binding, then verify the searching, matched, error, vehicle-selection, and messaging states.

## Migration Plan

No data or schema migration is required. Roll back by restoring the prior `/customer` component wrappers and customer-scoped styles; no backend or database rollback is needed.
