## Purpose

Define a clear, responsive customer dashboard presentation that helps a driver view nearby provider availability, choose roadside assistance, and follow an existing request while preserving the current request flow.

## ADDED Requirements

### Requirement: Customer dashboard presents a responsive two-card layout
The customer dashboard SHALL use the full available page width, a maximum content width of approximately 1680px or 96vw, a soft blue-gray gradient, responsive horizontal padding, and at least the viewport height. On desktop viewports, the page SHALL use a vertical layout whose map/request content grows to fill the available viewport height. The map and request/status cards SHALL use a two-column layout with a 65/35 balance, a map-favoring ratio, and a gap of approximately 24px. The customer header SHALL wrap without clipping or squeezing its brand, availability badge, or avatar. At viewport widths below 1024px, the cards SHALL stack vertically, with a comfortable 380px–450px map height and the request/status card below it. The page SHALL not have horizontal overflow.

#### Scenario: Customer opens the dashboard on a wide viewport
- **WHEN** a customer opens the dashboard on a wide viewport
- **THEN** the header presents the SOS Drive brand, customer area title and subtitle, the current available-provider count, and the customer avatar
- **AND** the map and request/status content appear in separate rounded white cards with subtle shadows
- **AND** the cards fill the usable page height without a large unused area below them

#### Scenario: Customer opens the dashboard on a tablet or mobile viewport
- **WHEN** a customer opens the dashboard at a viewport width below 1024px
- **THEN** the header and cards adapt to the available width
- **AND** the map and request/status cards stack, with the map remaining comfortably usable and no horizontal overflow

### Requirement: Map card retains its existing map and location controls
The customer map SHALL remain inside a rounded, clipped card and fill the available width and height of its parent at desktop, tablet, and mobile sizes. A visible “Centralizar no meu local” action SHALL remain positioned within the map card without being clipped. The existing map initialization, geolocation updates, and recenter interaction SHALL remain available and retain their current behavior.

#### Scenario: Customer views and recenters the map
- **WHEN** the customer dashboard is displayed
- **THEN** the existing Leaflet map remains visible within the map card
- **AND** the recenter action remains visible and invokes the existing map recenter behavior

### Requirement: Service and request controls retain their existing behavior
The request/status card SHALL fill the available height alongside the map on desktop and show the existing service choices as prominent, rounded cards in a two-by-two grid. Service cards SHALL provide comfortable clickable areas, with icon containers approximately 48px square, labels around 15px, and a minimum card height around 120px. When no request is active, the service grid SHALL expand to use available panel space. Searching, matched, error, messaging, and cancellation content SHALL remain readable and fit within the panel without clipping when present. The existing service-selection actions, status conditions, messaging action, and cancellation action SHALL remain unchanged. When a request is matched, its success status and existing estimated price and distance SHALL be clearly legible.

#### Scenario: Customer chooses a service
- **WHEN** a customer selects any displayed service card
- **THEN** the existing action for that service is invoked unchanged

#### Scenario: Request status changes
- **WHEN** a request is searching, matched, or has an error
- **THEN** the corresponding existing state feedback remains visible and readable in the request/status card
- **AND** the matched state shows the existing price and distance values without changing how those values are produced

#### Scenario: Customer opens request messages or cancels
- **WHEN** the existing state conditions make request messaging or cancellation available
- **THEN** the respective full-width action is displayed in the request/status card
- **AND** activating it invokes its existing event handler unchanged

### Requirement: Availability badge separates its indicator from its dynamic count
The header SHALL display the existing available-provider count in a rounded pill with exactly one green status indicator positioned before the text. The indicator SHALL remain fixed-size and non-absolute, and the count text SHALL remain on one line when the available width permits. The count SHALL remain bound to its current dynamic value and SHALL NOT be hardcoded or recalculated by the visual redesign.

#### Scenario: Customer views current provider availability
- **WHEN** the customer dashboard header is displayed
- **THEN** one green indicator appears to the left of the current available-provider count
- **AND** the indicator does not overlap or touch the count text
- **AND** the badge adapts to narrow headers without leaving the viewport
