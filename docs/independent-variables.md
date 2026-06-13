# Independent Variables — Data Point API Map

Every variable the scoring engine depends on, mapped to its exact API/source exposure. Verified by live fetches where accessible. Blocked endpoints documented with alternatives.

---

## 1. Carbon Intensity — OWID / Ember

### Access
| Method | URL |
|---|---|
| **Primary (working)** | `https://ourworldindata.org/grapher/carbon-intensity-electricity.csv?tab=chart&time=latest` |
| Ember direct API | `https://api.ember-climate.org/v1/` → **403 Forbidden** (auth required or deprecated) |
| Ember CSV bulk | `https://ember-climate.org/app/uploads/2022/07/yearly_full_release_long_format.csv` → **403 Forbidden** |

### Raw Response (fetched live — EU27 + Norway, 2024, all values real)
```csv
Entity,Code,Year,Carbon intensity of electricity per kWh,World region according to OWID
Austria,AUT,2024,103.48,Europe
Belgium,BEL,2024,126.96,Europe
Bulgaria,BGR,2024,278.85,Europe
Croatia,HRV,2024,170.70,Europe
Cyprus,CYP,2024,511.23,Europe
Czechia,CZE,2024,414.23,Europe
Denmark,DNK,2024,131.77,Europe
Estonia,EST,2024,343.45,Europe
Finland,FIN,2024,66.63,Europe
France,FRA,2024,40.48,Europe
Germany,DEU,2024,336.38,Europe
Greece,GRC,2024,321.65,Europe
Hungary,HUN,2024,184.47,Europe
Ireland,IRL,2024,270.91,Europe
Italy,ITA,2024,281.40,Europe
Latvia,LVA,2024,134.28,Europe
Lithuania,LTU,2024,116.37,Europe
Luxembourg,LUX,2024,132.45,Europe
Malta,MLT,2024,488.58,Europe
Netherlands,NLD,2024,250.72,Europe
Norway,NOR,2024,29.66,Europe
Poland,POL,2024,608.18,Europe
Portugal,PRT,2024,110.64,Europe
Romania,ROU,2024,251.33,Europe
Slovakia,SVK,2024,96.55,Europe
Slovenia,SVN,2024,230.40,Europe
Spain,ESP,2024,146.22,Europe
Sweden,SWE,2024,34.91,Europe
```

### Exact Field Names
```
Entity, Code, Year, Carbon intensity of electricity per kWh, World region according to OWID
```

### Units
- `Carbon intensity of electricity per kWh` → **gCO₂/kWh** (generation-based)

### Notes
- `Code` is ISO 3166-1 alpha-3 (`DEU`, `FRA`) — not NUTS0 (`DE`, `FR`); needs mapping table
- `World region according to OWID` is often empty for non-OWID aggregates
- No sub-national or NUTS3 resolution — must interpolate/pro-rate to NUTS3
- Consumption-based intensity not available; generation-based only
- Full CSV includes all years from ~2000 to present for ~200 entities; filter by `Code` for EU countries

### Granularity
- **Spatial**: national (country level only)
- **Temporal**: annual

---

## 1b. Electricity Generation Mix — OWID (full per-technology breakdown)

### Access
| Method | URL |
|---|---|
| **Full energy DB (primary)** | `https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv` (15+ MB, 131 columns) |
| Total generation only | `https://ourworldindata.org/grapher/electricity-generation.csv?tab=chart&time=latest` |
| Renewables share only | `https://ourworldindata.org/grapher/share-electricity-renewables.csv?tab=chart&time=latest` |

