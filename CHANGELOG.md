# Changelog

Alle vesentlige endringer i dette prosjektet dokumenteres her.

## [1.1.1] - 2026-03-12

### Changed

- Changed homepage in metadata.txt

## [1.0.0] - 2026-03-11

### Added

- Støtte for installasjon, oppdatering og avinstallering av SVG-baserte ikonpakker
- Dock-panel for søk, filtrering og valg av ikoner
- Filtrering etter ikonpakke og kategori
- Støtte for ikonvarianter fra pakkedefinisjoner
- Oppdateringssjekk for tilgjengelige ikonpakker
- Styling av eksisterende punktlag med SVG-felter og kategorisert renderer
- Plassering av nye punktobjekter med valgt SVG-ikon

### Fixed

- Fikset kompatibilitet med QGIS 4 / Qt6
- Fikset `QNetworkRequest`-kompatibilitet i Qt6
- Fikset `QStandardPaths`-kompatibilitet i Qt6
- Fikset `QDockWidget`-relaterte enum-endringer i Qt6
- Fikset `QListWidget`, `QTableWidget`, `QHeaderView` og andre widget-enums i Qt6
- Fikset `QEventLoop.exec()` / `exec_()`-kompatibilitet
- Fikset `QMessageBox`-knapper i Qt6
- Fikset `QPainter`-render hints og farge-enums i Qt6
- Fikset `QSizePolicy`-enums i Qt6
- Fikset håndtering av nettverksrespons i QGIS 4 ved henting av pakkeliste
- Fikset reinstallasjon av ikonpakker slik at gamle filer ikke blir liggende igjen
- Forbedret stabilitet ved unload / reload av plugin

### Changed

- Pluginen er nå SVG-basert og bruker ikonpakker i stedet for lokal Font Awesome OTF-basert arbeidsflyt
- Metadata, beskrivelse og funksjonsomfang er oppdatert til å reflektere dagens funksjonalitet
