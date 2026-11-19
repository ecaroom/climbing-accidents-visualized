# Climbing accidents scrollytelling

DRAFT: written by Claude from the project brief because the intended CLAUDE.md contents were missing. Replace freely.

Vertical-scroll data story (NYT-style) built on Eliot Caroom's 2020 dataset of ~2,770 AAC accident reports (pub years 1990–2019).

## Rules
- `source/` is a clone of https://github.com/ecaroom/climbing-accidents. **Never modify anything in it.** Every derived file must be reproducible from it by script.
- Exclude the 46 rows tagged `Non-climbing` from the story (2,724 climbing accidents).
- Attribution (footer, exact): "Data: an analysis of the AAC's climbing accident reports by Eliot Caroom (CC BY 4.0)" linking to the repo. This is **not an AAC project**; never imply AAC authorship or use AAC branding.
- Site: plain HTML + D3 v7 + d3-sankey + scrollama from CDN. No build step, no framework.
- Python data work uses the local venv: `.venv/bin/python` (pandas, openpyxl, python-docx).

## Layout
- `source/`: upstream repo, read-only
- `data/raw/`: verbatim CSV export of every sheet (+ `__formulas.csv` sidecars) and `methodology.md`
- `data/PROFILE.md`: profile of the raw data and data-quality gotchas. Read before changing cleaning logic.
- `data/clean/`: tidy outputs (`accidents.csv`)
- `scripts/`: `export_raw.py` → `profile_raw.py` → `build_data.py` (+ tests)
- `site/`: `index.html`, `sankey.json`

## Data facts that bite
- Tags are wide one-column-per-tag flags; accidents carry multiple disciplines, factors and outcomes. There is no primary-factor field.
- Age columns are headcounts, not flags. Month columns mix `1` and `Y`.
- The `data` sheet's `Tags Applied` text column abbreviates `Aid & Big Wall Climbing`; treat the flag columns as the source of truth.

## Commands
- Rebuild raw: `.venv/bin/python scripts/export_raw.py && .venv/bin/python scripts/profile_raw.py`
- Build + test: `.venv/bin/python scripts/build_data.py && .venv/bin/python scripts/test_build_data.py`
- Serve: `.venv/bin/python -m http.server 8765 --directory site` → http://localhost:8765
- Sankey rules (approved): discipline 1/n weighting; view A = factor mix, view B = activity at time of accident; outcome = worst outcome. See `data/SANKEY_PROPOSALS.md` and `PLAN.md`.