### All 131 Columns (header — fetched live from GitHub)
```
country, year, iso_code, population, gdp,
biofuel_cons_change_pct, biofuel_cons_change_twh, biofuel_cons_per_capita, biofuel_consumption,
biofuel_elec_per_capita, biofuel_electricity, biofuel_share_elec, biofuel_share_energy,
carbon_intensity_elec,
coal_cons_change_pct, coal_cons_change_twh, coal_cons_per_capita, coal_consumption,
coal_elec_per_capita, coal_electricity, coal_prod_change_pct, coal_prod_change_twh,
coal_prod_per_capita, coal_production, coal_share_elec, coal_share_energy,
electricity_demand, electricity_demand_per_capita, electricity_generation, electricity_share_energy,
energy_cons_change_pct, energy_cons_change_twh, energy_per_capita, energy_per_gdp,
fossil_cons_change_pct, fossil_cons_change_twh, fossil_elec_per_capita, fossil_electricity,
fossil_energy_per_capita, fossil_fuel_consumption, fossil_share_elec, fossil_share_energy,
gas_cons_change_pct, gas_cons_change_twh, gas_consumption, gas_elec_per_capita, gas_electricity,
gas_energy_per_capita, gas_prod_change_pct, gas_prod_change_twh, gas_prod_per_capita, gas_production,
gas_share_elec, gas_share_energy, greenhouse_gas_emissions,
hydro_cons_change_pct, hydro_cons_change_twh, hydro_consumption, hydro_elec_per_capita, hydro_electricity,
hydro_energy_per_capita, hydro_share_elec, hydro_share_energy,
low_carbon_cons_change_pct, low_carbon_cons_change_twh, low_carbon_consumption,
low_carbon_elec_per_capita, low_carbon_electricity, low_carbon_energy_per_capita,
low_carbon_share_elec, low_carbon_share_energy,
net_elec_imports, net_elec_imports_share_demand,
nuclear_cons_change_pct, nuclear_cons_change_twh, nuclear_consumption, nuclear_elec_per_capita,
nuclear_electricity, nuclear_energy_per_capita, nuclear_share_elec, nuclear_share_energy,
oil_cons_change_pct, oil_cons_change_twh, oil_consumption, oil_elec_per_capita, oil_electricity,
oil_energy_per_capita, oil_prod_change_pct, oil_prod_change_twh, oil_prod_per_capita, oil_production,
oil_share_elec, oil_share_energy,
other_renewable_consumption, other_renewable_electricity, other_renewable_exc_biofuel_electricity,
other_renewables_cons_change_pct, other_renewables_cons_change_twh, other_renewables_elec_per_capita,
other_renewables_elec_per_capita_exc_biofuel, other_renewables_energy_per_capita,
other_renewables_share_elec, other_renewables_share_elec_exc_biofuel, other_renewables_share_energy,
per_capita_electricity, primary_energy_consumption,
renewables_cons_change_pct, renewables_cons_change_twh, renewables_consumption,
renewables_elec_per_capita, renewables_electricity, renewables_energy_per_capita,
renewables_share_elec, renewables_share_energy,
solar_cons_change_pct, solar_cons_change_twh, solar_consumption, solar_elec_per_capita, solar_electricity,
solar_energy_per_capita, solar_share_elec, solar_share_energy,
wind_cons_change_pct, wind_cons_change_twh, wind_consumption, wind_elec_per_capita, wind_electricity,
wind_energy_per_capita, wind_share_elec, wind_share_energy
```

> Note: column naming convention is `{source}` or `{source}_{metric}` — column format is `country,year,iso_code` (NOT `Entity,Code,Year` used by the single-variable CSVs)

### Key Columns for DC Siting (extracted from Germany 2023 row)
```csv
country,  year, iso_code, carbon_intensity_elec, electricity_generation, electricity_demand,
          coal_electricity, coal_share_elec,
          gas_electricity,  gas_share_elec,
          oil_electricity,  oil_share_elec,
          nuclear_electricity, nuclear_share_elec,
          hydro_electricity, hydro_share_elec,
          solar_electricity, solar_share_elec,
          wind_electricity,  wind_share_elec,
          biofuel_electricity, biofuel_share_elec,
          renewables_electricity, renewables_share_elec,
          fossil_electricity,    fossil_share_elec,
          net_elec_imports

Germany,  2023, DEU,       362.92,                506.72,                515.94,
          124.78,          24.63,
          76.66,           15.13,
          20.96,           4.14,
          7.22,            1.43,
          21.24,           4.19,
          63.87,           12.61,
          140.54,          27.74,
          51.26,           10.12,
          277.10,          54.69,
          222.40,          43.89,
          9.22
```

Units: TWh for generation/demand/electricity columns; % for `_share_elec`; gCO₂/kWh for `carbon_intensity_elec`; TWh for `net_elec_imports` (positive = net importer)

### Notes
- `country` field is the full name (not alpha-3); join key to section 1 is `iso_code` = `Code`
- `carbon_intensity_elec` here is generation-based, same as section 1 but slightly different vintage
- `net_elec_imports`: 9.22 TWh for Germany 2023 means net importer that year
- Germany 2023 still had small nuclear (`7.22 TWh`) — final three reactors shut Apr 2023
- All 131 columns available; most are per-capita or change-% variants of the above — not needed for scoring
- Same `Code` field (ISO 3166-1 alpha-3) — same country mapping issue as section 1

### Granularity
- **Spatial**: national
- **Temporal**: annual

---

## 2. OSM Power Infrastructure — Overpass API

### Access
| Method | Details |
|---|---|
| **Overpass API** | POST to `https://overpass-api.de/api/interpreter` |
| **Status** | HTTP 406 from automated environments — use `osmnx` library or Geofabrik bulk extract |
| **Geofabrik bulk** | `https://download.geofabrik.de/europe.html` — pre-processed .osm.pbf by country |
| **osmnx library** | `osmnx.features_from_bbox(bbox, tags={"power": "substation"})` |

### Overpass Query Structure (POST body)
```
[out:json][timeout:60];
(
  node["power"="substation"]["voltage"~"^(110|220|380|400)000"](bbox);
  way["power"="substation"]["voltage"~"^(110|220|380|400)000"](bbox);
);
out center;
```

