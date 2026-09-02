# SchemeSetu

**Bridging citizens to state welfare entitlements.**

An interactive geospatial explorer for Indian state welfare schemes. You enter
your income, gender, category and state; SchemeSetu tells you which schemes you
qualify for, what they are collectively worth, and how that varies across the
country.

<!-- TODO: add screenshots. Run the app, then drop PNGs in docs/ and link them:
![Map view](docs/map.png)
![Matched schemes](docs/table.png)
-->

---

## Quickstart

```bash
git clone https://github.com/20tanishq10/statewise-scheme-app.git
cd statewise-scheme-app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at <http://localhost:8501>.

## What it does

- **Live filtering.** Income, gender, category and state filters apply as you
  move them; there is no submit gate, so the map is populated on first load.
- **Choropleth by total benefit.** Every state on the map is drawn, including
  those with no matching schemes, so "nothing here" is a visible answer rather
  than a hole in the map.
- **Hover detail.** Each state's tooltip lists the individual schemes behind its
  total, with amounts.
- **Ranked comparison.** A horizontal bar chart of the highest-benefit states.
- **Export.** Matched schemes download as CSV.

## Architecture

```
app.py                      Streamlit entrypoint -- widgets and layout only
schemesetu/
  config.py                 Paths, domain vocabulary, slider bounds
  data.py                   Loading + validation + normalisation (pure, no Streamlit)
  eligibility.py            The eligibility rules and aggregation (pure, tested)
  viz.py                    Plotly figure construction
  cache.py                  Streamlit caching wrappers around data.py
scripts/
  build_geodata.py          Shapefile -> simplified GeoJSON (build-time only)
data/
  schemes.csv               101 schemes across 32 states/UTs
  india_states.geojson      Generated state boundaries (67 KB)
tests/                      pytest suite over the rules and the shipped data
```

The separation is deliberate: `eligibility.py` decides what a citizen is
entitled to, and it is a pure function of a DataFrame and an `Applicant`
dataclass. It imports nothing from Streamlit, so the rules that matter most are
testable without a browser or a server.

### Why the shapefile is preprocessed

The original build shipped a zipped district shapefile and, on **every rerun**,
unzipped it and dissolved 482 district polygons into 32 states. That required
`geopandas`, `pyogrio` and `pyproj` — roughly 60 MB of wheels — at runtime, and
it is the most common reason a geospatial Streamlit app fails to deploy.

`scripts/build_geodata.py` now does that work once and writes a simplified
GeoJSON. It also fixes two latent bugs along the way:

- The source shapefile has no `.prj`, so geopandas read its CRS as `None`,
  leaving the Mercator projection undefined. The build step declares EPSG:4326.
- `dissolve` leaves self-intersections at district seams, which render as
  slivers. The build step repairs them with `buffer(0)`.

Regenerate it after any change to the source shapefile:

```bash
pip install -r requirements-dev.txt
python scripts/build_geodata.py
```

### Data note

The source CSV contains a `Category` value of `EWC`, which is not one of the
five categories the Government of India recognises (SC, ST, OBC, EWS, General).
It is a data-entry slip for `EWS`, affecting 13 rows. `data.py` corrects it on
load rather than editing the CSV, so the raw source stays byte-identical to what
was collected and the correction is visible, documented and covered by a test.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

18 tests covering the eligibility rules (income-ceiling boundaries, the `Any`
gender wildcard, empty filters meaning "no restriction" rather than "match
nothing", zero-fill for unmatched states) and the shipped data (every state in
the CSV exists on the map, categories are canonical, amounts are positive).

## Deploying to Streamlit Community Cloud

1. Push to GitHub.
2. At [share.streamlit.io](https://share.streamlit.io), point a new app at this
   repo with `app.py` as the main file.
3. Set the Python version to 3.11 or later in **Advanced settings**.

No `packages.txt` is needed — the runtime dependencies are pure-wheel.

## Limitations

- The scheme data is a **demonstration dataset** with fictional scheme names,
  not a live feed from state portals. It is representative in shape, not in
  content.
- Eligibility is modelled on four attributes (income, gender, category, state).
  Real schemes also turn on age, occupation, land holding, disability status and
  household composition.
- Boundaries are simplified to ~1.1 km tolerance, which is fine for a national
  choropleth and unsuitable for anything cadastral.

## Licence

MIT.
