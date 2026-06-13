"""
DOWNLOAD NETWORK — Zenodo PyPSA-Eur pre-built bundle
=====================================================
Downloads bundle.tar.xz from Zenodo record 13756400 (~85 MB), extracts it,
finds .nc network files, and checks whether OPF results are present.

Run from project root:
    python src/data_normalization/download_network.py

After running, set the env var printed at the end, then run:
    python src/data_normalization/02_energy_price.py   # if OPF present
    python src/data_normalization/05_congestion.py     # if OPF present
    python src/data_normalization/06_capacity.py
    python src/data_normalization/08_cleanup.py
    python src/data_normalization/09_build_table.py

If OPF results are NOT present in the bundle, run the fallback instead:
    python src/data_normalization/10_pypsa_fallback.py
"""
import os
import sys
import tarfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from _utils import setup_logger, get_paths

log = setup_logger("download_network")

ZENODO_URL = "https://zenodo.org/api/records/13756400/files/bundle.tar.xz/content"
_CHUNK = 1 << 20  # 1 MB


def _download(url: str, dest: str) -> None:
    log.info(f"Downloading {url}")
    r = requests.get(url, stream=True, timeout=300)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    received = 0
    with open(dest, "wb") as f:
        for chunk in r.iter_content(_CHUNK):
            f.write(chunk)
            received += len(chunk)
            if total:
                pct = received * 100 // total
                print(f"\r  {received // 1_048_576} / {total // 1_048_576} MB  ({pct}%)", end="", flush=True)
    print()
    log.info(f"Saved → {dest}  ({received // 1_048_576} MB)")


def _extract(archive: str, dest_dir: str) -> list[str]:
    os.makedirs(dest_dir, exist_ok=True)
    log.info(f"Extracting {archive} → {dest_dir}")
    with tarfile.open(archive, "r:xz") as tf:
        tf.extractall(dest_dir)
    # collect all extracted paths
    paths = []
    for root, _, files in os.walk(dest_dir):
        for f in files:
            paths.append(os.path.join(root, f))
    log.info(f"Extracted {len(paths)} files")
    return paths


def _check_opf(nc_path: str) -> dict:
    try:
        import pypsa
    except ImportError:
        log.warning("pypsa not installed — cannot inspect .nc file")
        return {}
    log.info(f"Inspecting {nc_path} with pypsa …")
    n = pypsa.Network(nc_path)
    result = {
        "n_buses": len(n.buses),
        "n_generators": len(n.generators),
        "marginal_price_empty": n.buses_t.marginal_price.empty,
        "lines_p0_empty": n.lines_t.p0.empty,
        "loads_t_empty": n.loads_t.p_set.empty,
    }
    log.info(
        f"  buses={result['n_buses']}  generators={result['n_generators']}\n"
        f"  buses_t.marginal_price empty: {result['marginal_price_empty']}\n"
        f"  lines_t.p0 empty:             {result['lines_p0_empty']}\n"
        f"  loads_t.p_set empty:          {result['loads_t_empty']}"
    )
    return result


def run():
    paths = get_paths()
    bundle_dir = os.path.join(paths["data"], "pypsa_bundle")
    os.makedirs(bundle_dir, exist_ok=True)

    archive = os.path.join(bundle_dir, "bundle.tar.xz")

    # -----------------------------------------------------------------------
    # 1. Download (skip if already present)
    # -----------------------------------------------------------------------
    if os.path.exists(archive):
        log.info(f"Archive already exists at {archive} — skipping download")
    else:
        _download(ZENODO_URL, archive)

    # -----------------------------------------------------------------------
    # 2. Extract
    # -----------------------------------------------------------------------
    all_files = _extract(archive, bundle_dir)

    # -----------------------------------------------------------------------
    # 3. Find .nc files
    # -----------------------------------------------------------------------
    nc_files = [f for f in all_files if f.endswith(".nc")]
    if not nc_files:
        log.warning(
            "No .nc network files found in bundle.\n"
            "The bundle is input data, not a solved network.\n"
            "Run 10_pypsa_fallback.py instead to populate columns from public data."
        )
        return

    log.info(f"Found {len(nc_files)} .nc file(s):")
    for f in nc_files:
        size_mb = os.path.getsize(f) / 1e6
        log.info(f"  {f}  ({size_mb:.1f} MB)")

    # Pick the largest .nc — most likely to be the full solved network
    chosen = max(nc_files, key=os.path.getsize)
    log.info(f"Selected: {chosen}")

    # -----------------------------------------------------------------------
    # 4. Check for OPF results
    # -----------------------------------------------------------------------
    info = _check_opf(chosen)

    # -----------------------------------------------------------------------
    # 5. Print instructions
    # -----------------------------------------------------------------------
    abs_path = os.path.abspath(chosen)
    print("\n" + "=" * 60)
    if info.get("marginal_price_empty") is False and info.get("lines_p0_empty") is False:
        print("OPF RESULTS FOUND — full pipeline available:")
        print(f"\n  set PYPSA_NETWORK_PATH={abs_path}")
        print("\nThen run:")
        print("  python src/data_normalization/02_energy_price.py")
        print("  python src/data_normalization/05_congestion.py")
        print("  python src/data_normalization/06_capacity.py")
    elif info.get("n_generators", 0) > 0:
        print("STATIC NETWORK ONLY (no OPF results):")
        print(f"\n  set PYPSA_NETWORK_PATH={abs_path}")
        print("\nRun for capacity only:")
        print("  python src/data_normalization/06_capacity.py")
        print("\nThen run fallback for energy_price + congestion:")
        print("  python src/data_normalization/10_pypsa_fallback.py")
    else:
        print("No usable network data found.")
        print("Run the full fallback:")
        print("  python src/data_normalization/10_pypsa_fallback.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run()
