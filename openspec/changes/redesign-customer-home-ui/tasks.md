## 1. Customer Dashboard Presentation

- [x] 1.1 Reuse the existing `/customer` components to build the branded header and responsive map/request cards while preserving the map ID, mount callback, state conditions, and all event handlers; verify the rendered component retains the existing callback references.
- [x] 1.2 Add customer-dashboard-scoped styles for the gradient, card surfaces, service grid, status treatments, and responsive stacking; verify at wide and narrow viewport widths that the cards remain legible and have no horizontal overflow.

## 2. Behavior Preservation and Verification

- [x] 2.1 Verify the existing service choices, searching/matched/error feedback, provider count, vehicle selection, request messaging, and cancellation remain present under their original state conditions; add or update focused UI tests for the rendered states.
- [x] 2.2 Run the focused customer UI tests and `python -m reflex compile`, then manually verify map initialization, recentering, request-state presentation, and responsive layout in the browser.

## 3. Viewport and Card Refinements

- [x] 3.1 Expand the customer page and content region to use the available desktop viewport, with a map-favoring two-column layout and a stacked layout below 1024px; verify card dimensions and no horizontal overflow at desktop, tablet, and mobile widths.
- [x] 3.2 Rebuild the provider-availability badge as one non-absolute green indicator followed by the unchanged dynamic count; verify the rendered badge has exactly one indicator, readable spacing, and no clipping at narrow widths.
- [x] 3.3 Enlarge service cards, icons, and labels, and make the service grid use available idle panel space while yielding to active request status/actions; verify idle, searching, and matched states do not clip or overflow the card.

## 4. Refinement Verification

- [x] 4.1 Add or update focused layout/style tests, run the customer and chat regression tests plus `python -m reflex compile`, and manually inspect the map, header badge, and active/idle panel layouts in the browser.
