# Changelog

All notable changes to this project are documented here.

## [1.1.1] - 2026-03-12

### Changed

- Changed homepage in metadata.txt

## [1.1.0] - 2026-03-11

### Changed

- Replaced the remote package manifest format from XML to JSON.
- Removed XML parsing from the plugin package feed workflow.
- Simplified package feed handling and removed Bandit XML parser warnings.

## [1.0.0] - 2026-03-11

### Added

- Support for installing, updating, and uninstalling SVG-based icon packages
- Dock panel for searching, filtering, and selecting icons
- Filtering by icon package and category
- Support for icon variants from package definitions
- Update checking for available icon packages
- Styling of existing point layers using SVG fields and a categorized renderer
- Placement of new point features using the selected SVG icon

### Fixed

- Fixed compatibility with QGIS 4 / Qt6
- Fixed `QNetworkRequest` compatibility in Qt6
- Fixed `QStandardPaths` compatibility in Qt6
- Fixed `QDockWidget`-related enum changes in Qt6
- Fixed `QListWidget`, `QTableWidget`, `QHeaderView`, and other widget enums in Qt6
- Fixed `QEventLoop.exec()` / `exec_()` compatibility
- Fixed `QMessageBox` buttons in Qt6
- Fixed `QPainter` render hints and color enums in Qt6
- Fixed `QSizePolicy` enums in Qt6
- Fixed network response handling in QGIS 4 when fetching the package list
- Fixed icon package reinstallation so old files are properly removed
- Improved plugin stability during unload / reload

### Changed

- The plugin is now SVG-based and uses icon packages instead of a local Font Awesome OTF-based workflow
- Metadata, description, and documented functionality were updated to reflect the current implementation
