# Tomorrow: scroll transitions

**Starting point:** `site/index.html` renders the static Sankey with an A ↔ B toggle that already morphs.

- Five placeholder steps are wired to scrollama. `onStepEnter` sets `state.step` and `#chart[data-step]` and does nothing else yet.
- Data is final: `site/sankey.json` (both views) and `site/accidents.json` (per-accident records for drill-downs).
- Run: `.venv/bin/python -m http.server 8765 --directory site`, then open http://localhost:8765
- After any data change: `.venv/bin/python scripts/build_data.py && .venv/bin/python scripts/test_build_data.py`

## Built since the first plan

- **Persistent caption header.**
  - Step text now shows in a caption above a full-width sticky chart ("Step n of 5" plus progress dots), not in a left card column.
  - `.step` elements are invisible scroll triggers. Each holds its caption in a `<p class="sr-only">`, which `setCaption()` copies into the header.
  - Edit captions there.
- **Outcome colors.** Fatal is wine, Serious burnt orange, Minor amber, No injury stone. Flows from the middle column blend from discipline color into outcome color: one SVG gradient per (discipline, outcome) pair, which works because columns never move.
- **Report viewer pane.**
  - Clicking any bar, label or flow opens a right-side pane prefiltered to that selection. Filters show as removable chips.
  - Keyword search: all words must match, "quoted phrases" count as one term, case-insensitive. It searches title, factor tags and full report text (`reports.json`, ~7MB, loaded lazily on first open).
  - Each list item shows year, outcome pill, discipline dots, a title that expands to the full report, a text snippet when the match is in the body, and factor badges (environment factors tinted).
  - Esc closes it.
  - The pane lists every report carrying a tag; the chart counts multi-discipline reports fractionally, so a pane count can exceed the chart number. The footer explains this.
- **Before publishing:** `reports.json` holds the AAC narrative text. It's in the source repo already, but it's the heaviest asset (7MB uncompressed). Consider gzip on the host, or search titles/tags only for a lighter build.

- **Top-level Sankey / Intake tabs** (top left; `#sankey` / `#intake` in the URL).
- **Intake view: "read what happened on similar trips".**
  - **Form fields:**
    - style (required)
    - experience: <1 / 1–3 / 3+ yrs, the dataset's own scale
    - time since last climbed
    - state/province + area text
    - new to style/area
    - trip date (month ±1) + time of day
    - party size + party experience
  - **Matching** happens in the browser (`criteria()` / `match()` in index.html). Each answered field is a criterion that returns match, mismatch, or "report can't tell".
    - Thin-data fields can only add matches, never exclude a report: layoff, new style/area and area text are text cues found in only ~30–40 reports each.
    - "How close" toggle: Every detail (no mismatches) / All but one (≤1 mismatch, default) / Style only.
  - **Heatmap:** the top 12 factors among the matches (rows) × worst outcome (columns), cell shade by count. A "vs all <style>" column shows how much more common each factor is in the matches than in all reports of that style.
  - **Clicks:** any cell or factor opens the report pane on just those reports, ranked by closeness.
  - **Coverage list** under the heatmap: how many reports of the style can actually be judged on each detail (e.g. time of day is known for only 84 of 898 trad reports).
  - **Caveat on the page:** reported accidents, not risk. There is no count of trips that went fine.
  - **Known limits:**
    - Party size is approximated by how many climbers' ages a report gives.
    - Experience tags describe someone in the accident, so "your experience" and "party experience" match the same tags.
    - "All but one" can drop the location match. That's intended, but a reader who picked California may be surprised to see Alaska reports.

## Architecture to adopt first (before any step)

Make each step a **declarative state**, not a sequence of commands:

```js
const STEPS = [
  { view: "B", stages: [0],       highlight: null },
  { view: "B", stages: [0, 1],    highlight: null },
  { view: "B", stages: [0, 1, 2], highlight: { mid: "mB:unroped" } },
  { view: "B", stages: [0, 1, 2], highlight: { discipline: ["trad", "mountaineering"] } },
  { view: "A", stages: [0, 1, 2], highlight: null, toggle: true },
];
```

`onStepEnter` then calls `render(STEPS[i])`, and `render` diffs against what's on screen. Scrolling backwards, skipping steps or jumping mid-page all land in the right state.

- Every transition calls `selection.interrupt()` first.
- The toggle buttons stay hidden until step 5, then unlock.

