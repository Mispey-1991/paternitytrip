"""Route-line segment SVG generator.

Emits a self-contained SVG. Stdlib only.
Set the per-segment inputs below, then run. Nothing else is
segment-specific.
"""
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

CATS = [("Points of Interest", "#2f9e44"),
        ("Hikes",              "#e8590c"),
        ("Places to Stay",     "#9c36b5"),
        ("Food & Drink",       "#e03131")]

# ---- per-segment inputs (from the Route Stops query) ----------------
SEG       = 3
SEG_TITLE = "Sault Ste. Marie → Wawa"
STOPS     = [  # (item_id, category, lat, lon)
    ("I3-01", "Points of Interest", 46.9280, -84.4258),
    ("H3-02", "Hikes",              47.7167, -84.8500),
]
ENDPOINTS = ((46.5136, -84.3358), (47.9899, -84.7731))   # start, end

# ---- canvas --------------------------------------------------------
W, H   = 900, 340
X0, X1 = 170, 870          # line span; X0 clears the widest label
YS     = [90, 155, 220, 285]

# ---- choose the interpolation axis ---------------------------------
# Span every point, stops included -- not just the two endpoints.
(alat, alon), (blat, blon) = ENDPOINTS
lats = [s[2] for s in STOPS] + [alat, blat]
lons = [s[3] for s in STOPS] + [alon, blon]
use_lon = (max(lons) - min(lons)) >= (max(lats) - min(lats))
vals   = lons if use_lon else lats
lo, hi = min(vals), max(vals)
# keep direction of travel: start town stays at the left edge
forward = (blon >= alon) if use_lon else (blat >= alat)
a, b = (lo, hi) if forward else (hi, lo)

def frac(lat, lon):
    v = lon if use_lon else lat
    return 0.0 if b == a else max(0.0, min(1.0, (v - a) / (b - a)))

# ---- draw ----------------------------------------------------------
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#ffffff"/>'
       f'<text x="{X0}" y="42" font-family="Georgia,serif" font-size="17" '
       f'font-weight="bold" fill="#222">Segment {SEG}: {escape(SEG_TITLE)}</text>']

for (cat, col), y in zip(CATS, YS):
    rows = [s for s in STOPS if s[1] == cat]
    svg.append(f'<text x="{X0-15}" y="{y+4}" text-anchor="end" '
               f'font-family="Helvetica,Arial,sans-serif" font-size="11.5" '
               f'font-weight="bold" fill="{col}">{escape(cat)}</text>')
    dash = '' if rows else ' stroke-dasharray="6,4"'
    svg.append(f'<line x1="{X0}" y1="{y}" x2="{X1}" y2="{y}" '
               f'stroke="{col}" stroke-width="2.4"{dash}/>')

    if not rows:
        svg.append(f'<text x="{(X0+X1)//2}" y="{y-9}" text-anchor="middle" '
                   f'font-family="Georgia,serif" font-size="10" font-style="italic" '
                   f'fill="#8a8a8a">(none logged in Route Stops yet)</text>')
        continue

    placed, above = [], True
    for iid, _c, lat, lon in sorted(rows, key=lambda r: frac(r[2], r[3])):
        x = X0 + frac(lat, lon) * (X1 - X0)
        if placed and x - placed[-1] < 46:      # would collide -> alternate
            above = not above
        else:
            above = True
        placed.append(x)
        ly = y - 12 if above else y + 20
        svg.append(f'<circle cx="{x:.1f}" cy="{y}" r="4" fill="{col}" '
                   f'stroke="#ffffff" stroke-width="1.4"/>')
        svg.append(f'<text x="{x:.1f}" y="{ly}" text-anchor="middle" '
                   f'font-family="monospace" font-size="9.5" font-weight="bold" '
                   f'fill="{col}">{iid}</text>')

svg.append('</svg>')
out = "".join(svg)

ET.fromstring(out)                       # must parse before use
open(f"segment{SEG}-route-line.svg", "w").write(out)
