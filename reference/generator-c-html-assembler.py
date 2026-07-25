"""HTML printable assembler — Generator C.

Reads Generator A (route-line SVG) and Generator B (full-page map SVG) from
disk. Set per-segment inputs below, then run as a top-level script. Do NOT
wrap this in a function — Notion strips the common leading indent (TN-11).

Writes: segment{SEG}-printable.html
"""
import html as _html, json, re

E = _html.escape   # escape helper; call on every string from the DB

# ---- category config (must match Generators A and B) -------------------
CAT_ORDER = ["Points of Interest", "Hikes", "Places to Stay", "Food & Drink"]
CAT_COL   = {
    "Points of Interest": "#2f9e44",
    "Hikes":              "#e8590c",
    "Places to Stay":     "#9c36b5",
    "Food & Drink":       "#e03131",
}

# ---- advisory emoji heuristic (Op 7 spec: 📵 cell, ⛽ fuel, 🫎 wildlife, ⚠️ else)
def adv_emoji(text):
    t = text.lower()
    if any(w in t for w in ("cell", "coverage", "reception", "network", "signal")):
        return "\U0001f4f5"   # 📵
    if any(w in t for w in ("fuel", "gas", "gasoline", "petrol")):
        return "\u26fd"        # ⛽
    if any(w in t for w in ("wildlife", "moose", "bear ", "deer", "elk", "caribou")):
        return "\U0001f98c"   # 🫎
    return "\u26a0\ufe0f"     # ⚠️

# ---- per-segment inputs (from Route Stops + Segments DB queries) --------
# SEG: string identifier, e.g. "1a", "1b", "3" — used in filenames and headings
# SEG_META: highway | drive time | distance | {N} stops  (leave {N} literal;
#           it is replaced at runtime with the actual STOPS count)
# ADVISORIES_RAW: verbatim Advisories field value from Segments DB; split on \n
# STOPS: list of 9-tuples — one per active Route Stop, in Item ID order:
#   (item_id, name, category, description, address, gps_str, link, must_do, contributor)
#   contributor: JSON array string from DB, e.g. '["Mike"]', or None

SEG         = 3
SEG_TITLE   = "Sault Ste. Marie \u2192 Wawa"
SEG_META    = "Hwy 17 N | ~2.5 hrs | ~235 km | {N} stops"
SEG_INTRO   = "Placeholder intro."
ADVISORIES_RAW = ""

STOPS = [
    # (item_id, name, category, description, address, gps_str, link, must_do, contributor)
    ("I3-01", "Chippewa Falls", "Points of Interest",
     "A roadside waterfall near Sault Ste. Marie.", "Sample Rd, ON", "46.928, -84.426",
     None, False, None),
]

# ---- file I/O -----------------------------------------------------------
ROUTE_SVG_FILE = f"segment{SEG}-route-line.svg"
MAP_SVG_FILE   = f"segment{SEG}-map.svg"
OUT_FILE       = f"segment{SEG}-printable.html"

# ---- load and sanitise SVGs --------------------------------------------
def load_svg(path):
    raw = open(path, encoding="utf-8").read()
    raw = re.sub(r"<\?xml[^?]*\?>", "", raw).strip()  # strip XML declaration
    if not raw.startswith("<svg"):
        raise ValueError(f"{path}: expected <svg> start after stripping declaration")
    return raw

route_svg = load_svg(ROUTE_SVG_FILE)
map_svg   = load_svg(MAP_SVG_FILE)

# ---- derived values -----------------------------------------------------
n_stops = len(STOPS)
meta    = SEG_META.replace("{N}", str(n_stops))

advisories = [ln.strip() for ln in ADVISORIES_RAW.split("\n") if ln.strip()]

by_cat = {cat: [] for cat in CAT_ORDER}
for stop in STOPS:
    by_cat[stop[2]].append(stop)

# ---- contributor formatting --------------------------------------------
def fmt_contributor(raw):
    if not raw:
        return None
    try:
        names = json.loads(raw) if isinstance(raw, str) else raw
        if not names:
            return None
        return "Researched by " + ", ".join(names)
    except (json.JSONDecodeError, TypeError):
        return None

