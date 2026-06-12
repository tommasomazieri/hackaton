import os
import urllib.request
import json
import time

def create_folders():
    print("Creating 'data' and 'src/data_ingestion' folders...")
    os.makedirs("data", exist_ok=True)
    os.makedirs("src/data_ingestion", exist_ok=True)
    print("Folders created successfully.")

def download_file(url, destination_path):
    print(f"Downloading from {url} to {destination_path}...")
    start_time = time.time()
    try:
        # Use urllib to stream the download and print progress
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req) as response, open(destination_path, 'wb') as out_file:
            meta = response.info()
            file_size_header = meta.get("Content-Length")
            file_size = int(file_size_header) if file_size_header else None
            
            if file_size:
                print(f"File size: {file_size / (1024 * 1024):.2f} MB")
            else:
                print("File size unknown, downloading stream...")

            bytes_downloaded = 0
            block_size = 1024 * 1024  # 1MB blocks
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                bytes_downloaded += len(buffer)
                out_file.write(buffer)
                if file_size:
                    percent = (bytes_downloaded / file_size) * 100
                    print(f"Progress: {percent:.1f}% ({bytes_downloaded / (1024 * 1024):.2f} MB / {file_size / (1024 * 1024):.2f} MB)", end='\r')
                else:
                    print(f"Downloaded: {bytes_downloaded / (1024 * 1024):.2f} MB", end='\r')
            print()
        elapsed = time.time() - start_time
        print(f"Success! Download completed in {elapsed:.1f} seconds.\n")
    except Exception as e:
        print(f"Error downloading {url}: {e}\n")

def fetch_osm_power_grid():
    print("Querying Overpass API for Luxembourg's power grid infrastructure (substations and high-voltage lines)...")
    # Overpass QL query targeting power lines and substations in Luxembourg (LU)
    query = """
    [out:json][timeout:90];
    area["ISO3166-1"="LU"]->.searchArea;
    (
      node["power"="substation"](area.searchArea);
      way["power"="line"](area.searchArea);
      way["power"="cable"](area.searchArea);
    );
    out body;
    >;
    out skel qt;
    """
    
    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({'data': query}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Antigravity Siting Tool Hackathon (gabbo@gabbo.com)'})
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            elements = result.get('elements', [])
            nodes_count = sum(1 for e in elements if e['type'] == 'node')
            ways_count = sum(1 for e in elements if e['type'] == 'way')
            print(f"OSM Query Success! Found {len(elements)} power elements ({nodes_count} nodes/substations, {ways_count} transmission lines).")
            
            output_path = "data/osm_power_infrastructure.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Saved OSM data to {output_path} in {time.time() - start_time:.1f} seconds.\n")
    except Exception as e:
        print(f"Error fetching OSM data: {e}\n")

def create_iea_ai_reference():
    print("Creating IEA Energy & AI reference specifications file...")
    specs = {
        "source": "IEA - Energy and AI Report 2025/2026",
        "last_updated": "2026-06-12",
        "data_center_electricity_projections": {
            "2026_global_consumption_est_twh": 945.0,
            "annual_growth_rate_pct": 17.0,
            "target_growth_2030": "double"
        },
        "typical_power_distribution_pct": {
            "servers_it_load": 60.0,
            "cooling_systems": 30.0,
            "storage": 5.0,
            "networking": 5.0
        },
        "reference_pue_benchmarks": {
            "state_of_the_art": 1.1,
            "global_average_2025": 1.5,
            "legacy": 2.0
        },
        "gpu_power_characteristics": {
            "nvidia_h100_tdp_w": 700.0,
            "nvidia_b200_tdp_w": 1000.0,
            "estimated_pue_overhead": 0.3
        }
    }
    
    output_path = "data/iea_reference_specs.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(specs, f, indent=2, ensure_ascii=False)
    print(f"Saved IEA reference specs to {output_path}.\n")

if __name__ == "__main__":
    create_folders()
    
    # 1. Download Our World in Data Energy (Ember integrated)
    owid_url = "https://owid-public.owid.io/data/energy/owid-energy-data.csv"
    download_file(owid_url, "data/owid-energy-data.csv")
    
    # 2. Fetch OSM infrastructure
    fetch_osm_power_grid()
    
    # 3. Create IEA specifications
    create_iea_ai_reference()
    
    print("All databases and reference data initialized in the 'data/' folder!")
