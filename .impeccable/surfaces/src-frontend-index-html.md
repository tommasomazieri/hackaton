---
version: 1
slug: "src-frontend-index-html"
primary_target: "src/frontend/index.html"
related_targets: []
---

## Scope

The DC Hound console (`src/frontend/index.html`) and its printable export. Mode: Operate. A replacement world: the old dark CARTO/amber dashboard is evidence, not authority.

## Audience and job

The site-selection analyst screens EU grid regions for one data-center brief (MW, m², countries, weights) and leaves with a defensible shortlist. Cold visitors (team, investors, prospects) must read a real ranked result on first load. Approvers only see the export.

Constraints: the model side is untouched; the UI presents `/api/query`, `/api/sources`, `/api/sites/{id}`. Never oversell the stated limits in PRODUCT.md: congestion is a national proxy, land is farmland, and there is no queue or regulatory layer.

## Direction contract

THESIS: DC Hound is a grid operator's overview display turned on siting: a quiet grey console where only what deviates, the shortlist and the data faults, carries colour. It refuses the dark full-bleed map with a card sidebar and KPI tiles.

OWN-WORLD: ISA-101 high-performance HMI. The ground is #dcdfe1, faceplates are a slightly lighter flat grey, ink is #2b2f33 and mid-grey is #8b9298. Amber #e0a800 marks the shortlist and selection only; red #b3261e marks faults (excluded regions, failed or stale sources, proxy warnings). The components are flat faceplates with engraved labels, analog-bar readouts with a field-range track and a median tick, setpoint bars for weights, and tabular numerals in fixed digit slots. The map is a schematic tile-free mimic of Europe with countries as grey plates.

STORY: On load the visitor sees Europe with every region as a grey dot and the ten best as amber numbered markers, next to a ranked readout table. They see why each site ranks where it does (a four-part contribution bar), change the brief and watch the order re-sort, open a site's faceplate for every figure and its source, and export a standalone report.

FIRST VIEWPORT: The status bar spans the top: wordmark, data build time, region count, excluded count as a red fault chip, sources, and Export at the right. The input faceplate is fixed on the left at about 300px: load MW, footprint m², the country filter and four weight setpoints. The schematic map fills the upper centre with the numbered amber shortlist. The ranked readouts sit below the map, one row per site: rank, region name with its NUTS code and country, the four analog readouts, and the contribution bar. Selecting a site docks its faceplate over the map's right edge. There is no Run button: every change re-queries.

FORM: Control Room (ISA-101 HMI), my own top-ranked grounded candidate (1 of 7), chosen over the rolled Site Datasheet. Seed key d6f19049. Signature interaction: moving a weight setpoint re-ranks live; rows slide to their new positions (FLIP, 200 ms) and show a rank delta; digits change in place without reflow; the map's numbered markers follow. Motion grammar: state changes only, 150–250 ms ease-out, no entrance choreography. Raises kept from the declined hand: each rank decomposed into weighted contributions; the country filter is also the map's geometry; the shortlist is labelled on the map without hover; fixed digit slots; one rank-to-emphasis scale shared by row, marker and export.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Memorable moment

Dragging the carbon weight up and watching Nordic regions slide into the amber top ten on the map and in the table at the same time.

## Unresolved

- Region names depend on a GISCO field added to the node cache. If it is missing, the UI falls back to NUTS codes.
- The site analysis's own "grid distance" and "road distance" inputs look broken (for example 1,310 km and infinity). The UI shows buildable land only and does not show those scores. This is the algorithm side, so it is flagged to the owner.
