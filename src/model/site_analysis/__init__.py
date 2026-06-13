"""
site_analysis — post-Pareto CNN land-suitability pipeline.

Runs the pretrained Google Dynamic World CNN on Sentinel-2 imagery fetched
on-the-go for the top-N ranked nodes, scores buildable land, and returns the
bounding box + largest inscribed circle marking where to place the data center.

Submodules:
    fetch_model  vendor the DW SavedModel
    imagery      Planetary Computer S2 + DEM fetch
    dw_model     DW preprocess + tiled inference
    osm          grid / road / landuse layers
    constraints  EEA Natura 2000 + CDDA exclusion
    scoring      DW class -> suitability score spec
    geometry     buildable patches + inscribed circle

Orchestrated by src/model/04_site_analysis.py.
"""
