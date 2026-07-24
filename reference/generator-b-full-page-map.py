"""Full-page segment map generator.

Emits a self-contained SVG. Stdlib only (cairosvg optional, preview only).
Set the per-segment inputs below, then run. Nothing else is
segment-specific.
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



# ---- per-segment inputs (from Route Stops + Segments + places_search) ----
SEG         = 3
SEG_TITLE   = "Sault Ste. Marie \u2192 Wawa"
SEG_META    = "Hwy 17 N \u00b7 ~235 km \u00b7 ~2.5 hrs"
PRIMARY     = "17"          # matches properties.name in ne_10m_roads
STOPS = [   # (item_id, name, lat, lon, category)
    ("I3-01", "Chippewa Falls", 46.9280482, -84.4257830, "Points of Interest"),
    # ... one tuple per row returned by the Route Stops query
]
TOWNS = [   # (name, lat, lon, is_endpoint)
    ("Sault Ste. Marie", 46.5153817, -84.3330487, True),
    ("Wawa", 47.9922017, -84.7709192, True),
]


# ---- bbox from stops + towns, padded --------------------------------
lats = [s[2] for s in STOPS] + [t[1] for t in TOWNS]
lons = [s[3] for s in STOPS] + [t[2] for t in TOWNS]
lat0, lat1 = min(lats) - 0.10, max(lats) + 0.10
lon0, lon1 = min(lons) - 0.10, max(lons) + 0.10
k = math.cos(math.radians((lat0 + lat1) / 2))

# ---- page: Letter, 14mm margins; orientation from the segment's shape
PORTRAIT = (lat1 - lat0) > (lon1 - lon0) * k
PW, PH = (190.0, 251.0) if PORTRAIT else (251.0, 190.0)
SC = 3.7795
W, H = PW * SC, PH * SC
FR = 6.0

# expand the deficient axis so the bbox aspect matches the page
target = (H - 2 * FR) / (W - 2 * FR)
dh, dw = lat1 - lat0, (lon1 - lon0) * k
if dh / dw > target:
    grow = ((dh / target) - dw) / k / 2
    lon0 -= grow; lon1 += grow
else:
    grow = ((dw * target) - dh) / 2
    lat0 -= grow; lat1 += grow

mlon, mlat = (lon0 + lon1) / 2, (lat0 + lat1) / 2
s = (W - 2 * FR) / ((lon1 - lon0) * k)      # ONE scale for both axes

def P(lat, lon):
    return (W / 2 + (lon - mlon) * k * s, H / 2 - (lat - mlat) * s)

# ---- geometry helpers ----------------------------------------------
BB = (lon0 - 0.4, lat0 - 0.4, lon1 + 0.4, lat1 + 0.4)

def touches(ring):
    """Bbox-overlap test, NOT vertex-in-bbox.

    A polygon far larger than the frame -- Lake Superior on a 1.5 deg
    segment -- has no vertex inside BB and a vertex test drops it
    entirely. Comparing extents is what makes big water reliable.
    """
    xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
    return not (max(xs) < BB[0] or min(xs) > BB[2] or
                max(ys) < BB[1] or min(ys) > BB[3])

def polys(g):
    """Polygons as ring-groups, holes preserved.

    Flattening rings loses the hole/exterior distinction and paints
    every island as water. Lake Huron is ONE polygon with 15 rings:
    the outer lake plus 14 islands, Manitoulin among them. Draw the
    group as a single path with fill-rule=evenodd so the holes punch
    through to the land beneath.
    """
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
        if prev is None or abs(x - prev[0]) > 0.35 or abs(y - prev[1]) > 0.35:
            out.append(f"{x:.1f} {y:.1f}"); prev = (x, y)
    if len(out) < 2:
        return None
    return "M " + " L ".join(out) + (" Z" if close else "")

o = []
a = o.append

# ---- canvas ---------------------------------------------------------
a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.1f}" height="{H:.1f}" '
  f'viewBox="0 0 {W:.1f} {H:.1f}" font-family="Helvetica,Arial,sans-serif">')
a(f'<defs><clipPath id="fr"><rect x="{FR}" y="{FR}" '
  f'width="{W-2*FR:.1f}" height="{H-2*FR:.1f}"/></clipPath></defs>')
a(f'<rect width="{W:.1f}" height="{H:.1f}" fill="{PAPER}"/>')
a(f'<rect x="{FR}" y="{FR}" width="{W-2*FR:.1f}" height="{H-2*FR:.1f}" fill="{LAND}"/>')
a('<g clip-path="url(#fr)">')

# ---- layer 2: graticule, 0.25 deg -----------------------------------
g0 = math.floor(lat0 * 4) / 4
while g0 <= lat1:
    y = P(g0, mlon)[1]
    a(f'<line x1="{FR}" y1="{y:.1f}" x2="{W-FR:.1f}" y2="{y:.1f}" '
      f'stroke="{GRAT}" stroke-width="0.5"/>')
    a(f'<text x="{FR+3:.1f}" y="{y-2:.1f}" font-family="monospace" font-size="5" '
      f'fill="{MUTED}">{g0:.2f}\u00b0N</text>')
    g0 += 0.25
g1 = math.floor(lon0 * 4) / 4
while g1 <= lon1:
    x = P(mlat, g1)[0]
    a(f'<line x1="{x:.1f}" y1="{FR}" x2="{x:.1f}" y2="{H-FR:.1f}" '
      f'stroke="{GRAT}" stroke-width="0.5"/>')
    a(f'<text x="{x+2:.1f}" y="{H-FR-3:.1f}" font-family="monospace" font-size="5" '
      f'fill="{MUTED}">{abs(g1):.2f}\u00b0W</text>')
    g1 += 0.25

# ---- layer 3: water -------------------------------------------------
for f in _load("ne_10m_lakes"):
    for poly in polys(f["geometry"]):
        if not touches(poly[0]):
            continue
        ds = [d for d in (path(r, close=True) for r in poly) if d]
        if ds:
            a(f'<path d="{" ".join(ds)}" fill="{WATER_F}" fill-rule="evenodd" '
              f'stroke="{WATER_S}" stroke-width="0.6"/>')
for f in _load("ne_10m_coastline"):
    for r in rings(f["geometry"]):
        if not touches(r):
            continue
        d = path(r)
        if d:
            a(f'<path d="{d}" fill="none" stroke="{WATER_S}" stroke-width="0.7"/>')

# ---- roads: split primary from secondary ----------------------------
prim, sec = [], []
for f in _load("ne_10m_roads"):
    nm = (f["properties"].get("name") or "").strip()
    if not nm:
        continue
    for r in rings(f["geometry"]):
        if not touches(r):
            continue
        (prim if nm == PRIMARY else sec).append((nm, r))

def shield(x, y, label, w=22, h=16):
    return (f'<g><rect x="{x-w/2:.1f}" y="{y-h/2:.1f}" width="{w}" height="{h}" '
            f'rx="3" fill="#ffffff" stroke="{ROAD1}" stroke-width="1"/>'
            f'<text x="{x:.1f}" y="{y+3.6:.1f}" text-anchor="middle" '
            f'font-family="Helvetica,Arial,sans-serif" font-size="9.5" '
            f'font-weight="bold" fill="{ROAD1}">{esc(label)}</text></g>')

# layer 4: secondary highways
seen = set()
for nm, r in sec:
    d = path(r)
    if not d:
        continue
    a(f'<path d="{d}" fill="none" stroke="{ROAD2}" stroke-width="1.5" '
      f'stroke-dasharray="7,3"/>')
    if nm not in seen and len(r) > 2:
        pl = [P(p[1], p[0]) for p in r]
        vis = [p for p in pl
               if FR + 14 < p[0] < W - FR - 14 and FR + 14 < p[1] < H - FR - 14]
        if vis:
            seen.add(nm)
            a(shield(*vis[len(vis)//2], nm, w=17, h=12))

# layer 5: primary highway -- EVERY matching feature, not just the first
longest, longest_len = None, 0.0
for nm, r in prim:
    d = path(r)
    if not d:
        continue
    a(f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="5.4" '
      f'stroke-linecap="round" stroke-linejoin="round"/>')
    a(f'<path d="{d}" fill="none" stroke="{ROAD1}" stroke-width="2.9" '
      f'stroke-linecap="round" stroke-linejoin="round"/>')
    pl = [P(p[1], p[0]) for p in r]
    L = sum(math.dist(pl[i-1], pl[i]) for i in range(1, len(pl)))
    if L > longest_len:
        longest, longest_len = pl, L

def inbounds(p, pad=12):
    return FR + pad < p[0] < W - FR - pad and FR + pad < p[1] < H - FR - pad

def at_fraction(pl, frac):
    """Point at `frac` along ONE feature's own length.

    Never measure across features: Natural Earth splits a route into
    several disjoint pieces, and running a cumulative distance through
    the concatenation jumps between them, so the fraction is meaningless
    and the shield lands nowhere. Segment 3 drew zero shields this way.
    Falls back to the nearest in-bounds vertex.
    """
    run = [0.0]
    for i in range(1, len(pl)):
        run.append(run[-1] + math.dist(pl[i-1], pl[i]))
    tgt = run[-1] * frac
    i = min(range(len(run)), key=lambda j: abs(run[j] - tgt))
    if inbounds(pl[i]):
        return pl[i]
    cand = [p for p in pl if inbounds(p)]
    if not cand:
        return None
    return min(cand, key=lambda p: abs(p[1] - pl[i][1]))

if longest and len(longest) > 2:
    for frac in (0.30, 0.62):
        p = at_fraction(longest, frac)
        if p:
            a(shield(p[0], p[1], PRIMARY))

# ---- layer 6: towns -------------------------------------------------
for nm, la, lo, endpoint in TOWNS:
    x, y = P(la, lo)
    r = 4.2 if endpoint else 2.4
    a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#ffffff" '
      f'stroke="{INK}" stroke-width="1.2"/>')
    a(f'<text x="{x:.1f}" y="{y-r-3:.1f}" text-anchor="middle" '
      f'font-size="{9 if endpoint else 7}" '
      f'font-weight="{"bold" if endpoint else "normal"}" fill="{INK}" '
      f'paint-order="stroke" stroke="{LAND}" stroke-width="3.4" '
      f'stroke-linejoin="round">{esc(nm)}</text>')

# ---- layer 7: stops + labels ----------------------------------------
# Side split on the stops' own mean x, never the canvas midpoint: a
# mandatory endpoint far from the cluster drags W/2 off the data and
# stacks every label on one side.
xmid = sum(P(st[2], st[3])[0] for st in STOPS) / len(STOPS)
placed = {1: [], -1: []}
for iid, nm, la, lo, cat in sorted(STOPS, key=lambda t: -t[2]):   # N -> S
    col = CAT_COL[cat]
    x, y = P(la, lo)
    side = 1 if x < xmid else -1
    ly = y
    for py in placed[side]:
        if abs(ly - py) < 15:
            ly = py + 15
    placed[side].append(ly)
    lx = x + side * 34
    a(f'<path d="M {x:.1f} {y:.1f} L {x+side*14:.1f} {ly:.1f} L {lx:.1f} {ly:.1f}" '
      f'fill="none" stroke="{col}" stroke-width="0.8" opacity="0.75"/>')
    a(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{col}" '
      f'stroke="#ffffff" stroke-width="1.6"/>')
    anch = "start" if side == 1 else "end"
    tx = lx + side * 2
    a(f'<text x="{tx:.1f}" y="{ly-1:.1f}" text-anchor="{anch}" '
      f'font-family="monospace" font-size="7.5" font-weight="bold" fill="{col}" '
      f'paint-order="stroke" stroke="{LAND}" stroke-width="3.4" '
      f'stroke-linejoin="round">{esc(iid)}</text>')
    a(f'<text x="{tx:.1f}" y="{ly+7.5:.1f}" text-anchor="{anch}" '
      f'font-family="Georgia,serif" font-size="8.5" fill="{INK}" '
      f'paint-order="stroke" stroke="{LAND}" stroke-width="3.4" '
      f'stroke-linejoin="round">{esc(nm)}</text>')

a('</g>')   # end clip

# ---- furniture ------------------------------------------------------
a(f'<rect x="{FR}" y="{FR}" width="{W-2*FR:.1f}" height="{H-2*FR:.1f}" '
  f'fill="none" stroke="{INK}" stroke-width="1"/>')

# title block, top-left
tx, ty = FR + 12, FR + 22
a(f'<text x="{tx}" y="{ty}" font-size="7" letter-spacing="2.4" fill="{MUTED}" '
  f'paint-order="stroke" stroke="{LAND}" stroke-width="3.4">SEGMENT {SEG}</text>')
a(f'<text x="{tx}" y="{ty+18:.1f}" font-family="Georgia,serif" font-size="14.5" '
  f'font-weight="bold" fill="{INK}" paint-order="stroke" stroke="{LAND}" '
  f'stroke-width="3.4">{esc(SEG_TITLE)}</text>')
a(f'<text x="{tx}" y="{ty+31:.1f}" font-family="monospace" font-size="7.5" '
  f'fill="{MUTED}" paint-order="stroke" stroke="{LAND}" '
  f'stroke-width="3.4">{esc(SEG_META)}</text>')

# legend, bottom-left
lx0, ly0 = FR + 12, H - FR - 76
a(f'<rect x="{lx0-7:.1f}" y="{ly0-12:.1f}" width="128" height="82" rx="3" '
  f'fill="#ffffffdd" stroke="{GRAT}" stroke-width="0.8"/>')
yy = ly0
for cat, col in CAT_COL.items():
    a(f'<circle cx="{lx0+4:.1f}" cy="{yy-3:.1f}" r="4" fill="{col}" '
      f'stroke="#ffffff" stroke-width="1.2"/>')
    a(f'<text x="{lx0+14:.1f}" y="{yy:.1f}" font-size="7.5" fill="{INK}">{esc(cat)}</text>')
    yy += 12
a(f'<line x1="{lx0}" y1="{yy-3:.1f}" x2="{lx0+9:.1f}" y2="{yy-3:.1f}" '
  f'stroke="{ROAD1}" stroke-width="2.9"/>')
a(f'<text x="{lx0+14:.1f}" y="{yy:.1f}" font-size="7.5" fill="{INK}">Hwy {esc(PRIMARY)}</text>')
yy += 12
a(f'<line x1="{lx0}" y1="{yy-3:.1f}" x2="{lx0+9:.1f}" y2="{yy-3:.1f}" '
  f'stroke="{ROAD2}" stroke-width="1.5" stroke-dasharray="4,2"/>')
a(f'<text x="{lx0+14:.1f}" y="{yy:.1f}" font-size="7.5" fill="{INK}">Other highway</text>')
yy += 12
a(f'<rect x="{lx0-1:.1f}" y="{yy-7:.1f}" width="11" height="8" fill="{WATER_F}" '
  f'stroke="{WATER_S}" stroke-width="0.6"/>')
a(f'<text x="{lx0+14:.1f}" y="{yy:.1f}" font-size="7.5" fill="{INK}">Water</text>')

# scale bar, bottom-right -- derived from the projection, never guessed
seg_px = 25.0 / 111.0 * s
sx0, sy0 = W - FR - 24 - seg_px * 2, H - FR - 26
a(f'<rect x="{sx0:.1f}" y="{sy0:.1f}" width="{seg_px:.1f}" height="4" '
  f'fill="{INK}" stroke="{INK}" stroke-width="0.6"/>')
a(f'<rect x="{sx0+seg_px:.1f}" y="{sy0:.1f}" width="{seg_px:.1f}" height="4" '
  f'fill="#ffffff" stroke="{INK}" stroke-width="0.6"/>')
for i, lab in enumerate(("0", "25", "50")):
    a(f'<text x="{sx0+seg_px*i:.1f}" y="{sy0-3:.1f}" text-anchor="middle" '
      f'font-family="monospace" font-size="6" fill="{INK}">{lab}</text>')
a(f'<text x="{sx0+seg_px:.1f}" y="{sy0+12:.1f}" text-anchor="middle" '
  f'font-family="monospace" font-size="6" fill="{MUTED}">km</text>')

# north arrow, top-right
nx, ny = W - FR - 20, FR + 20
a(f'<path d="M {nx} {ny-11} L {nx+5} {ny+5} L {nx} {ny+1} L {nx-5} {ny+5} Z" '
  f'fill="{INK}"/>')
a(f'<text x="{nx}" y="{ny+15}" text-anchor="middle" font-size="7" '
  f'font-weight="bold" fill="{INK}">N</text>')

# attribution
a(f'<text x="{W-FR-4:.1f}" y="{H-FR-4:.1f}" text-anchor="end" font-size="6.5" '
  f'fill="{MUTED}">Coastline, lakes &amp; roads: Natural Earth 10m '
  f'\u00b7 stops from Route Stops GPS</text>')

a('</svg>')
out = "".join(o)

ET.fromstring(out)                      # must parse before upload
open(f"segment{SEG}-map.svg", "w").write(out)
print(SEG, "portrait" if PORTRAIT else "landscape", len(out))
