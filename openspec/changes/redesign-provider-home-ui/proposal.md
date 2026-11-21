## Why

The provider home currently places the map and requests in a dense, edge-to-edge layout with limited visual separation, making availability, map actions, and nearby calls harder to scan. A responsive card-based presentation will improve hierarchy and readability while preserving the existing provider workflow and map behavior.

## What Changes

- Restyle the provider home background with a subtle ice-to-pastel-blue gradient and page-level spacing.
- Reorganize the header into a branded horizontal bar with the provider title, explanatory subtitle, current availability control, and avatar.
- Present the map and nearby requests in two floating white cards on wide screens and a vertically stacked layout on narrow screens.
- Keep map controls positioned within the map card, with rounded clipping and a clearly visible recenter action.
- Restyle the requests panel and individual request cards for readable text, category and distance hierarchy, and visible actions.
- Preserve existing state-driven availability, request rendering, all event handlers, routes, modals, request polling, and Leaflet initialization and behavior.
- Limit implementation changes to the provider-home presentation in `sosdrive.py` and its styles in `styles.py`, plus focused UI verification.

## Capabilities

### New Capabilities
- `provider-home-ui`: Responsive visual hierarchy and card-based presentation for the provider home screen.

### Modified Capabilities
- None.

## Impact

- Affects the Reflex provider home UI in `sosdrive.py` and related selectors in `styles.py`; tests may be updated to verify visual structure and preserved interactions.
- Reuses current UI components, state values, event handlers, and Leaflet map. No new dependencies, APIs, backend behavior, database integrations, or state variables are introduced.
- Within the SOS Drive MVP. The Prestador, Chamado, and Localização are presented using existing data only; no domain entity is changed.
- No migration or data rollback is required.