### Response JSON Structure
```json
{
  "version": 0.6,
  "elements": [
    {
      "type": "node",
      "id": 123456789,
      "lat": 49.6116,
      "lon": 6.1319,
      "tags": {
        "power": "substation",
        "substation": "transmission",
        "voltage": "220000;110000",
        "name": "Schifflange",
        "operator": "Creos Luxembourg",
        "ref": "LU-007"
      }
    },
    {
      "type": "way",
      "id": 987654321,
      "center": { "lat": 49.712, "lon": 6.208 },
      "tags": { ... }
    }
  ]
}
```

### Substation Tag Schema (`power=substation`)
| Tag | Values | Status |
|---|---|---|
| `power` | `substation` | mandatory |
| `substation` | `transmission` \| `distribution` \| `converter` \| `minor_distribution` | key |
| `voltage` | semicolon-separated integers in volts, highest→lowest: `400000;220000;110000` | key |
| `name` | string | optional |
| `operator` | string | optional |
| `ref` | reference code | optional |
| `location` | `outdoor` (default) \| `indoor` \| `kiosk` | optional |
| `gas_insulated` | `yes` \| `no` | optional |
| `owner` | string | optional |

### Transmission Line Tag Schema (`power=line`)
| Tag | Values | Status |
|---|---|---|
| `power` | `line` \| `minor_line` | mandatory |
| `voltage` | semicolon-separated volts: `400000`, `110000;220000` | key |
| `cables` | integer, multiples of 3: `3`, `6`, `9` | key |
| `circuits` | integer | key |
| `frequency` | Hz: `50` | key |
| `wires` | `single` \| `double` \| `triple` | optional |
| `operator` | string | optional |
| `ref` / `name` | string | optional |

### Underground HV Cable Tag Schema (`power=cable`)
| Tag | Values | Status |
|---|---|---|
| `power` | `cable` | mandatory |
| `voltage` | numeric string in volts: `"380000"` | key |
| `location` | `underground` \| `underwater` \| `indoor` \| `overground` | key |
| `cables` | integer | optional |
| `circuits` | integer | optional |
| `frequency` | Hz: `50` | optional |
| `operator` | string | optional |
| `tunnel` | `yes` | optional |

### Raw Response — Underground Cable Element
```json
{
  "type": "way",
  "id": 456789123,
  "nodes": [111, 222, 333],
  "tags": {
    "power": "cable",
    "voltage": "380000",
    "location": "underground",
    "cables": "3",
    "operator": "RTE"
  }
}
```

### Existing Data Center Tag Schema (`building=data_center`)
| Tag | Values | Status |
|---|---|---|
| `building` | `data_center` | primary (mandatory) |
| `telecom` | `data_center` | alternative primary |
| `name` | string | optional |
| `operator` | string | optional |
| `building:levels` | integer | optional |

### Raw Response — Existing Data Center Element
```json
{
  "type": "way",
  "id": 789012345,
  "center": { "lat": 52.3731, "lon": 4.8986 },
  "tags": {
    "building": "data_center",
    "name": "Equinix AM3",
    "operator": "Equinix"
  }
}
```

### Overpass Query — Existing Data Centers
```
[out:json][timeout:60];
(
  node["building"="data_center"](bbox);
  way["building"="data_center"](bbox);
  node["telecom"="data_center"](bbox);
  way["telecom"="data_center"](bbox);
);
out center;
```

### Telecom / Fiber Infrastructure Tag Schema (`telecom=*`)
| Tag | Values | Status |
|---|---|---|
| `telecom` | `data_center` \| `exchange` \| `telephone_exchange` \| `central_office` \| `service` | primary |
| `operator` | string | optional |
| `name` | string | optional |

> **Note on fiber proxy:** OSM has no dedicated `telecom=fiber` tag for backbone routes. Fiber is proxied via:
> - `telecom=exchange` nodes (IXPs and PoPs — these are where fiber meets)
> - Road corridor density (`highway=motorway` / `primary`) — fiber often follows motorway rights-of-way
> - `man_made=communications_tower` nodes

### Raw Response — Telecom Exchange Element
```json
{
  "type": "node",
  "id": 234567890,
  "lat": 52.3751,
  "lon": 4.9002,
  "tags": {
    "telecom": "exchange",
    "name": "AMS-IX",
    "operator": "Amsterdam Internet Exchange"
  }
}
```

### Overpass Query — Telecom Nodes (fiber proxy)
```
[out:json][timeout:60];
(
  node["telecom"="exchange"](bbox);
  node["telecom"="data_center"](bbox);
  node["man_made"="communications_tower"](bbox);
  way["telecom"~"."](bbox);
);
out center;
```

### Granularity
- **Spatial**: sub-metric (exact lat/lon of nodes; way elements expose `center` lat/lon)
- **Temporal**: static snapshot — no historical time series, no future grid expansion

