"""Full-page segment map generator — Segment 5, bbox from STOPS only.

Marathon falls off-frame; Thunder Bay anchors the western end.
Route: Marathon → Thunder Bay  (Highway 17 / 11/17)
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

SEG         = 5
SEG_TITLE   = "Marathon \u2192 Thunder Bay"
SEG_META    = "Hwy 17 / Hwy 11/17 \u00b7 ~330 km \u00b7 ~3.5 hrs"
PRIMARY     = "17"

STOPS = [
    ("I5-01", "Eagle Canyon Suspension Bridge", 48.794711, -88.613712, "Points of Interest"),
    ("I5-02", "Mount McKay & Hillcrest Park",   48.345278, -89.285556, "Points of Interest"),
    ("I5-03", "Nipigon River Bridge",            49.019772, -88.250667, "Points of Interest"),
    ("I5-04", "Ouimet Canyon",                   48.789514, -88.671295, "Points of Interest"),
    ("I5-05", "Terry Fox Memorial & Lookout",    48.484970, -89.167923, "Points of Interest"),
    ("P5-01", "Kakabeka Falls",                  48.403257, -89.623953, "Places to Stay"),
    ("P5-02", "Rainbow Falls Provincial Park",   48.843837, -87.395938, "Places to Stay"),
    ("P5-03", "Sleeping Giant Provincial Park",  48.369305, -88.804575, "Places to Stay"),
]

# TOWNS for rendering only (not bbox) — Marathon is off-frame for this segment;
# show Thunder Bay only. The title block carries both endpoints.
TOWNS = [
    ("Thunder Bay", 48.3994, -89.2477, True),
]

# ---- bbox from STOPS only (not towns) --------------------------------
# Marathon at -86.38°W would expand the map so far east that all stops
# compress into the left 25% and the aspect-ratio latitude expansion
# pushes lat0 below 48°N into Lake Superior. Using stops-only bbox keeps
# all dots spread across the canvas and the bottom edge solidly in Ontario.
lats = [s[2] for s in STOPS]
lons = [s[3] for s in STOPS]
lat0, lat1 = min(lats) - 0.15, max(lats) + 0.15
lon0, lon1 = min(lons) - 0.20, max(lons) + 0.20
k = math.cos(math.radians((lat0 + lat1) / 2))

PORTRAIT = (lat1 - lat0) > (lon1 - lon0) * k
PW, PH = (190.0, 251.0) if PORTRAIT else (251.0, 190.0)
SC = 3.7795
W, H = PW * SC, PH * SC
FR = 6.0

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

BB = (lon0 - 0.4, lat0 - 0.4, lon1 + 0.4, lat1 + 0.4)

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
        if prev is None or abs(x - prev[0]) > 0.35 or abs(y - prev[1]) > 0.35:
            out.append(f"{x:.1f} {y:.1f}"); prev = (x, y)
    if len(out) < 2:
        return None
    return "M " + " L ".join(out) + (" Z" if close else "")

o = []
a = o.append

a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.1f}" height="{H:.1f}" '
  f'viewBox="0 0 {W:.1f} {H:.1f}" font-family="Helvetica,Arial,sans-serif">')
a(f'<defs><clipPath id="fr"><rect x="{FR}" y="{FR}" '
  f'width="{W-2*FR:.1f}" height="{H-2*FR:.1f}"/></clipPath></defs>')
a(f'<rect width="{W:.1f}" height="{H:.1f}" fill="{PAPER}"/>')
a(f'<rect x="{FR}" y="{FR}" width="{W-2*FR:.1f}" height="{H-2*FR:.1f}" fill="{LAND}"/>')
a('<g clip-path="url(#fr)">')

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

# Marathon: off-frame — draw edge indicator at right margin
mx, my = P(48.7167, -86.3785)
mx_clamped = W - FR - 2
a(f'<path d="M {mx_clamped-10} {my-6} L {mx_clamped} {my} L {mx_clamped-10} {my+6}" '
  f'fill="none" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round"/>')
a(f'<text x="{mx_clamped-13}" y="{my-9}" text-anchor="end" font-size="7" '
  f'font-weight="bold" fill="{INK}">Marathon</text>')
a(f'<text x="{mx_clamped-13}" y="{my+16}" text-anchor="end" font-size="6" '
  f'fill="{MUTED}">(segment start, 170 km \u2192)</text>')

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

xmid = sum(P(st[2], st[3])[0] for st in STOPS) / len(STOPS)
placed = {1: [], -1: []}
for iid, nm, la, lo, cat in sorted(STOPS, key=lambda t: -t[2]):
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

a('</g>')

a(f'<rect x="{FR}" y="{FR}" width="{W-2*FR:.1f}" height="{H-2*FR:.1f}" '
  f'fill="none" stroke="{INK}" stroke-width="1"/>')

tx, ty = FR + 12, FR + 22
a(f'<text x="{tx}" y="{ty}" font-size="7" letter-spacing="2.4" fill="{MUTED}" '
  f'paint-order="stroke" stroke="{LAND}" stroke-width="3.4">SEGMENT {SEG}</text>')
a(f'<text x="{tx}" y="{ty+18:.1f}" font-family="Georgia,serif" font-size="14.5" '
  f'font-weight="bold" fill="{INK}" paint-order="stroke" stroke="{LAND}" '
  f'stroke-width="3.4">{esc(SEG_TITLE)}</text>')
a(f'<text x="{tx}" y="{ty+31:.1f}" font-family="monospace" font-size="7.5" '
  f'fill="{MUTED}" paint-order="stroke" stroke="{LAND}" '
  f'stroke-width="3.4">{esc(SEG_META)}</text>')

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

nx, ny = W - FR - 20, FR + 20
a(f'<path d="M {nx} {ny-11} L {nx+5} {ny+5} L {nx} {ny+1} L {nx-5} {ny+5} Z" '
  f'fill="{INK}"/>')
a(f'<text x="{nx}" y="{ny+15}" text-anchor="middle" font-size="7" '
  f'font-weight="bold" fill="{INK}">N</text>')

a(f'<text x="{W-FR-4:.1f}" y="{H-FR-4:.1f}" text-anchor="end" font-size="6.5" '
  f'fill="{MUTED}">Coastline, lakes &amp; roads: Natural Earth 10m '
  f'\u00b7 stops from Route Stops GPS</text>')

a('</svg>')
out = "".join(o)
ET.fromstring(out)
open("segment5-map.svg", "w").write(out)
print(5, "portrait" if PORTRAIT else "landscape", len(out))