# ---- HTML assembly ------------------------------------------------------
parts = []
p = parts.append

p(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Segment {E(str(SEG))}: {E(SEG_TITLE)} \u2014 Northern Ontario Paternity Trip</title>
<style>
@page {{ size: letter portrait; margin: 16mm 14mm 14mm 14mm; }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ font-family: Georgia, serif; font-size: 10.5pt; color:#222; margin:0; }}
.eyebrow {{ font-family: Helvetica, Arial, sans-serif; font-size:9pt; letter-spacing:2.4px; color:#666; text-transform:uppercase; }}
h1 {{ font-family: Georgia, serif; font-size: 22pt; margin: 4px 0 6px 0; }}
.metarule {{ font-family: monospace; font-size: 9.5pt; color:#444; margin-bottom:10px; }}
.lede {{ font-size:11pt; line-height:1.5; max-width:74ch; margin-bottom:14px; }}
.advisory {{ border:1px solid #cfc9bd; border-left:4px solid #4a4741; background:#fbfaf8;
  padding:6px 10px; margin:6px 0; font-family: Helvetica, Arial, sans-serif;
  font-size:9pt; line-height:1.4; max-width:82ch;
  page-break-inside: avoid; break-inside: avoid; }}
figure.route {{ margin: 14px 0; page-break-inside: avoid; break-inside: avoid; }}
figure.route svg.fig {{ width:100%; height:auto; max-width: 940px; }}
figcaption {{ font-family: Helvetica, Arial, sans-serif; font-size:8pt; color:#777;
  text-align:center; margin-top:2px; }}
.category h2 {{ font-family: Helvetica, Arial, sans-serif; font-size:13pt; border-bottom:2px solid;
  padding-bottom:3px; margin-top:18px; margin-bottom:6px;
  page-break-after: avoid; break-after: avoid; }}
.emptycat {{ font-style:italic; color:#8a8a8a; font-size:10pt; }}
.stop {{ display:grid; grid-template-columns: 17mm 1fr; gap:8px; padding:6px 0;
  border-bottom:1px solid #eee; page-break-inside: avoid; break-inside: avoid; }}
.idgutter {{ font-family: monospace; font-weight:bold; white-space:nowrap;
  font-size:10pt; padding-top:2px; }}
.stopname {{ font-size:12pt; font-weight:bold; margin-bottom:2px; }}
.stopdesc {{ max-width:68ch; line-height:1.45; margin-bottom:3px; }}
.ulabel {{ font-family: Helvetica, Arial, sans-serif; font-size:7pt; letter-spacing:1px; color:#888; }}
.addrline, .gpsline, .linkline {{ font-family: Helvetica, Arial, sans-serif; font-size:8.5pt; color:#444; }}
.gpsline {{ font-family: monospace; font-size:8.5pt; }}
.contrib {{ font-style:italic; font-size:8.5pt; color:#666; margin-top:2px; }}
.legend {{ margin-top:20px; padding-top:10px; border-top:1px solid #ccc;
  font-family: Helvetica, Arial, sans-serif; font-size:9pt;
  page-break-inside: avoid; break-inside: avoid; }}
.legswatch {{ display:inline-block; width:10px; height:10px; border-radius:50%;
  margin:0 4px 0 14px; vertical-align:middle; }}
.legswatch:first-child {{ margin-left:0; }}
.colophon {{ font-family: monospace; font-size:8pt; color:#888; margin-top:8px; }}
.mappage {{ page-break-before: always; break-before: page; }}
.mappage svg.fullmap {{ width:100%; height:auto; max-width: 190mm; margin:0 auto; display:block; }}
@media screen and (max-width: 640px) {{
  .stop {{ grid-template-columns: 1fr; }}
  .idgutter {{ padding-top:0; }}
}}
</style>
</head>
<body>
""")

# ---- masthead -----------------------------------------------------------
p(f'<div class="eyebrow">Northern Ontario Paternity Trip \u00b7 Segment {E(str(SEG))} of 13</div>\n')
p(f'<h1>{E(SEG_TITLE)}</h1>\n')
p(f'<div class="metarule">{E(meta)}</div>\n')
p(f'<div class="lede">{E(SEG_INTRO)}</div>\n')
for adv in advisories:
    p(f'<div class="advisory">{adv_emoji(adv)} {E(adv)}</div>\n')

# ---- route line ---------------------------------------------------------
p('<figure class="route">\n')
p(route_svg.replace("<svg", '<svg class="fig" preserveAspectRatio="xMidYMid meet"', 1))
p('\n<figcaption>Route line view \u2014 stops positioned west to east</figcaption>\n')
p('</figure>\n')

# ---- stop sections ------------------------------------------------------
for cat in CAT_ORDER:
    col = CAT_COL[cat]
    stops = by_cat[cat]
    p(f'<div class="category">\n')
    p(f'<h2 style="color:{col};border-color:{col}">{E(cat)}</h2>\n')
    if not stops:
        p(f'<p class="emptycat"><em>No {cat.lower()} stops on this segment.</em></p>\n')
    for (iid, name, _cat, desc, addr, gps, link, must_do, contrib) in stops:
        display_name = ("\u2605 " if must_do else "") + name
        contrib_text = fmt_contributor(contrib)
        p('<div class="stop">\n')
        p(f'  <div class="idgutter" style="color:{col}">{E(iid)}</div>\n')
        p('  <div class="stopbody">\n')
        p(f'    <div class="stopname">{E(display_name)}</div>\n')
        if desc:
            p(f'<div class="stopdesc">{E(desc)}</div>\n')
        if addr:
            p(f'    <div class="addrline">\n<span class="ulabel">ADDR</span> {E(addr)}</div>\n')
        if gps:
            p(f'    <div class="gpsline">\n<span class="ulabel">GPS</span> {E(gps)}</div>\n')
        if link:
            p(f'    <div class="linkline">\n<span class="ulabel">LINK</span> {E(link)}</div>\n')
        if contrib_text:
            p(f'    <div class="contrib">{E(contrib_text)}</div>\n')
        p('  </div>\n')
        p('</div>\n')
    p('</div>\n')

# ---- legend + colophon --------------------------------------------------
p('<div class="legend">\n')
for cat, col in CAT_COL.items():
    p(f'<span class="legswatch" style="background:{col}"></span> {E(cat)}\n')
p('<br><small>\u2605\u2005=\u2005Must do</small>')
p(f'<div class="colophon">Northern Ontario Paternity Trip \u00b7 Segment {E(str(SEG))} '
  f'\u00b7 {n_stops} stops \u00b7 Built from Route Stops DB</div>\n')
p('</div>\n')

# ---- full-page map ------------------------------------------------------
p('<div class="mappage">\n')
p(map_svg.replace("<svg", '<svg class="fullmap"', 1))
p('\n</div>\n')

p('</body>\n</html>')

# ---- write and verify ---------------------------------------------------
import xml.etree.ElementTree as ET

out = "".join(parts)

assert 'src="' not in out,           "FAIL: external src= reference found"
assert out.count('<svg') == 2,        f"FAIL: expected 2 <svg> elements, got {out.count('<svg')}"
assert '<?xml' not in out,            "FAIL: <?xml declaration present"

# map page is last svg, preceded by mappage div
last_svg_pos = out.rfind('<svg')
mappage_pos  = out.rfind('class="mappage"')
assert mappage_pos < last_svg_pos,    "FAIL: last <svg> not inside mappage div"
after_last   = out[last_svg_pos + out[last_svg_pos:].index('</svg>') + 6:]
assert after_last.strip().replace('\n','').replace(' ','') in ('</div></body></html>', '</div>\n</body>\n</html>') or \
       all(c in ' \n<>/divbodyhtml' for c in after_last), \
       "FAIL: content after final </svg>"

stop_count_in_meta = re.search(r'(\d+)\s+stops', meta)
if stop_count_in_meta:
    assert int(stop_count_in_meta.group(1)) == n_stops, \
        f"FAIL: meta says {stop_count_in_meta.group(1)} stops but STOPS has {n_stops}"

ET.fromstring(route_svg)   # must parse independently
ET.fromstring(map_svg)     # must parse independently

open(OUT_FILE, "w", encoding="utf-8").write(out)
print(f"OK: segment{SEG}-printable.html  |  {n_stops} stops  |  {len(out):,} bytes")