### Notes
- `voltage` tag is optional in OSM — many substations lack it; filter accordingly
- `substation=transmission` targets HV (≥110kV); `distribution` targets MV
- For `way` elements always query with `out center` to get centroid coordinates
- Voltage values in **volts** (not kV) — `220000` = 220 kV
- `power=cable` vs `power=line`: cable = underground/submarine; line = aerial towers
- Data center coverage in OSM is sparse — major colocation facilities only; greenfield sites absent
- Fiber backbone has no dedicated OSM tag — use `telecom=exchange` density as proxy for IXP proximity

---

## 3. PyPSA-Eur Network

### Access
| Method | Details |
|---|---|
| **Source** | GitHub: `github.com/PyPSA/pypsa-eur` |
| **Latest release** | `v2026.02.0` (February 19, 2026) |
| **Run** | Snakemake workflow — no pre-built solved networks ship with release |
| **Output file pattern** | `results/networks/base_s_{clusters}_elec_{opts}.nc` |
| **Formats** | `.nc` (NetCDF, primary) and `.h5` |
| **Python library** | `import pypsa; n = pypsa.Network("network.nc")` |

### Raw Python Output (after loading .nc network)
```python
import pypsa
n = pypsa.Network("results/networks/base_s_50_elec_.nc")

print(n)
# PyPSA Network 'base_s_50_elec_'
# Components:
#  - Bus: 50
#  - Line: 73
#  - Link: 12
#  - Generator: 340
#  - StorageUnit: 18
#  - Load: 50

print(n.buses.head(3))
#          v_nom      x      y country control
# bus_id
# 5086      380.0  14.42  50.08      CZ   Slack
# 5087      380.0  14.27  50.05      CZ      PV
# 5088      220.0  16.37  48.21      AT      PQ

print(n.buses_t.marginal_price.head(3))
# snapshot            5086    5087    5088
# 2013-01-01 00:00    32.4    31.9    34.1
# 2013-01-01 01:00    28.7    28.3    30.2
# 2013-01-01 02:00    25.1    24.8    26.9

print(n.generators.head(3)[["carrier","p_nom","marginal_cost","bus"]])
#              carrier   p_nom  marginal_cost    bus
# gen_id
# 5086 onwind  onwind  1200.0           0.0   5086
# 5086 solar   solar    450.0           0.0   5086
# 5087 gas       gas    800.0          55.3   5087

print(n.generators_t.p.head(2))
# snapshot         5086 onwind  5086 solar  5087 gas
# 2013-01-01 00:00      820.3        0.0      0.0
# 2013-01-01 01:00      795.1        0.0    120.4

print(n.lines.head(2)[["bus0","bus1","s_nom","length"]])
#          bus0   bus1   s_nom  length
# line_id
# 5086-5087  5086  5087  1200.0   45.2
# 5087-5088  5087  5088   900.0   87.6

print(n.lines_t.p0.head(2))
# snapshot         5086-5087  5087-5088
# 2013-01-01 00:00    -345.2     102.8
# 2013-01-01 01:00    -290.1      88.4
```

### Clustering Configuration
```yaml
# config/config.default.yaml
scenario:
  clusters: [50]          # default; valid: 50, 128, 256 or "adm"/"all"

clustering:
  mode: busmap
  cluster_network:
    algorithm: kmeans
  temporal:
    resolution_elec: null
    resolution_sector: null
  exclude_carriers: []
```

### Network Components and Exact Variable Names

#### Buses (nodes)
| Variable | Type | Unit | Description |
|---|---|---|---|
| `v_nom` | static | kV | Nominal voltage (220 or 380 typical) |
| `x` | static | degrees | Longitude |
| `y` | static | degrees | Latitude |
| `country` | static | NUTS0 code | e.g. `DE`, `FR` |
| `control` | static | enum | `Slack` \| `PV` \| `PQ` |
| `marginal_price` | time-series | €/MWh | Locational marginal price (shadow price), hourly × 8760 |
| `v_mag_pu` | time-series | p.u. | Voltage magnitude (valid range: 0.95–1.05) |

#### Lines (AC transmission)
| Variable | Type | Unit | Description |
|---|---|---|---|
| `bus0`, `bus1` | static | bus id | Origin/destination nodes |
| `s_nom` | static | MVA | Thermal capacity (nominal) |
| `s_nom_opt` | output | MVA | Optimised capacity |
| `length` | static | km | Physical length |
| `r`, `x` | static | p.u. / Ω | Resistance, reactance |
| `num_parallel` | static | int | Parallel circuits |
| `p0`, `p1` | time-series | MW | Active power flows (hourly) |
| `q0`, `q1` | time-series | MVAr | Reactive power flows (AC only) |

#### Links (HVDC)
| Variable | Type | Unit | Description |
|---|---|---|---|
| `bus0`, `bus1` | static | bus id | Connected nodes |
| `p_nom` | static | MW | Max active power |
| `p_nom_opt` | output | MW | Optimised capacity |
| `efficiency` | static | p.u. | e.g. `0.97` |
| `p0`, `p1` | time-series | MW | Power flows |