## The five steps

| # | Chart shows | Highlights | Caption (draft) | Technique |
|---|---|---|---|---|
| 1 | Discipline column only; middle and outcome nodes and all links at opacity 0 | none | Mountaineering and trad account for nearly three in four reported accidents. | **Re-stage**: reveal one column |
| 2 | + middle column (view B, what they were doing); discipline → middle links grow from width 0 | none | Most accidents happen climbing up on a rope, but 865 happen on the way down. | **Re-stage**: links grow left to right (stroke-width tween, or stroke-dashoffset draw-on) |
| 3 | + outcome column, full chart | Unroped / solo ascent node and its flows; everything else fades to ~0.15 | Climbing unroped: 366 accidents, 39% of them fatal, more than three times the rate on a rope (11%). | **Highlight / fade** (opacity only, no geometry change) |
| 4 | Full chart | Trad and Mountaineering bands end to end; others faded | Trad accidents are mostly roped falls. Mountaineering accidents end in death twice as often (25% vs 12%). | **Highlight / fade** by `link.discipline` |
| 5 | Middle column morphs to view A (what contributed); toggle unlocks | none, then free exploration | More than 4 in 5 reports involve human error, but accidents with only environmental causes are the deadliest (29% fatal). | **Filter-and-reflow**: middle nodes keyed by slot, links by discipline\|slot\|outcome (already built) |

Verify every caption number against `data/clean/accidents.csv` before publishing. Steps 3 and 4 use worst outcome; discipline shares use 1/n weights.

### Optional juncture: size-scaled accidents (decide whether it's viable)

After step 3, the Unroped / solo node could burst into one dot per accident (366), sized by `party_size`.

- **Viability concern, to check first:** `party_size` is the count of climbers whose age is reported.
  - Of the 2,724 climbing accidents, it's present for 1,894 (70%).
  - Of those, 1,165 are 1 and 547 are 2. Only 62 are 4+, and ID `166` is 25.
  - So most dots would be the same size, and 30% have no size at all.
- **Quick test:** render the 366 dots with `d3.forceSimulation` (forceX/forceY to a cluster, forceCollide by radius) and see whether size says anything.
- **Fallback:** uniform dots colored by worst outcome (a unit chart). "Each dot is one accident" lands without size.
- Accidents with no party size would need a hollow dot, not a default size, so the chart doesn't overstate certainty.

## Risks

1. **Scroll sync.**
   - Fast scrolling fires several `onStepEnter`s mid-transition. Use the declarative state + `interrupt()` above.
   - Use scrollama `offset: 0.6` (current). Test trackpad flicks and the keyboard End key.
   - Call `scroller.resize()` after fonts load and on resize (resize is already wired).
2. **Node reflow jank.**
   - Columns already don't move between views: `iterations(0)`, `nodeSort(null)`, fixed input order.
   - Only middle-node heights change, so link paths interpolate cleanly.
   - Links missing in one view (e.g. Sport → Unclear) enter and exit at width 0. Watch for a flash of thin 0.5px strokes and drop the `Math.max(0.5, …)` floor during transitions if it shows.
   - Re-staging (step 1 → 2) must change opacity/width only, never re-run the layout with fewer nodes. Removing nodes rescales `ky` and everything jumps.
3. **Mobile layout (partly fixed).**
   - Below 560px, labels sit inside the plot: discipline labels right of their bars, outcome labels left of theirs, and middle labels drop their counts.
   - The chart fits 375px with no horizontal scroll.
   - Remaining collisions:
     - "No factor tagged" vs "No injury reported" at the bottom
     - the middle and outcome column headers touching
   - Options: stagger the bottom labels, abbreviate headers on phones, or a vertical Sankey (skip unless needed).
4. **Middle-label legibility.** Middle node labels sit on top of bands. The 4px halo helps but crowded bands still compete. Consider a background pill or placing labels in the gap above each node.
5. **Gray dominance.** Mountaineering (42% of weight) is gray, so the chart reads as mostly gray until a highlight step. That's intentional (it's the data), but step 1's caption should own it.
6. **Fractional counts.** Labels show "160.7". Captions should use integer accident counts ("223 accidents involve ice") and explain the weighting in the footer, which already does.
7. **Accessibility.** Add a data table (or `<details>` with link values) as the non-visual fallback. Tooltips are mouse-only today; add focusable nodes or rely on the table.
