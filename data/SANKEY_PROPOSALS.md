# Sankey proposals (Step 3): awaiting approval

All counts are climbing-only (n = 2,724, `Non-climbing` excluded), computed by `scripts/sankey_candidates.py` from `data/raw/`. **There is no primary-factor field, and none of these designs invents one.** The methodology treats every tag as a contributing factor.

## Shared stages

### Stage 1: Discipline (7 nodes)

| node | accidents with tag | weighted (1/n) | fatal share |
|---|---|---|---|
| Mountaineering (`Alpine/Mountaineering`) | 1,245 | 1,140.7 | 25% |
| Trad | 898 | 845.5 | 12% |
| Ice | 223 | 160.7 | 23% |
| Sport | 173 | 168.0 | 9% |
| Top-rope | 93 | 80.2 | 22% |
| Bouldering | 15 | 14.0 | 0% |
| Unspecified (312 untagged + 3 aid-only) | 315 | 315.0 | 29% |
| **total** | 2,962 (> 2,724) | **2,724** | |

**Multi-tag problem:** 230 accidents (8%) have 2–3 disciplines. Most are Ice + Mountaineering (100) or Mountaineering + Trad (91), plus Ice + Top-rope (11) and a long tail. If each tag counts as a full accident, the column sums to 2,962, not 2,724.

### Stage 3: Worst outcome (4 nodes, exclusive)

Outcome is tagged per climber, so 113 accidents carry more than one of Deadly/Serious/Minor. I collapse each accident to its **most severe** outcome. That's a severity ordering, not a primary-tag pick.

| Fatal | Serious injury | Minor injury | No injury reported |
|---|---|---|---|
| 544 | 1,776 | 215 | 189 |

"No injury reported" = none of the three tags. The dataset has no explicit no-injury tag.

---

## Design A: Discipline → Factor mix → Worst outcome

The middle stage is exclusive by construction (the "multiple factors" node approach applied to families):

| Human only | Human + environment | Environment only | No factor tagged |
|---|---|---|---|
| 1,641 | 606 | 216 | 261 |

- **Human:** the definitions file's Human Factors plus Alpine & Ice Climbing Factors (crampons, glissading, poor position, pitons/screws, ski, ascent illness).
- **Environment:** Natural Factors plus Alpine & Ice Natural Factors.
- Folding the alpine "factors" into Human is an editorial call.
- **Story:** human error dominates, but environment-only accidents are the deadliest (29% fatal vs 16% for human-only). Sport and top-rope are almost entirely human-only. Mountaineering is the only discipline where environment matters a lot (559 of 1,141).

## Design B: Discipline → What they were doing → Worst outcome (recommended)

The middle stage is a time-of-accident activity. The methodology tagged `Descent`, `Roped` and `Unroped`/`Solo` as status at the moment of the accident, not mentions anywhere in the narrative. Rule: Descent > Roped > Unroped/solo > Unclear.

| node | accidents | fatal share |
|---|---|---|
| Roped ascent | 1,102 | 11% |
| Descent | 865 | 23% |
| Unroped / solo ascent | 366 | **39%** |
| Unclear | 391 | 21% |

- **Story:** going up roped is the common case. Coming down is twice as deadly, and climbing without a rope is the deadliest. Trad is roped ascent (668 of 846). Mountaineering is descent-heavy (453) and often unclear (344, because alpine reports rarely tag roped/unroped).
- **Overlaps:** 482 descents were roped (rappel/lower) and stay "Descent". 5 rows are both Roped and Unroped.

## Design C: Discipline → Specific factor → Worst outcome (shown as the cautionary one)

Top 8 factors plus "Other factors" plus "None":

| Inadequate protection | Stranded/lost | Rappel error | No helmet | Exposure | Inadequate equipment | Off-route | Visibility |
|---|---|---|---|---|---|---|---|
| 606 | 316 | 251 | 250 | 241 | 239 | 239 | 235 |

