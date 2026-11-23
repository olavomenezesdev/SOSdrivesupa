## Purpose

Provide a clear, responsive visual hierarchy for the provider home so the availability control, map, and nearby requests are easy to scan and use across screen sizes.

## ADDED Requirements

### Requirement: Provider home uses a responsive card-based layout
The provider home SHALL present its content on a soft, spacious page background with a clear branded header and floating content cards. On wide screens, the map and nearby requests SHALL appear side by side; on narrow screens, they SHALL stack without horizontal overflow.

#### Scenario: Provider opens home on a wide screen
- **WHEN** a provider opens the home screen on a wide viewport
- **THEN** the page shows the SOS Drive branding, provider title and subtitle, availability control, and provider avatar in a horizontal header
- **AND** the map and nearby requests appear in separate rounded white cards with subtle shadows in a two-column layout

#### Scenario: Provider opens home on a narrow screen
- **WHEN** a provider opens the home screen on a narrow viewport
- **THEN** the header and content cards adapt to the available width
- **AND** the map and nearby requests stack vertically without horizontal overflow

### Requirement: Provider map remains usable within its visual card
The map SHALL be displayed in a rounded, clipped white card with a visible recenter action positioned within the map area. The existing map interactions, geolocation feedback, initialization, and recenter behavior SHALL remain available.

#### Scenario: Provider uses the map card
- **WHEN** a provider views the map
- **THEN** the map is visually contained within rounded card boundaries
- **AND** the recenter action remains visible and usable without obscuring essential map interactions

### Requirement: Nearby requests remain readable and actionable
The nearby requests card SHALL retain its dynamic summary and state-driven request contents, using high-contrast text and distinct individual request cards that show the existing service type, distance, vehicle, and description. Existing request actions SHALL remain available with their current state-dependent behavior.

#### Scenario: Provider views available nearby requests
- **WHEN** nearby requests are available
- **THEN** the card shows the dynamic regional summary and each request's service type, distance, vehicle, and description in a readable layout
- **AND** the existing action for each request type remains present and keeps its current action

#### Scenario: Provider has no available requests or an error
- **WHEN** requests are loading, unavailable, or fail to load
- **THEN** the existing loading, empty, retry, or unavailable feedback remains visible and readable within the requests card

### Requirement: Availability control preserves its existing behavior
The provider home SHALL continue to show the current availability state and allow the provider to toggle it using the existing action. The visual treatment SHALL distinguish available from unavailable without relying on color alone.

#### Scenario: Provider toggles availability
- **WHEN** the provider activates the availability control
- **THEN** the displayed state updates between "Disponível" and "Indisponível"
- **AND** nearby requests continue to follow the current availability-dependent visibility behavior
