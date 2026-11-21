## Context

The provider home already renders its header, availability control, map, dynamic request list, and request actions in one Reflex screen, with related selectors in the global style map. See proposal.md for the presentation goals and specs/provider-home-ui/spec.md for observable requirements. The controlling constraint is to keep state, event handlers, routes, map scripts, and request rendering logic unchanged.

## Goals / Non-Goals

**Goals:**
- Reuse the current header content, provider avatar, availability state, map wrapper, request summary, request cards, and status feedback.
- Use a small set of provider-home-specific classes to create the requested desktop cards and responsive stacked layout.
- Keep map controls inside the map card and preserve their current callbacks and accessible labels.
- Keep every existing request action and state condition intact while changing only its visual presentation.

**Non-Goals:**
- Modify state classes, polling, distance calculations, request data, map initialization/geolocation scripts, API/database behavior, or any other screen.
- Add dependencies, new state, or new routes.

## Decisions

1. **Keep the existing Reflex data and action tree; adjust only its presentation wrappers and props.** This avoids duplicating behavior or changing callbacks while allowing the map and request panels to become card containers. Rebuilding the screen from new components was considered but would add indirection without improving this single-page layout.
2. **Use provider-home-scoped styles in `styles.py` for gradient, spacing, card surfaces, shadows, radii, and responsive breakpoints.** This keeps visual tokens together and limits the changes to the provider screen. Inline-only styling was considered but would scatter responsive rules across the component.
3. **Make the header non-obstructive and let the page own the layout flow.** Replace fixed positioning with a normal header inside the padded page, so content does not need compensating offsets and narrow layouts can wrap cleanly.
4. **Make the map card a positioned, clipped container and anchor the recenter control within it.** This keeps the existing map DOM element and scripts unchanged while making its controls part of the card. Moving the control into another page region was rejected because it could overlap the request panel.
5. **Use a flexible desktop grid/flex ratio and stack cards at the existing mobile breakpoint.** The requests card may scroll internally when its content exceeds available height on desktop; on mobile, the document should scroll naturally to avoid trapping the user in a nested panel.
6. **Style availability from the existing boolean state with both text and visual state cues.** Keep the same click event and accessibility label, and provide distinct available/unavailable styles without relying on color alone.

## Risks / Trade-offs

- [The map or recenter control can be clipped or overlap content after repositioning] → Keep the map pane positioned and overflow-clipped, place the control relative to that pane, and verify interaction at desktop and mobile widths.
- [A fixed-height request card can create nested scrolling on small devices] → Use internal scrolling only where the two-column desktop layout needs it; allow the mobile page to scroll normally.
- [Visual changes could accidentally replace or remove an existing request action] → Keep the current state-driven branches and verify rendered handlers and labels for each request type.