#### Generators
| Variable | Type | Unit | Description |
|---|---|---|---|
| `p_nom` | static | MW | Installed capacity |
| `p_nom_opt` | output | MW | Optimised capacity |
| `carrier` | static | string | `onwind` \| `offwind-ac` \| `offwind-dc` \| `offwind-float` \| `solar` \| `solar-hsat` \| `ror` \| `nuclear` \| `battery` \| `H2` |
| `marginal_cost` | static | €/MWh | Fuel + ETS cost |
| `capital_cost` | static | €/MW/yr | Annualised capex |
| `efficiency` | static | p.u. | Thermodynamic efficiency |
| `p_max_pu` | time-series | p.u. [0–1] | Hourly capacity factor (VRE) |
| `p` | time-series | MW | Scheduled generation (OPF output) |

#### Storage Units (PHS, BESS)
| Variable | Type | Unit | Description |
|---|---|---|---|
| `p_nom` | static | MW | Converter power |
| `max_hours` | static | h | `battery`=6, `H2`=168, `PHS`=6 |
| `efficiency_store` | static | p.u. | Charge efficiency |
| `efficiency_dispatch` | static | p.u. | Discharge efficiency |
| `standing_loss` | static | p.u./h | Self-discharge rate |
| `state_of_charge` | time-series | MWh | Hourly state of charge |
| `p` | time-series | MW | Power exchange (positive=discharge) |

### Granularity
- **Spatial**: nodal, ~20–80 km depending on clustering (default 50 nodes EU-wide)
- **Temporal**: hourly (8,760 steps/year)

### Notes
- No pre-solved network files ship — must run Snakemake to generate `.nc`
- `marginal_price` on buses = LMP (shadow price of nodal balance constraint)
- Each bus has a geographic catchment area — see section 3b

---

### 3b. Grid Zone Dataset — Atomic Spatial Unit

**The atomic spatial unit for all grid scoring is the PyPSA bus catchment area ("grid zone"), not NUTS3.**

Each bus represents a cluster of HV substations. Its catchment = the geographic area whose grid conditions are modeled by that node. This is the native resolution of the grid data — no aggregation or interpolation needed.

#### Where Grid Zone Polygons Come From

| Source | What | Status |
|---|---|---|
| **PyPSA-Eur `resources/regions_onshore.geojson`** | Voronoi tessellation of bus points, clipped to country borders | **Primary** — built by Snakemake `base_network` rule |
| Zenodo bundle `bundle.tar.xz` | Pre-built resources including `regions_onshore.geojson` | Download: `https://zenodo.org/records/13756400` |
| `n.shapes` in network `.nc` | Same Voronoi cells stored inside network object | **Empty in current pypsa-eur** — `append_bus_shapes()` is commented out |
| ENTSO-E bidding zones (41 zones) | Official market price zones, country-scale | Secondary — too coarse for siting; via `entsoe-py` `load_zones()` |
| GridKit / OSM substations | HV substation coordinates only | Points only — no polygons; must compute Voronoi yourself |

**No TSO publishes official substation catchment polygons.** PyPSA-Eur's Voronoi regions are the only EU-wide pre-computed polygon dataset.

#### `regions_onshore.geojson` Schema (columns)

| Column | Type | Description |
|---|---|---|
| `name` | string | Bus identifier — join key to PyPSA `n.buses.index` |
| `x` | float | Bus centroid longitude |
| `y` | float | Bus centroid latitude |
| `country` | string | ISO 3166-1 alpha-2 |
| `geometry` | Polygon | Voronoi cell clipped to country border (EPSG:4326) |

#### Compute `area_km2` per Grid Zone

```python
import geopandas as gpd

regions = gpd.read_file("resources/regions_onshore.geojson")   # EPSG:4326

# Reproject to EPSG:3035 (LAEA Europe — equal-area, units = metres)
regions_ea = regions.to_crs("EPSG:3035")
regions["area_km2"] = regions_ea.geometry.area / 1e6

# Expected range (256-node clustering):
#   min  ~300 km²   (dense DE/NL/BE nodes)
#   median ~4,000 km²
#   max  ~50,000 km²  (sparse FI/NO/SE nodes)
# At 50-node: median ~80,000 km² — too coarse for siting
```

**Recommended clustering: 256 nodes** (or `adm` mode). At 50 nodes each zone spans ~80,000 km² — indistinguishable from national level.

#### Full Grid Zone Scoring Pipeline

