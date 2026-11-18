## Context

See `proposal.md` for motivation and `specs/profile/responsive-layout/spec.md` for user-visible requirements. The profile page is composed in Reflex and its current visual rules live in `styles.py`, including mobile breakpoints. The change should refine those rules and preserve existing page behavior.

## Goals / Non-Goals

**Goals:**
- Keep the header and all profile cards within the viewport at mobile, tablet, and desktop sizes.
- Prevent narrow form fields, vehicle actions, and save controls from colliding or clipping.
- Preserve the current visual language and interactions.

**Non-Goals:**
- Change profile fields, business logic, state, validation, APIs, persistence, or authentication behavior.
- Redesign unrelated pages or introduce a new UI framework or dependency.

## Decisions

- Reuse the profile's existing class names and responsive rules in `styles.py`; adjust the Reflex component structure only if CSS cannot express the required wrapping.
- Treat 320–420px as the narrow-mobile range and 421–820px as the tablet range, keeping the desktop layout above 820px. These ranges make the existing mobile behavior measurable without requiring new dependencies.
- Reflow content before reducing text to unreadable sizes: stack form fields on narrow screens, allow header and section actions to wrap, and keep cards fluid with bounded padding.
- Validate the rendered profile at 320px, 375px, 768px, 1024px, and 1440px, checking horizontal overflow and the visibility of the header, vehicle, and save actions.
- Prefer CSS-only changes; no domain entities are created, read, updated, or removed, and no authorization rules are involved.

## Risks / Trade-offs

- [Breakpoints can expose awkward gaps or wrapping] → Inspect representative widths around each breakpoint and tune only profile-specific rules.
- [Shared CSS selectors could affect another screen] → Scope changes to existing profile-specific selectors and run the relevant regression tests.
