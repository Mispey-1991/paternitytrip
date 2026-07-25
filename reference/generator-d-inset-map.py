"""Inset map generator — Generator D.

Produces a half-page SVG showing a tight geographic area within a segment
(e.g. the Tobermory peninsula tip in Segment 1a). Reads the same Natural
Earth 10m data as Generator B. Writes segment{SEG}-inset.svg.

Generator C detects this file on disk and appends it as a final sheet in
the printable. Run Generator D AFTER Generators A, B, C for the segment.

Do NOT wrap this in a function — Notion strips common leading indent (TN-11).
"""
import json, math, os
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as esc

NE = "/home/claude/ne"

POI, HIKE, STAY, FOOD = "#2f9e44", "#e8590c", "#9c36b5", "#e03131"
CAT_COL = {"Points of Interest": POI, "Hikes": HIKE,
           "Places to Stay": STAY, "Food & Drink": FOOD}

PAPER, LAND = "#fbfaf8", "#f2efe9"
GRAT = "#e2ded6"
WATER_F, WATER_S = "#d6e7f2", "#9dc0d6"
ROAD2, ROAD1 = "#c2bcb0", "#4a4741"
INK, MUTED = "#2b2926", "#6b6660"

_CACHE = {}

def _load(name):
    if name not in _CACHE:
        with open(os.path.join(NE, name + ".geojson")) as fh:
            _CACHE[name] = json.load(fh)["features"]
    return _CACHE[name]

# ---- per-segment inputs (from Build Notes in Segments DB) --------
# SEG: string identifier matching the main segment (e.g. "1a")
# INSET_TITLE: short label shown in top-left (e.g. "Tobermory Detail")
# INSET_BBOX: (lat0, lat1, lon0, lon1) — MANUAL; do not recompute from stops.
#   The bbox in Build Notes is approved. Recomputing from stop extents will
#   produce a different frame and may clip or crowd labels.
# INSET_STOPS: subset of the segment's stops that fall in this area.
#   Same 5-tuple format as Generator B: (item_id, name, lat, lon, category)
# INSET_TOWNS: small list of named places for orientation. Same 4-tuple as
#   Generator B: (name, lat, lon, is_endpoint). Use is_endpoint=False for all
#   towns in an inset — they're reference points, not segment anchors.
# PRIMARY: same highway name as Generator B for this segment (may be empty "").

SEG          = "1a"
INSET_TITLE  = "Tobermory Detail"
INSET_BBOX   = (45.17, 45.31, -81.72, -81.42)   # lat0, lat1, lon0, lon1
PRIMARY      = "6"

INSET_STOPS = [   # (item_id, name, lat, lon, category)
    ("E1a-01", "The Crowsnest Pub",                 45.2547,    -81.6653,   "Food & Drink"),
    ("H1a-01", "Halfway Log Dump",                  45.2281,    -81.4792,   "Hikes"),
    ("I1a-01", "MS Chi-Cheemaun Ferry Terminal",    45.257139,  -81.664114, "Points of Interest"),
    ("I1a-02", "The Grotto & Indian Head Cove",     45.2452,    -81.5243,   "Points of Interest"),
    ("I1a-03", "Singing Sands Beach",               45.1912,    -81.5786,   "Points of Interest"),
    ("I1a-04", "Big Tub Lighthouse & Shipwrecks",   45.2533,    -81.6811,   "Points of Interest"),
    ("I1a-05", "Flowerpot Island",                  45.2988,    -81.6173,   "Points of Interest"),
    ("I1a-06", "Tobermory Harbourfront",             45.2544,    -81.6656,   "Points of Interest"),
    ("I1a-07", "Fathom Five NMP Visitor Centre",    45.2531,    -81.6647,   "Points of Interest"),
    ("P1a-01", "Cyprus Lake Campground",             45.2259,    -81.5248,   "Places to Stay"),
    ("P1a-02", "Wireless Bay Cottages",             45.2619937, -81.6599405,"Places to Stay"),
    ("P1a-03", "Tobermory Village Campground",      45.235723,  -81.64155,  "Places to Stay"),
    ("P1a-04", "Coach House Inn",                   45.2374748, -81.6432522,"Places to Stay"),
]

INSET_TOWNS = [   # (name, lat, lon, is_endpoint)
    ("Tobermory", 45.2544, -81.6656, False),
]

# ---- page: half Letter landscape (same width as full map, ~half height) ---
# 190 x 120 mm — fits as a second sheet on Letter paper
PW, PH = 190.0, 120.0
SC = 3.7795
W, H = PW * SC, PH * SC
FR = 6.0

# ---- projection from manual bbox ------------------------------------
lat0, lat1, lon0, lon1 = INSET_BBOX
k = math.cos(math.radians((lat0 + lat1) / 2))

# expand to match page aspect ratio
target = (H - 2 * FR) / (W - 2 * FR)
dh, dw = lat1 - lat0, (lon1 - lon0) * k
if dh / dw > target:
    grow = ((dh / target) - dw) / k / 2
    lon0 -= grow; lon1 += grow
