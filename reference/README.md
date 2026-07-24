# Reference: Generator Code

Canonical source for all generators. Operations 7 and 8 fetch these at build time via GitHub raw URLs.

## generator-a-route-line.py

Generates the route-line SVG for a segment — four horizontal category lines spanning the segment's geographic extent, with stops marked by Item ID.

- **Input:** SEG, SEG_TITLE, STOPS (item_id, category, lat, lon), ENDPOINTS (start/end towns)
- **Output:** `segmentN-route-line.svg`
- **Dependencies:** stdlib only

## generator-b-full-page-map.py

Generates the full-page geographic map for a segment — real coastlines, lakes, roads, and graticule from Natural Earth 10m geodata.

- **Input:** SEG, SEG_TITLE, SEG_META, PRIMARY (highway), STOPS, TOWNS
- **Output:** `segmentN-map.svg`
- **Dependencies:** stdlib only; Natural Earth GeoJSON files (ne_10m_lakes, ne_10m_coastline, ne_10m_roads)
- **Data source:** https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/

**Note:** Both generators are top-level scripts (no wrapping functions). Notion's connector strips common leading indent from code blocks, which would break nested code. These run exactly as written.

---

**Last updated:** 2026-07-24

**Pinned commit for Operations 7 & 8:** Use the URL with `@<commit-hash>` to fetch a specific version and ensure reproducibility.

