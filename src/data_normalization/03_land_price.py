"""
LAND PRICE — Agricultural Land Transaction Prices (Eurostat apri_lprc)
=======================================================================
Theory
------
Land acquisition cost is a meaningful CapEx component for data center development,
typically 5–15 % of total project cost depending on site footprint and location.
A hyperscale DC (100+ MW) requires 20–100 ha of buildable land; site cost at
€20,000–€80,000/ha in rural EU regions adds €4 M–€8 M to project CapEx.

Agricultural land price (€/ha) is used as a DC siting proxy for three reasons:

  1. It is the only freely available EU-wide sub-national land price time series
     with consistent methodology, available at NUTS2 granularity via Eurostat
     dataset `apri_lprc` (Agricultural Land Prices and Rents).

  2. Farmland prices are driven by the same structural factors as industrial and
     commercial land prices: regional GDP per capita, infrastructure quality
     (proximity to highways, rail, fiber), development pressure, and urban
     proximity. A NUTS2 region with high farmland prices almost universally also
     has high industrial/commercial land prices.

  3. The Eurostat dataset records actual land transaction prices, not assessed or
     tax values — it reflects true market-clearing land costs in each region.

The "last 10 trades" rule applied here: average of the last 10 non-NaN annual
Eurostat observations per NUTS2 region. Each annual observation in `apri_lprc`
aggregates hundreds or thousands of individual agricultural land sales within the
NUTS2 region during that calendar year, so this equals averaging 10 annual market
clearing prices — a stable, low-volatility signal.

NUTS2 is the finest administrative level at which Eurostat consistently publishes
land transaction data. NUTS3 is available for some countries (Germany, France)
but not EU-wide. We use NUTS2 and assign the NUTS2 value to every PyPSA bus
whose centroid falls within that NUTS2 polygon (spatial join in 08_cleanup.py).

MVP Implementation
------------------
1. Fetch `apri_lprc` via the `eurostat` Python package (or REST API fallback).
2. Filter to unit=EUR_HA (price per hectare in euros) and landuse=AG (agricultural
   land, total arable + permanent grassland combined).
3. For each NUTS2 region: average of the last 10 non-NaN annual values.
4. Output NUTS2-level table. Spatial join to PyPSA nodes is in 08_cleanup.py.

Limitation: Farmland price ≠ industrial/DC land price. Urban NUTS2 regions
(Amsterdam, Frankfurt, Paris metropolitan) have scarce agricultural land and the
`apri_lprc` prices there are priced differently from commercial buildable land.
Rural regions near urban corridors may be underpriced in this proxy. This is a
first-order approximation suitable for macro-level regional screening.

Future Implementation
---------------------
[Empty — to be filled in dedicated planning session]

Real implementation: commercial real estate transaction databases (CoStar, CBRE,
JLL) or national land registry APIs (Kadaster NL, HM Land Registry UK, German
Katasteramt) for industrial/logistics land prices at municipality or cadastral
parcel level. These give true DC-site land costs but require commercial data
licenses or complex per-country API integrations.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import pandas as pd
from _utils import setup_logger, get_paths, ensure_dirs

log = setup_logger("03_land")

EUROSTAT_REST_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    "apri_lprc?format=JSON&lang=EN"
)

EU27_PREFIXES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE", "NO",
}


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def _fetch_package() -> pd.DataFrame | None:
    """Try the `eurostat` Python package. Returns None on failure."""
    try:
        import eurostat
        log.info("Fetching apri_lprc via eurostat package…")
        return eurostat.get_data_df("apri_lprc")
    except Exception as exc:
        log.warning(f"eurostat package failed: {exc}")
        return None


def _fetch_rest() -> pd.DataFrame:
    """
    Fallback: parse Eurostat JSON-stat REST response.
    Returns a long-format DataFrame with columns:
        unit, landuse, nuts2_code, year, land_price_raw
    """
    log.info("Fetching apri_lprc via Eurostat REST API…")
    resp = requests.get(EUROSTAT_REST_URL, timeout=180)
    resp.raise_for_status()
    data = resp.json()

    import itertools

    dim_ids = data["id"]       # list of dimension names in order
    dims = data["dimension"]
    values = data["value"]     # dict: str(flat_index) → float

    # Build ordered label lists for each dimension
    dim_keys = {
        d: list(dims[d]["category"]["index"].keys())
        for d in dim_ids
    }

    combos = list(itertools.product(*[dim_keys[d] for d in dim_ids]))
    rows = []
    for i, combo in enumerate(combos):
        val = values.get(str(i))
        if val is None:
            continue
        row = {dim_ids[j]: combo[j] for j in range(len(dim_ids))}
        row["land_price_raw"] = float(val)
        rows.append(row)

    df = pd.DataFrame(rows)
    # Standardise to lowercase column names
    df.columns = [c.lower() for c in df.columns]
    return df


def _normalise_long(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert either package (wide) or REST (already long) output to a uniform
    long-format DataFrame with columns:
        nuts2_code, year (int), land_price_raw (float), unit, landuse
    """
    cols_lower = [str(c).lower() for c in df.columns]

    # Detect if wide-format (package output has year-integers as column names)
    year_cols = [
        c for c in df.columns
        if str(c).lstrip("-").isdigit() and int(str(c).lstrip("-")) > 1990
    ]

    if year_cols:
        # Wide format from eurostat package
        df = df.reset_index() if df.index.name else df
        df.columns = [str(c).lower() if not (str(c).lstrip("-").isdigit()) else c
                      for c in df.columns]

        geo_col = next(
            (c for c in df.columns if c in (
                "geo", "geo\\time", "geo_time", "geo\\\\time",
                "geo\\time_period", "geo\\\\time_period",
            )),
            None,
        )
        unit_col = next((c for c in df.columns if c == "unit"), None)
        # agriprod is the land-use dimension in apri_lprc; also accept landuse/land_use
        landuse_col = next(
            (c for c in df.columns
             if c in ("agriprod", "landuse", "land_use") or "landuse" in c),
            None,
        )

        if unit_col:
            df = df[df[unit_col].str.upper() == "EUR_HA"]
        # For agriprod: prefer total codes; fall back to averaging all types
        if landuse_col:
            vals = df[landuse_col].str.upper().unique().tolist()
            total_codes = [v for v in vals if v in ("AG", "AA_PA", "TOTAL", "T")]
            if total_codes:
                df = df[df[landuse_col].str.upper().isin(total_codes)]
            # If no known total code exists, keep all rows (averaged later per NUTS2/year)

        if geo_col is None:
            raise ValueError(
                "Cannot locate geo/NUTS column in eurostat package output. "
                f"Available columns: {df.columns.tolist()}"
            )

        id_vars = [geo_col]
        df = df.melt(id_vars=id_vars, value_vars=year_cols,
                     var_name="year", value_name="land_price_raw")
        df = df.rename(columns={geo_col: "nuts2_code"})
        df["unit"] = "EUR_HA"
        df["landuse"] = "AG"
    else:
        # Long format from REST — rename geo column if present
        if "geo" in df.columns:
            df = df.rename(columns={"geo": "nuts2_code"})
        elif "time" in df.columns and "nuts2_code" not in df.columns:
            # Some REST responses use 'time' for year and 'geo' for region
            pass

        # Normalise unit/landuse filter
        unit_col = next((c for c in df.columns if c == "unit"), None)
        landuse_col = next(
            (c for c in df.columns if "landuse" in c or "land_use" in c), None
        )
        if unit_col:
            df = df[df[unit_col].str.upper() == "EUR_HA"]
        if landuse_col:
            df = df[df[landuse_col].str.upper() == "AG"]

        time_col = next(
            (c for c in df.columns if c in ("time", "year", "year_str")), None
        )
        if time_col and time_col != "year":
            df = df.rename(columns={time_col: "year"})

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["land_price_raw"] = pd.to_numeric(df["land_price_raw"], errors="coerce")
    df = df.dropna(subset=["year", "land_price_raw"])
    df["year"] = df["year"].astype(int)
    df["nuts2_code"] = df["nuts2_code"].astype(str).str.strip()

    return df[["nuts2_code", "year", "land_price_raw"]]


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def run():
    paths = get_paths()
    ensure_dirs()

    raw = _fetch_package()
    df = _normalise_long(raw) if raw is not None else _normalise_long(_fetch_rest())

    # Keep only proper NUTS2 codes: 2-letter country prefix + 2-digit region
    df = df[df["nuts2_code"].str.match(r"^[A-Z]{2}\d{2}$", na=False)]

    # Restrict to EU27 + Norway
    df = df[df["nuts2_code"].str[:2].isin(EU27_PREFIXES)]

    df["country"] = df["nuts2_code"].str[:2]

    # Average of last 10 non-NaN annual values per NUTS2 region
    def _last10_mean(grp: pd.DataFrame) -> pd.Series:
        valid = grp.sort_values("year").dropna(subset=["land_price_raw"])
        tail = valid.tail(10)
        return pd.Series({
            "land_price_eur_ha": tail["land_price_raw"].mean() if len(tail) > 0 else float("nan"),
            "n_years_used": len(tail),
            "last_year": int(tail["year"].max()) if len(tail) > 0 else None,
        })

    result = (
        df.groupby(["nuts2_code", "country"], group_keys=False)
        .apply(_last10_mean, include_groups=False)
        .reset_index()
    )

    result = result.dropna(subset=["land_price_eur_ha"])
    log.info(
        f"Land price: {len(result)} NUTS2 regions, "
        f"{result['country'].nunique()} countries"
    )
    log.info(
        f"Price range: {result['land_price_eur_ha'].min():.0f} – "
        f"{result['land_price_eur_ha'].max():.0f} €/ha"
    )

    out_path = os.path.join(paths["data_raw"], "land_price.parquet")
    result[
        ["nuts2_code", "country", "land_price_eur_ha", "n_years_used", "last_year"]
    ].to_parquet(out_path, index=False)
    log.info(f"Saved → {out_path}  ({len(result)} rows)")


if __name__ == "__main__":
    run()
