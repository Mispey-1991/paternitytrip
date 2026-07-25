# Northern Ontario Paternity Trip

Self-contained printable HTML packages for each segment of the trip. Click **View** to open a segment as a rendered page (via htmlpreview.github.io). Print via Ctrl+P → Save as PDF; page breaks are CSS-controlled.

---

## Printable Segment Pages

| # | Route | Status | View |
|---|-------|--------|------|
| 1a | Whitby → Tobermory | ✅ Built | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment1a-printable.html) |
| 1b | Tobermory → Little Current *(ferry)* | ✅ Built | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment1b-printable.html) |
| 2 | Little Current → Sault Ste. Marie | ✅ Built | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment2-printable.html) |
| 3 | Sault Ste. Marie → Wawa | ✅ Built | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment3-printable.html) |
| 4 | Wawa → Marathon | ✅ Built | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment4-printable.html) |
| 5 | Marathon → Thunder Bay | ✅ Built | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment5-printable.html) |
| 6 | Thunder Bay → Geraldton | ✅ Built | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment6-printable.html) |
| 7 | Geraldton → Hearst | ✅ Built | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment7-printable.html) |
| 8 | Hearst → Cochrane | ⚠️ Stale | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment8-printable.html) |
| 9 | Cochrane → Timmins | ⚠️ Stale | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment9-printable.html) |
| 10 | Timmins → New Liskeard | ✅ Built | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment10-printable.html) |
| 11 | New Liskeard → North Bay | ✅ Built | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment11-printable.html) |
| 12 | North Bay → Algonquin | ✅ Built | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment12-printable.html) |
| 13 | Algonquin → Whitby | ✅ Built | [View](https://htmlpreview.github.io/?https://github.com/Mispey-1991/paternitytrip/blob/main/printables/segment13-printable.html) |

---

## Repository Layout

```
printables/          One HTML file per segment — self-contained, SVG inline, no external deps
reference/           Generator scripts (A, B, C, D) — source of truth for all derived artifacts
```

## Generators

| Script | Purpose |
|--------|---------|
| `generator-a-route-line.py` | Route-line SVG (schematic, west→east layout) |
| `generator-b-full-page-map.py` | Full-page geographic map SVG (Natural Earth 10m) |
| `generator-c-html-assembler.py` | Assembles A + B into the printable HTML; auto-appends inset if present |
| `generator-d-inset-map.py` | Detail inset map for tight stop clusters (e.g. Tobermory peninsula) |
| `gen_b_5_fixed.py` | Segment 5 bbox override — see Build Notes in Segments DB |

Canonical instructions live in Notion (Op 7). These scripts are the transport copy.