- **Multi-tag problem at full strength:** 60% of accidents (1,632) have 2+ factor tags; 858 have 3+.
- Counting each tag as a full accident gives 4,583 flows out of 2,724 accidents.
- Under 1/n weighting, "Other factors" swallows 1,345 of 2,724 and the named bars shrink to 84–366. That weighting implies "this accident was 1/3 rappel error", which the methodology explicitly doesn't claim.
- Factors make a better **bar or dot chart at a drill-down juncture** than a Sankey stage.

---

## Recommended handling rule

1. **Discipline: fractional 1/n.** It touches only 8% of accidents, every column sums to exactly 2,724, and each band keeps a single discipline color. A "Multiple disciplines" node would need a color that isn't any of the six and would hide the meaningful Ice + Mountaineering group.
   - **Tradeoff:** node sizes are non-integer (Ice = 160.7). Tooltips should show both numbers: "223 accidents involve ice; weighted 161".
2. **Middle and outcome stages:** exclusive by construction (precedence / worst outcome), so no weighting is needed.
3. **Factors** never enter the Sankey. They appear in drill-downs as "% of accidents with this tag", where multi-tag is fine because each bar stands alone.

## Color: one scale per discipline

Aesthetics first, as requested. Each discipline gets a 5-step ramp:

- The **mid step (300)** is the node and band color.
- **Lighter steps** are for hover and dimmed states.
- **Darker steps** shade flows toward worse outcomes (e.g. the Fatal band from Trad uses Trad 500).

| discipline | 100 | 200 | **300 (base)** | 400 | 500 |
|---|---|---|---|---|---|
| Ice (blue) | `#dbe9f6` | `#a8cbea` | **`#5f9fd6`** | `#2f72b2` | `#1a4c80` |
| Mountaineering (gray) | `#ececea` | `#cfcfcb` | **`#a3a39e`** | `#7a7a75` | `#56564f` |
| Bouldering (black) | `#8a8a8a` | `#5c5c5c` | **`#2e2e2e`** | `#1c1c1c` | `#0a0a0a` |
| Sport (red) | `#f8d9d4` | `#eea69c` | **`#d9604f`** | `#b23a2c` | `#7f2219` |
| Trad (purple) | `#e8e0f3` | `#c5b2e2` | **`#9476c6`** | `#6c4ea6` | `#4a3378` |
| Top-rope (green) | `#d8eedc` | `#a6d6b0` | **`#5fae74`** | `#3a8a51` | `#245f36` |
| Unspecified | hatched/outline in the page ink color, no fill hue (open question) | | | | |

Middle-stage and outcome nodes are neutral (ink on the page background). Bands carry the discipline color all the way through, so a reader can trace Trad from left to right.

- **Mountaineering vs Bouldering vs Unspecified:** three neutrals means Bouldering stays near-black and Mountaineering stays mid-gray. Unspecified is outline-only so it never reads as a fourth gray.
- **Known tradeoff:** red/green (Sport/Top-rope) blur for red-green colorblind readers. Direct node labels carry identity so color is never the only cue.

## Drill-down junctures (size-scaled accident display)

At chosen points, the Sankey hands off to a view where **each accident is one mark**, sized by a per-accident value. Candidate size encodings (all exist in the data):

| size = | coverage | notes |
|---|---|---|
| Climbers involved (sum of age headcounts) | 1,894 (70%) | 1–12, one 25. Untagged rows would need a default size, which overstates certainty |
| Number of factors tagged (`COUNT OF TAGS`) | 100% | 1–17, median 6. Reads as "how many things went wrong" |
| Report length (words) | 100% | median 317. Proxy for how well documented, not severity |

Candidate junctures:

1. **After Stage 1, Mountaineering node:** its 1,245 accidents burst into a dot cloud, colored by mountaineering gray steps by outcome.
2. **Middle stage, "Unroped / solo ascent":** 366 dots, the 39% fatal ones dark. The strongest single fact in the data.
3. **Fatal node:** 544 dots laid out on a publication-year axis (1990–2019), colored by discipline. Answers "is it getting better?" (caveat: AAC editorial selection changed after 2015).
4. **Factor detail:** for one discipline, bars of "% with each factor tag". This is where Design C's content lives.