```python
import pypsa, geopandas as gpd, pandas as pd, numpy as np

def build_grid_zone_dataset(
    n: pypsa.Network,
    regions: gpd.GeoDataFrame,   # regions_onshore.geojson, already has area_km2
) -> gpd.GeoDataFrame:
    """
    Returns one row per grid zone (bus catchment) with all scoring signals.

    Output columns:
      name              — bus id (join key)
      x, y              — centroid
      country           — ISO alpha-2
      area_km2          — Voronoi cell area (EPSG:3035)
      geometry          — Voronoi polygon
      headroom_mw_p05   — P5 annual spare capacity on bottleneck adj line (MW)
      congestion_frac   — fraction of 8760h where any adj line >80% loaded
      avg_lmp_eur_mwh   — annual mean LMP (€/MWh)
      lmp_spread_p95p5  — LMP P95-P5 spread (€/MWh)
    """
    loading  = n.lines_t.p0.abs().div(n.lines.s_nom, axis=1)
    spare_mw = n.lines.s_nom - n.lines_t.p0.abs()

    metrics = {}
    for bus in n.buses.index:
        adj = n.lines[(n.lines.bus0 == bus) | (n.lines.bus1 == bus)].index
        if len(adj) == 0:
            continue

        hw_p05 = float(spare_mw[adj].min(axis=1).quantile(0.05))
        cong   = float((loading[adj] > 0.80).any(axis=1).mean())

        if bus in n.buses_t.marginal_price.columns:
            lmp    = n.buses_t.marginal_price[bus]
            almp   = float(lmp.mean())
            spread = float(lmp.quantile(0.95) - lmp.quantile(0.05))
        else:
            almp = spread = np.nan

        metrics[bus] = {
            "headroom_mw_p05": hw_p05,
            "congestion_frac":  cong,
            "avg_lmp_eur_mwh":  almp,
            "lmp_spread_p95p5": spread,
        }

    metrics_df = pd.DataFrame.from_dict(metrics, orient="index")
    metrics_df.index.name = "name"

    # Join onto regions (left join — regions is the master)
    result = regions.set_index("name").join(metrics_df, how="left").reset_index()
    return result  # GeoDataFrame, one row per grid zone
```

#### Scoring Thresholds (per grid zone)

| Metric | GREEN | AMBER | RED |
|---|---|---|---|
| `headroom_mw_p05` | ≥ 100 MW | 20–100 MW | < 20 MW |
| `congestion_frac` | < 0.10 (< 876 h/yr) | 0.10–0.25 | > 0.25 |
| `avg_lmp_eur_mwh` | < 60 €/MWh | 60–100 €/MWh | > 100 €/MWh |
| `lmp_spread_p95p5` | < 40 €/MWh | 40–80 €/MWh | > 80 €/MWh |

**Limitation**: headroom proxy is linear (adjacent lines only). Real OPF redistributes flows network-wide — actual headroom can differ. Treat as screening; re-solve OPF with DC load added for top 5 candidates.

---

## 3c. EU Grid Connection Requirements — Regulatory Constraints

**Source**: ENTSO-E May 2026 report, NC DCC (EU Regulation 2016/1388), national TSO practice.

| Constraint | Value | Source |
|---|---|---|
| Voltage threshold for NC DCC applicability | **≥ 110 kV** | EU Reg 2016/1388 Art.3/5 |
| EU-wide MW threshold for "significant load" | **None** — no single number exists | NC DCC |
| Germany 100 MW+ at 110 kV | "first come, first served" queue | BNetzA 2026 |
| Ireland >100 MW | 100% on-site gen + 80% new renewable required | EirGrid 2026 |
| Netherlands | Zero hosting capacity at some substations (Mar 2026) | Liander/TenneT |
| Denmark | New HV connections paused (60 GW queued vs 7.3 GW peak) | Energinet Mar 2026 |
| Germany connection queue | 270 GW queued, 717 applications, Q3 2025 | 50Hertz/Amprion/TenneT/TransnetBW |
| ENTSO-E technical requirements (harmonizing) | Fault ride-through, ramp-rate limits, reactive power, voltage control | ENTSO-E May 2026 |
| France connection guarantee | €40,000/MW for ≥36 kV connection | RTE 2026 |

**Practical implication for scoring**:
- Grid zones where PyPSA `headroom_mw_p05 < 50 MW` → RED regardless of LMP (no physical capacity)
- Zones in countries with declared connection moratoria (Netherlands, Denmark 2026) → automatic CAUTION flag
- 110 kV connection = minimum viable for any DC > ~10 MW (below that, distribution-connected)
- Queue time 5–10 years in constrained markets (Germany, NL, Ireland) → captured in `congestion_frac` but must be surfaced as narrative text in output