else:
    grow = ((dw * target) - dh) / 2
    lat0 -= grow; lat1 += grow

mlon, mlat = (lon0 + lon1) / 2, (lat0 + lat1) / 2
s = (W - 2 * FR) / ((lon1 - lon0) * k)

def P(lat, lon):
    return (W / 2 + (lon - mlon) * k * s, H / 2 - (lat - mlat) * s)

BB = (lon0 - 0.1, lat0 - 0.1, lon1 + 0.1, lat1 + 0.1)

def touches(ring):
    xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
    return not (max(xs) < BB[0] or min(xs) > BB[2] or
                max(ys) < BB[1] or min(ys) > BB[3])

def polys(g):
    t, c = g["type"], g["coordinates"]
    if t == "Polygon": return [c]
    if t == "MultiPolygon": return c
    return []

def rings(g):
    t, c = g["type"], g["coordinates"]
    if t == "Polygon": return c
    if t == "MultiPolygon": return [r for p in c for r in p]
    if t == "LineString": return [c]
    if t == "MultiLineString": return c
    return []

def path(ring, close=False):
    out, prev = [], None
    for p in ring:
        x, y = P(p[1], p[0])
        if prev is None or abs(x - prev[0]) > 0.25 or abs(y - prev[1]) > 0.25:
            out.append(f"{x:.1f} {y:.1f}"); prev = (x, y)
    if len(out) < 2:
        return None
    return "M " + " L ".join(out) + (" Z" if close else "")

o = []
a = o.append

# ---- canvas ---------------------------------------------------------
a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.1f}" height="{H:.1f}" '
  f'viewBox="0 0 {W:.1f} {H:.1f}" font-family="Helvetica,Arial,sans-serif">')
a(f'<defs><clipPath id="ifr"><rect x="{FR}" y="{FR}" '
  f'width="{W-2*FR:.1f}" height="{H-2*FR:.1f}"/></clipPath></defs>')
a(f'<rect width="{W:.1f}" height="{H:.1f}" fill="{PAPER}"/>')
a(f'<rect x="{FR}" y="{FR}" width="{W-2*FR:.1f}" height="{H-2*FR:.1f}" fill="{LAND}"/>')
a('<g clip-path="url(#ifr)">')

# ---- graticule, 0.05 deg (tighter for inset scale) ------------------
g0 = math.floor(lat0 * 20) / 20
while g0 <= lat1:
    y = P(g0, mlon)[1]
    a(f'<line x1="{FR}" y1="{y:.1f}" x2="{W-FR:.1f}" y2="{y:.1f}" '
      f'stroke="{GRAT}" stroke-width="0.4"/>')
    a(f'<text x="{FR+2:.1f}" y="{y-2:.1f}" font-family="monospace" font-size="4.5" '
      f'fill="{MUTED}">{g0:.2f}\u00b0N</text>')
    g0 = round(g0 + 0.05, 10)
g1 = math.floor(lon0 * 20) / 20
while g1 <= lon1:
    x = P(mlat, g1)[0]
    a(f'<line x1="{x:.1f}" y1="{FR}" x2="{x:.1f}" y2="{H-FR:.1f}" '
      f'stroke="{GRAT}" stroke-width="0.4"/>')
    a(f'<text x="{x+2:.1f}" y="{H-FR-2:.1f}" font-family="monospace" font-size="4.5" '
      f'fill="{MUTED}">{abs(g1):.2f}\u00b0W</text>')
    g1 = round(g1 + 0.05, 10)

# ---- water ----------------------------------------------------------
for f in _load("ne_10m_lakes"):
    for poly in polys(f["geometry"]):
        if not touches(poly[0]):
            continue
        ds = [d for d in (path(r, close=True) for r in poly) if d]
        if ds:
            a(f'<path d="{" ".join(ds)}" fill="{WATER_F}" fill-rule="evenodd" '
              f'stroke="{WATER_S}" stroke-width="0.5"/>')
for f in _load("ne_10m_coastline"):
    for r in rings(f["geometry"]):
        if not touches(r):
            continue
        d = path(r)
        if d:
            a(f'<path d="{d}" fill="none" stroke="{WATER_S}" stroke-width="0.6"/>')

# ---- roads ----------------------------------------------------------
for f in _load("ne_10m_roads"):
    nm = (f["properties"].get("name") or "").strip()
    if not nm:
        continue
    for r in rings(f["geometry"]):
        if not touches(r):
            continue
        d = path(r)
        if not d:
            continue
        if nm == PRIMARY:
            a(f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="4.0" '
              f'stroke-linecap="round" stroke-linejoin="round"/>')
            a(f'<path d="{d}" fill="none" stroke="{ROAD1}" stroke-width="2.2" '
              f'stroke-linecap="round" stroke-linejoin="round"/>')
        else:
            a(f'<path d="{d}" fill="none" stroke="{ROAD2}" stroke-width="1.2" '
              f'stroke-dasharray="5,2"/>')

