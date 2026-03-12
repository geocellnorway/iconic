# Iconic

Iconic is a QGIS plugin for working with SVG-based icon packages in point layers.

The plugin adds its own dock panel in QGIS where you can:

- install, update, and uninstall icon packages
- search and filter icons by package and category
- preview available SVG icons
- place new point features in the map using the selected icon
- style existing point layers with SVG icons
- use icon information stored in layer fields

## Features

### Icon packages

Iconic fetches a package list from an external `packages.json` file and lets you install icon packages directly from the plugin. Each package can contain:

- SVG files
- a related JSON file with names, descriptions, categories, and variants

The plugin also supports update checks for available package versions.

### Icon selection

In the dock panel, you can:

- search by icon name or description
- filter by icon package
- filter by category
- choose a variant where available
- define symbol size in mm

### Placing new points

When you choose **Place new points by clicking in the map**, you can click directly in the map canvas and create new point features using the selected SVG icon.

### Styling existing point layers

When you choose **Style existing layer**, the plugin can:

- create required fields if they are missing
- store SVG information in the layer
- use a categorized renderer based on `svg_path`
- overwrite existing icon values if desired

## Fields used

The plugin uses the following fields in the point layer:

- `icon_source`
- `svg_name`
- `svg_path`
- `svg_size`
- `svg_variant`
- `svg_category`
- `svg_pack`

These fields are used to store information about the selected icon, the location of the SVG file, the symbol size, and any selected variant.

## Requirements

- QGIS 3.34 or newer
- Also supports QGIS 4 / Qt6

## Installation

1. Install the plugin in QGIS
2. Open **Iconic** from the menu or toolbar
3. Open **Icon Packages**
4. Install the desired package
5. Select an icon and use the plugin to place or style features

## Icon packages

The plugin expects a package list in JSON format with links to:

- a ZIP archive containing SVG files
- a JSON file containing icon metadata

Packages are installed locally in the QGIS AppData folder.

## Status

The plugin is under active development. The main focus so far has been stable support for both QGIS 3 and QGIS 4, including Qt6 compatibility.

## Author

Tom-Erik Bakkely Aasheim  
Geocell  
mail@geocell.no