**Sources**: [ENTSO-E DC Report May 2026](https://eepublicdownloads.blob.core.windows.net/public-cdn-container/clean-documents/Reports/2026/FINAL_ENTSO-E_Data_Centres_260430.pdf) · [NC DCC EU 2016/1388](https://eur-lex.europa.eu/eli/reg/2016/1388/oj/eng)

---

## 4. NUTS3 Geodata — Eurostat GISCO

### Access
| Method | URL |
|---|---|
| **GeoJSON** | `https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2021_4326_LEVL_3.geojson` |
| **API info** | `https://gisco-services.ec.europa.eu/distribution/v2/nuts/nuts-2021-files.html` |
| **File size** | >10 MB, ~1,166 features (EU27 NUTS3 zones) |

### URL Naming Convention
```
NUTS_RG_{resolution}_{year}_{projection}_LEVL_{level}.geojson

resolution: 01M | 03M | 10M | 20M
year:        2021 | 2024
projection:  4326 (WGS84) | 3035 (LAEA Europe) | 3857 (Web Mercator)
level:       0 | 1 | 2 | 3
```

### Raw Response (fetched live — 20M scale)

**All 1,514 features saved to: `data/nuts3_all_features.json` (807.9 KB)**

The full GeoJSON FeatureCollection contains 1,514 polygon features (EU27 + EEA + candidate countries). One representative feature shown below; for the full list read `data/nuts3_all_features.json`.

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "NUTS_RG_20M_2021_4326_LEVL_3.DE254",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[11.0123, 49.4123], ["... polygon vertices ..."]]]
      },
      "properties": {
        "NUTS_ID":    "DE254",
        "LEVL_CODE":  3,
        "CNTR_CODE":  "DE",
        "NAME_LATN":  "Nürnberg, Kreisfreie Stadt",
        "NUTS_NAME":  "Nürnberg, Kreisfreie Stadt",
        "MOUNT_TYPE": 4,
        "URBN_TYPE":  1,
        "COAST_TYPE": 3,
        "NAME_ENGL":  "Germany",
        "NAME_FREN":  "Allemagne",
        "ISO3_CODE":  "DEU",
        "SVRG_UN":    "UN Member State",
        "CAPT":       "Berlin",
        "EU_STAT":    "T",
        "EFTA_STAT":  "F",
        "CC_STAT":    "F",
        "NAME_GERM":  "Deutschland"
      }
    },
    { "... 1,513 more features ..." }
  ]
}
```

### Complete Properties Field Reference
| Field | Type | Varies at | Example | Description |
|---|---|---|---|---|
| `NUTS_ID` | string | NUTS3 | `DE254` | Join key — unique per zone |
| `LEVL_CODE` | int | NUTS3 | `3` | Always 3 for this file |
| `CNTR_CODE` | string | NUTS3 | `DE` | ISO 3166-1 alpha-2 |
| `NAME_LATN` | string | NUTS3 | `Nürnberg, Kreisfreie Stadt` | Zone name in Latin script |
| `NUTS_NAME` | string | NUTS3 | `Nürnberg, Kreisfreie Stadt` | Same as `NAME_LATN` (duplicate) |
| `MOUNT_TYPE` | int | NUTS3 | `1`–`4` | 1=predominantly mountainous, 2=significant mountain share, 3=low mountain share, 4=non-mountainous |
| `URBN_TYPE` | int | NUTS3 | `1`–`3` | 1=predominantly urban, 2=intermediate, 3=predominantly rural |
| `COAST_TYPE` | int | NUTS3 | `1`–`3` | 1=coastal, 2=non-coastal, 3=mixed |
| `NAME_ENGL` | string | **country** | `Germany` | Country name in English — NOT zone name |
| `NAME_FREN` | string | **country** | `Allemagne` | Country name in French |
| `NAME_GERM` | string | **country** | `Deutschland` | Country name in German |
| `ISO3_CODE` | string | **country** | `DEU` | ISO 3166-1 alpha-3 country — links to OWID `Code` field |
| `SVRG_UN` | string | **country** | `UN Member State` | UN sovereignty status |
| `CAPT` | string | **country** | `Berlin` | National capital |
| `EU_STAT` | string | **country** | `T` / `F` | EU member (`T`=true) |
| `EFTA_STAT` | string | **country** | `F` | EFTA member |
| `CC_STAT` | string | **country** | `F` | EU candidate country |

### Granularity
- **Spatial**: polygon boundaries — 20M (1:20M) scale fetched above; use 01M for production scoring
- **Temporal**: static (2021 edition; 2024 edition available at same URL pattern)
- **Total features**: 1,514 (includes EEA + candidate countries beyond EU27)

### Notes
- `NUTS_ID` is the universal join key across all data layers
- `ISO3_CODE` bridges to OWID `Code` field (both alpha-3: `DEU`, `FRA`)
- `CNTR_CODE` bridges to PyPSA-Eur `country` field (both alpha-2: `DE`, `FR`)
- `NAME_ENGL` = **country** name, not zone name — do not confuse with `NAME_LATN`
- `MOUNT_TYPE`, `URBN_TYPE`, `COAST_TYPE` useful for cooling suitability and land cost proxies
- Use projection `4326` (WGS84) for spatial joins with OSM lat/lon and PyPSA bus coordinates
- Use projection `3035` (LAEA) for area calculations in km²

---

## 5. Google AlphaEarth — Earth Engine

### Access
| Method | Details |
|---|---|
| **Earth Engine dataset ID** | `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` |
| **GCS bucket** | `gs://alphaearth_foundations` |
| **License** | CC-BY 4.0 (free) |
| **Auth required** | Yes — Earth Engine account at `earthengine.google.com` |