# ---- towns ----------------------------------------------------------
for nm, la, lo, endpoint in INSET_TOWNS:
    x, y = P(la, lo)
    r = 3.0 if endpoint else 2.0
    a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#ffffff" '
      f'stroke="{INK}" stroke-width="1.0"/>')
    a(f'<text x="{x:.1f}" y="{y-r-2:.1f}" text-anchor="middle" '
      f'font-size="7" font-weight="{"bold" if endpoint else "normal"}" fill="{INK}" '
      f'paint-order="stroke" stroke="{LAND}" stroke-width="2.8" '
      f'stroke-linejoin="round">{esc(nm)}</text>')

# ---- stops + labels -------------------------------------------------
xmid = sum(P(st[2], st[3])[0] for st in INSET_STOPS) / len(INSET_STOPS)
placed = {1: [], -1: []}
for iid, nm, la, lo, cat in sorted(INSET_STOPS, key=lambda t: -t[2]):
    col = CAT_COL[cat]
    x, y = P(la, lo)
    side = 1 if x < xmid else -1
    ly = y
    for py in placed[side]:
        if abs(ly - py) < 13:
            ly = py + 13
    placed[side].append(ly)
    lx = x + side * 28
    a(f'<path d="M {x:.1f} {y:.1f} L {x+side*11:.1f} {ly:.1f} L {lx:.1f} {ly:.1f}" '
      f'fill="none" stroke="{col}" stroke-width="0.7" opacity="0.75"/>')
    a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="{col}" '
      f'stroke="#ffffff" stroke-width="1.4"/>')
    anch = "start" if side == 1 else "end"
    tx = lx + side * 2
    a(f'<text x="{tx:.1f}" y="{ly-1:.1f}" text-anchor="{anch}" '
      f'font-family="monospace" font-size="6.5" font-weight="bold" fill="{col}" '
      f'paint-order="stroke" stroke="{LAND}" stroke-width="2.8" '
      f'stroke-linejoin="round">{esc(iid)}</text>')
    a(f'<text x="{tx:.1f}" y="{ly+7:.1f}" text-anchor="{anch}" '
      f'font-family="Georgia,serif" font-size="7.5" fill="{INK}" '
      f'paint-order="stroke" stroke="{LAND}" stroke-width="2.8" '
      f'stroke-linejoin="round">{esc(nm)}</text>')

a('</g>')

# ---- furniture ------------------------------------------------------
a(f'<rect x="{FR}" y="{FR}" width="{W-2*FR:.1f}" height="{H-2*FR:.1f}" '
  f'fill="none" stroke="{INK}" stroke-width="1"/>')

# title block
tx, ty = FR + 10, FR + 16
a(f'<text x="{tx}" y="{ty}" font-size="6" letter-spacing="2" fill="{MUTED}" '
  f'paint-order="stroke" stroke="{LAND}" stroke-width="2.8">'
  f'SEGMENT {esc(SEG)} \u2014 DETAIL</text>')
a(f'<text x="{tx}" y="{ty+14:.1f}" font-family="Georgia,serif" font-size="12" '
  f'font-weight="bold" fill="{INK}" paint-order="stroke" stroke="{LAND}" '
  f'stroke-width="2.8">{esc(INSET_TITLE)}</text>')

# scale bar
seg_px = 5.0 / 111.0 * s   # 5 km segments at inset scale
sx0, sy0 = W - FR - 16 - seg_px * 2, H - FR - 18
a(f'<rect x="{sx0:.1f}" y="{sy0:.1f}" width="{seg_px:.1f}" height="3" '
  f'fill="{INK}" stroke="{INK}" stroke-width="0.5"/>')
a(f'<rect x="{sx0+seg_px:.1f}" y="{sy0:.1f}" width="{seg_px:.1f}" height="3" '
  f'fill="#ffffff" stroke="{INK}" stroke-width="0.5"/>')
for i, lab in enumerate(("0", "5", "10")):
    a(f'<text x="{sx0+seg_px*i:.1f}" y="{sy0-2:.1f}" text-anchor="middle" '
      f'font-family="monospace" font-size="5" fill="{INK}">{lab}</text>')
a(f'<text x="{sx0+seg_px:.1f}" y="{sy0+10:.1f}" text-anchor="middle" '
  f'font-family="monospace" font-size="5" fill="{MUTED}">km</text>')

# north arrow
nx, ny = W - FR - 14, FR + 14
a(f'<path d="M {nx} {ny-8} L {nx+4} {ny+4} L {nx} {ny+1} L {nx-4} {ny+4} Z" '
  f'fill="{INK}"/>')
a(f'<text x="{nx}" y="{ny+12}" text-anchor="middle" font-size="6" '
  f'font-weight="bold" fill="{INK}">N</text>')

a('</svg>')
out = "".join(o)
ET.fromstring(out)
open(f"segment{SEG}-inset.svg", "w").write(out)
print(f"Seg {SEG} inset: {len(out):,} bytes")
