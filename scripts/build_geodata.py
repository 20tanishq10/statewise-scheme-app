"""One-time build step: shapefile -> simplified state-level GeoJSON.

The raw district shapefile (india_ds.zip) is ~126 KB zipped but needs
geopandas + pyogrio + pyproj (~60 MB of wheels) to read, and dissolving
districts into states takes ~1s. Doing that on every Streamlit rerun is
wasteful, so we do it once here and commit the result.

Run after any change to the source shapefile:

    python scripts/build_geodata.py
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
SOURCE_ZIP = ROOT / "india_ds.zip"
OUTPUT = ROOT / "data" / "india_states.geojson"

# The source shapefile carries no .prj, so geopandas reads crs as None.
# The coordinates are plain lon/lat degrees, so we declare WGS 84 explicitly
# -- without this, any reprojection downstream is undefined behaviour.
SOURCE_CRS = "EPSG:4326"

# Douglas-Peucker tolerance in degrees. 0.01 deg ~ 1.1 km, which is far below
# what a national-scale choropleth can resolve, and cuts the payload ~10x.
SIMPLIFY_TOLERANCE = 0.01


def build() -> Path:
    with TemporaryDirectory() as tmp:
        with zipfile.ZipFile(SOURCE_ZIP) as archive:
            archive.extractall(tmp)
        districts = gpd.read_file(next(Path(tmp).glob("*.shp")))

    districts = districts.set_crs(SOURCE_CRS, allow_override=True)
    states = districts.dissolve(by="STATE").reset_index()[["STATE", "geometry"]]

    # buffer(0) repairs self-intersections that dissolve can leave behind at
    # district seams; without it a few states render as slivers in Plotly.
    states["geometry"] = states.geometry.buffer(0).simplify(
        SIMPLIFY_TOLERANCE, preserve_topology=True
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # id at the feature level is what Plotly matches `locations` against.
    payload = json.loads(states.to_json())
    for feature in payload["features"]:
        feature["id"] = feature["properties"]["STATE"]
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":")))
    return OUTPUT


if __name__ == "__main__":
    path = build()
    size_kb = path.stat().st_size / 1024
    print(f"wrote {path.relative_to(ROOT)} ({size_kb:.0f} KB)")
