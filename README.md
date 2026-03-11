# Iconic

Iconic er et QGIS-plugin for å jobbe med SVG-baserte ikonpakker i punktlag.

Pluginen gir deg et eget dock-panel i QGIS der du kan:

- installere, oppdatere og avinstallere ikonpakker
- søke og filtrere ikoner etter pakke og kategori
- forhåndsvise tilgjengelige SVG-ikoner
- plassere nye punktobjekter i kartet med valgt ikon
- style eksisterende punktlag med SVG-ikoner
- bruke ikoninformasjon lagret i felt på laget

## Funksjoner

### Ikonpakker

Iconic henter en pakkeliste fra en ekstern `packages.xml` og lar deg installere ikonpakker direkte fra pluginen. Hver pakke kan inneholde:

- SVG-filer
- tilhørende JSON-fil med navn, beskrivelser, kategorier og varianter

Pluginen støtter også oppdateringssjekk mot tilgjengelige pakkeversjoner.

### Ikonvalg

I dock-panelet kan du:

- søke etter ikonnavn eller beskrivelse
- filtrere på ikonpakke
- filtrere på kategori
- velge variant der dette finnes
- angi symbolstørrelse i mm

### Plassering av nye punkt

Når du velger **Plassér nye punkter ved klikk i kartet**, kan du klikke direkte i kartflaten og opprette nye punktobjekter med valgt SVG-ikon.

### Styling av eksisterende punktlag

Når du velger **Style eksisterende lag**, kan pluginen:

- opprette nødvendige felt dersom de mangler
- lagre SVG-informasjon i laget
- bruke kategorisert renderer på `svg_path`
- overskrive eksisterende ikonverdier dersom ønskelig

## Felt som brukes

Pluginen bruker disse feltene i punktlaget:

- `icon_source`
- `svg_name`
- `svg_path`
- `svg_size`
- `svg_variant`
- `svg_category`
- `svg_pack`

Disse brukes til å lagre informasjon om hvilket ikon som er valgt, hvor SVG-filen ligger, størrelse og eventuell variant.

## Krav

- QGIS 3.34 eller nyere
- Støtter også QGIS 4 / Qt6

## Installasjon

1. Installer pluginen i QGIS
2. Åpne **Iconic** fra meny eller verktøylinje
3. Åpne **Ikonpakker**
4. Installer ønsket pakke
5. Velg ikon og bruk pluginen til plassering eller styling

## Ikonpakker

Pluginen forventer en pakkeliste i XML-format med lenker til:

- ZIP med SVG-filer
- JSON med ikonmetadata

Pakker installeres lokalt i QGIS sin AppData-mappe.

## Status

Pluginen er under aktiv utvikling. Fokus har vært på stabil støtte for både QGIS 3 og QGIS 4, inkludert Qt6-kompatibilitet.

## Forfatter

Tom-Erik Bakkely Aasheim  
Geocell  
mail@geocell.no
