# Climbing Accidents Visualized

An interactive look at 2,724 climbing accident reports published by the American Alpine Club, publication years 1990 to 2019.

**Live:** https://eliotcaroom.com/climbing-accidents/

- **Sankey:** every accident flows from discipline to either what contributed (human or environmental factors) or what the climbers were doing, then to the worst outcome. Click any bar or flow to read the reports behind it.
- **Intake:** describe a planned trip (style, experience, location, date, time of day, party) and get the reported accidents most like it. A heatmap shows which factors were tagged in them and how they ended.
- **Search:** keyword search across all report text, titles and tags.

These are reported accidents, not risk rates. The AAC publishes a selection of incidents and there is no count of trips that went fine.

## Data

Built from [ecaroom/climbing-accidents](https://github.com/ecaroom/climbing-accidents): an analysis of the AAC's climbing accident reports by Eliot Caroom (CC BY 4.0). That dataset tags each report by discipline, experience, outcome and 48 contributing factors; see its methodology and category definitions. This is not an AAC project.

Rules used here (details in `data/SANKEY_PROPOSALS.md`):
- The 46 non-climbing incidents are excluded.
- Reports tagged with more than one discipline count fractionally toward each in the Sankey (an Ice + Mountaineering report adds ½ to each).
- Outcome is the most severe outcome in the report.

## Layout

| Path | What |
|---|---|
| `site/` | The app: plain HTML + D3 v7 + d3-sankey from a CDN, no build step. `sankey.json`, `accidents.json`, `reports.json` are generated. |
| `scripts/export_raw.py` | Source workbooks to `data/raw/` CSVs (not committed; regenerate) |
| `scripts/profile_raw.py` | Writes `data/PROFILE.md` |
| `scripts/build_data.py` | Source workbook to `data/clean/` and `site/*.json` |
| `scripts/test_build_data.py` | Row-count and Sankey reconciliation checks |
| `scripts/publish_to_site.py` | Copies `site/` into the eliotcaroom.com repo as a standalone page |
| `PLAN.md` | Design notes and the (currently disabled) scroll-story plan |

## Rebuild

```bash
git clone https://github.com/ecaroom/climbing-accidents source
python3 -m venv .venv && .venv/bin/pip install pandas openpyxl python-docx
.venv/bin/python scripts/build_data.py && .venv/bin/python scripts/test_build_data.py
.venv/bin/python -m http.server 8765 --directory site   # http://localhost:8765
```
