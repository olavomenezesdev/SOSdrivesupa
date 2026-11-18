## Purpose

Rebuild the public landing page as a responsive Reflex screen that matches the supplied reference image while keeping the current app navigation and login flow functional.

## ADDED Requirements

### Requirement: Reference-based landing composition

The landing page SHALL match the supplied reference with a dark night-road scene, centered headline, transparent top navigation, and primary emergency CTA without relying on a static image overlay alone.

#### Scenario: The public landing renders with the reference composition
- **WHEN** the home route loads
- **THEN** the page presents the SOS Drive wordmark, nav, headline, supporting text, and primary CTA in the same visual hierarchy as the supplied image

#### Scenario: The design remains functional and responsive
- **WHEN** the viewport changes between desktop and mobile sizes
- **THEN** the hero content stays readable, the nav remains usable, and no horizontal overflow or content clipping occurs

### Requirement: Night-road visual treatment

The landing hero SHALL reuse the supplied reference asset as the visual base and overlay it with subtle darkening and contrast to preserve readability while respecting the original composition.

#### Scenario: The reference image is used as the background base
- **WHEN** the landing hero renders
- **THEN** the hero background uses the local reference asset with a dark overlay so text remains legible over the road and vehicle scene

#### Scenario: Decorative elements remain non-interactive
- **WHEN** the user views the landing page
- **THEN** decorative visuals behind the text do not block clicks on the CTA or nav links

### Requirement: CTA and navigation continuity

The landing page SHALL preserve working navigation to the landing, login, and app entry points already used by the product without introducing a new flow or breaking authentication routes.

#### Scenario: CTA and nav links work for existing user flows
- **WHEN** the user clicks Home, Services, Pricing, Login, or the emergency action
- **THEN** the app continues to route to the existing pages already registered in the app

### Requirement: Accessibility and reduced motion

The landing page SHALL retain strong text contrast and avoid motion that can impair readability or accessibility.

#### Scenario: Reduced motion preference is honored
- **WHEN** the browser requests reduced motion
- **THEN** decorative motion is suppressed or reduced while content remains fully legible

#### Scenario: Content contrast stays readable
- **WHEN** the hero text overlays the night-road image
- **THEN** contrast stays sufficient for text readability without relying on a broken image or unreadable palette
