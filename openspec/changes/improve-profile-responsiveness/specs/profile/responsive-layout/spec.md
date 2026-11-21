## Purpose

Define como a página de perfil se reorganiza em celulares, tablets e desktops para manter seus dados e ações legíveis, acessíveis e sem rolagem horizontal.

## ADDED Requirements

### Requirement: Profile content adapts to the available viewport
The profile page MUST arrange its header, summary, information form, vehicles, and save area to fit the available viewport without horizontal overflow or clipped content.

#### Scenario: Profile on a narrow mobile viewport
- **WHEN** the profile page is viewed at a width from 320px through 420px
- **THEN** its cards and form fields fit the viewport, the form fields are arranged vertically, and the page has no horizontal scrolling

#### Scenario: Profile on a tablet viewport
- **WHEN** the profile page is viewed at a width from 421px through 820px
- **THEN** its cards use the available width with balanced spacing, and their content remains visible without horizontal scrolling

#### Scenario: Profile on a desktop viewport
- **WHEN** the profile page is viewed at a width greater than 820px
- **THEN** the content remains centered and comfortably readable while the cards and controls stay within the page layout

### Requirement: Profile actions remain available at every viewport
The profile page MUST keep its navigation, photo, vehicle, and save actions visible, distinguishable, and usable as the layout changes.

#### Scenario: Header actions at a narrow width
- **WHEN** the profile header is displayed on a narrow viewport
- **THEN** the “Voltar” and “Sair” actions remain visible, do not overlap, and can wrap when needed

#### Scenario: Vehicle and save actions on mobile
- **WHEN** the vehicles section is displayed at a mobile width
- **THEN** the add-vehicle and save actions remain fully visible and fit within their card