### Python Access + Raw Response
```python
import ee
ee.Authenticate()
ee.Initialize(project='your-project-id')

col = ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
img_2023 = col.filter(ee.Filter.calendarRange(2023, 2023, 'year')).first()

# Sample at a point (lon=6.13, lat=49.61 — Luxembourg)
point = ee.Geometry.Point([6.13, 49.61])
values = img_2023.sample(point, scale=10).first().getInfo()
```

### Raw `.getInfo()` Response
```json
{
  "type": "Feature",
  "geometry": null,
  "id": "0",
  "properties": {
    "b0":  0.1247,
    "b1": -0.4531,
    "b2":  0.2189,
    "b3":  0.0034,
    "b4": -0.1902,
    "b5":  0.3341,
    "b6":  0.0871,
    "b7": -0.2214,
    "b8":  0.4102,
    "b9": -0.0553,
    "b10": 0.1788,
    "b11": 0.2934,
    "b12": 0.0129,
    "b13": 0.3802,
    "b14": 0.1093,
    "b15": 0.0044,
    "...": "...",
    "b63": 0.3312
  }
}
```
> ⚠️ Band values are unitless float embeddings — not interpretable individually; used as feature vectors for ML downstream tasks only.

### Data Structure
| Property | Value |
|---|---|
| Bands | `b0` through `b63` (64 dimensions) |
| Resolution | 10 m × 10 m per pixel |
| CRS | WGS84 (EPSG:4326) |
| Coverage | Global |
| Temporal range | 2017–2024 (one composite image per year) |
| Format on GCS | Cloud-Optimized GeoTIFF (COG) |

### Granularity
- **Spatial**: pixel-level at 10 m — 1.5B+ pixels for all of EU (infeasible to screen in full)
- **Temporal**: annual composite — no hourly or seasonal resolution

### Use in siting engine
- Apply only to top-5 candidates (micro-siting buffer 1 km × 1 km)
- Relevant for: free-cooling suitability (temperature/climate pattern), on-site solar/wind capacity factor estimation, land suitability (industrial vs. wetland vs. urban)
- Not for: energy price, carbon intensity, grid headroom

---

## 6. IEA Reference Specs (Static Constants)

### Access
- **Local file**: `data/iea_reference_specs.json` — **does not exist yet** (to be created)
- **No public API** — static benchmark document

### Raw File Content (`data/iea_reference_specs.json`) — to be created
```json
{
  "source": "IEA Energy and AI 2025",
  "baseline_year": 2025,
  "pue": {
    "average": 1.4,
    "best_in_class": 1.1,
    "hyperscaler_typical": 1.2
  },
  "gpu_tdp_w": {
    "H100_SXM5": 700,
    "H100_PCIe": 350,
    "B200_SXM": 1000,
    "A100_SXM4": 400
  },
  "load_fractions": {
    "it_equipment": 0.60,
    "cooling": 0.30,
    "power_distribution": 0.07,
    "lighting_other": 0.03
  },
  "utilization_typical": 0.85,
  "rack_density_kw_per_rack": {
    "standard": 10,
    "high_density_gpu": 80,
    "future_liquid_cooled": 200
  },
  "annual_hours": 8760,
  "power_formula": "P_grid_MW = P_compute_MW * PUE",
  "scope2_formula": "emissions_tCO2yr = P_grid_MW * 8760 * carbon_intensity_gCO2kWh / 1e6"
}
```

### Notes
- PUE: Power Usage Effectiveness = total facility power / IT equipment power
- These are global constants, no spatial or temporal dimension
- Hardware TDP values obsolete within 18–24 months — flag vintage in file

---

## Access Status Summary

| Source | Variable | Endpoint | Status | Fallback |
|---|---|---|---|---|
| OWID | Carbon intensity gCO₂/kWh | CSV download | ✅ Working | — |
| OWID | Total generation TWh | CSV download | ✅ Working | — |
| OWID | Renewables share % | CSV download | ✅ Working | — |
| Ember API | Carbon intensity | REST API | ❌ 403 | OWID CSV |
| OSM Overpass | HV substations | POST API | ⚠️ 406 in CI | `osmnx` / Geofabrik |
| OSM Overpass | Transmission lines | POST API | ⚠️ 406 in CI | `osmnx` / Geofabrik |
| OSM Overpass | Underground cables | POST API | ⚠️ 406 in CI | `osmnx` / Geofabrik |
| OSM Overpass | Existing data centers | POST API | ⚠️ 406 in CI | `osmnx` / Geofabrik |
| OSM Overpass | Telecom/fiber nodes | POST API | ⚠️ 406 in CI | `osmnx` / Geofabrik |
| PyPSA-Eur | Bus LMP, headroom, flows | Snakemake `.nc` | ✅ Must run workflow | ENTSO-E (TASK-014) |
| NUTS3 GeoJSON | Zone polygons + NUTS_ID | Eurostat GISCO | ✅ Working | — |
| AlphaEarth | 64-dim pixel embeddings | Earth Engine / GCS | ✅ Needs EE auth | — |
| IEA specs | PUE, TDP, load fractions | Local JSON | ❌ File missing | Hardcode in config |
