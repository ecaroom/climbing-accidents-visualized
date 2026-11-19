"""Build tidy data + Sankey JSON straight from ./source (rerunnable, never writes there).

Outputs
  data/clean/accidents.csv      one row per climbing accident (Non-climbing excluded)
  data/clean/accident_tags.csv  long format: one row per (accident, tag) for climbing accidents
  site/sankey.json              nodes/links for view A (factor mix) and view B (activity)
  site/accidents.json           compact per-accident records for tomorrow's drill-down views

Approved rules (see data/SANKEY_PROPOSALS.md)
  Discipline   fractional 1/n across the accident's disciplines; none -> "Unspecified"
  Middle A     factor mix: Human only / Human + environment / Environment only / No factor tagged
  Middle B     activity at time of accident: Descent > Roped ascent > Unroped/solo ascent > Unclear
  Outcome      worst outcome: Fatal > Serious injury > Minor injury > No injury reported
  Mid->outcome links are split per discipline so band colour runs left to right.

Run: .venv/bin/python scripts/build_data.py
"""
import json, pathlib, re
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "source" / "_github-AAC_accidents_tagged_data.xlsx"
CLEAN, SITE = ROOT / "data" / "clean", ROOT / "site"
REPO_URL = "https://github.com/ecaroom/climbing-accidents"

# ---------- vocab ----------
AGE = ["<15", "15-20", "21-25", "26-30", "31-35", "36-50", "51-75", ">75"]
EXPERIENCE = ["No/Little", "Moderate", "Experienced", "Unknown"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
# Human Factors + Alpine & Ice Climbing Factors (definitions-file sections)
HUMAN = ["Pendulum", "Non-Ascent Illness", "Off-route", "Rushed", "Run Out", "Crowds",
         "Inadequate Food/Water", "No Helmet", "Late in Day", "Late Start", "Party Separated",
         "Ledge Fall", "Gym / Artificial", "Gym Climber", "Fatigue", "Large Group", "Distracted",
         "Object Dropped/Dislodged", "Handhold/Foothold Broke", "Knot & Tie-in Error",
         "No Backup or End Knot", "Gear Broke", "Intoxicated", "Inadequate Equipment",
         "Inadequate Protection / Pulled", "Anchor Failure / Error", "Stranded / Lost / Overdue",
         "Belay Error", "Rappel Error", "Lowering Error", "Miscommunication",
         "Piton/Ice Screw", "Ascent Illness", "Crampon Issues", "Glissading", "Ski-related",
         "Poor Position"]
# Natural Factors + Alpine & Ice Climbing Natural Factors
ENVIRONMENT = ["Visibility", "Severe Weather", "Wildlife", "Natural Rockfall",
               "Poor Cond/Seasonal Risk", "Avalanche", "Cornice / Snow Bridge Collapse",
               "Bergschrund", "Crevasse / Moat / Berschrund", "Icefall / Serac / Ice Avalanche",
               "Exposure"]
FAMILY = {**{t: "Age" for t in AGE}, **{t: "Experience" for t in EXPERIENCE},
          **{t: "Month" for t in MONTHS}, **{t: "Human factor" for t in HUMAN},
          **{t: "Environment factor" for t in ENVIRONMENT},
          **{t: "Outcome" for t in ["Deadly", "Serious", "Minor", "Head / Brain Injury"]}}

# Discipline nodes, top-to-bottom order; ramps 100..500, base = index 2
DISCIPLINES = [
    ("mountaineering", "Mountaineering", "Alpine/Mountaineering",
     ["#ececea", "#cfcfcb", "#a3a39e", "#7a7a75", "#56564f"]),
    ("ice", "Ice", "Ice Climbing", ["#dbe9f6", "#a8cbea", "#5f9fd6", "#2f72b2", "#1a4c80"]),
    ("trad", "Trad", "Trad Climbing", ["#e8e0f3", "#c5b2e2", "#9476c6", "#6c4ea6", "#4a3378"]),
    ("sport", "Sport", "Sport", ["#f8d9d4", "#eea69c", "#d9604f", "#b23a2c", "#7f2219"]),
    ("toprope", "Top-rope", "Top-Rope", ["#d8eedc", "#a6d6b0", "#5fae74", "#3a8a51", "#245f36"]),
    ("bouldering", "Bouldering", "Bouldering", ["#8a8a8a", "#5c5c5c", "#2e2e2e", "#1c1c1c", "#0a0a0a"]),
    ("unspecified", "Unspecified", None, None),  # outline-only in the site
]
DISC_COL = {d[0]: d[2] for d in DISCIPLINES if d[2]}

# View C: the 48 factor tags grouped into seven families (approved 2026-11-19, "Option 1").
# Human-side families first, then environment, mirroring view A's order.
FACTOR_FAMILIES = [
    ("gear", "Protection & gear", ["Inadequate Protection / Pulled", "Gear Broke", "Piton/Ice Screw", "Crampon Issues",
                                   "Inadequate Equipment", "No Helmet", "Run Out"]),
    ("rope", "Rope & belay systems", ["Belay Error", "Rappel Error", "Lowering Error", "Knot & Tie-in Error",
                                      "No Backup or End Knot", "Anchor Failure / Error", "Miscommunication", "Pendulum"]),
    ("decisions", "Decisions & timing", ["Off-route", "Rushed", "Late Start", "Late in Day", "Party Separated",
                                         "Large Group", "Crowds", "Distracted", "Intoxicated", "Stranded / Lost / Overdue",
                                         "Poor Position", "Gym Climber", "Gym / Artificial"]),
    ("movement", "Movement & terrain", ["Handhold/Foothold Broke", "Ledge Fall", "Glissading", "Ski-related",
                                        "Object Dropped/Dislodged"]),
    ("body", "Body & health", ["Fatigue", "Inadequate Food/Water", "Ascent Illness", "Non-Ascent Illness"]),
    ("weather", "Weather & conditions", ["Severe Weather", "Visibility", "Exposure", "Poor Cond/Seasonal Risk"]),
    ("hazards", "Mountain hazards", ["Avalanche", "Icefall / Serac / Ice Avalanche", "Cornice / Snow Bridge Collapse",
                                     "Crevasse / Moat / Berschrund", "Bergschrund", "Natural Rockfall", "Wildlife"]),
]
FAMILY_OF = {t: k for k, _, tags in FACTOR_FAMILIES for t in tags}

MIDDLE = {
    "A": ("Human vs. environment", [("human", "Human only"), ("both", "Human + environment"),
                                    ("env", "Environment only"), ("nofactor", "No factor tagged")]),
    "C": ("Factor families", [(k, lab) for k, lab, _ in FACTOR_FAMILIES] + [("nofactor", "No factor tagged")]),
    "B": ("What they were doing", [("roped", "Roped ascent"), ("descent", "Descent"),
                                   ("unroped", "Unroped / solo ascent"), ("unclear", "Unclear")]),
}
# severity colours (wine -> burnt orange -> amber -> stone), kept off the discipline hues
# Location: state / province named in the report's first line (fallback: title, then opening text)
REGIONS = ["West Virginia", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
           "North Dakota", "South Carolina", "South Dakota", "Rhode Island", "British Columbia",
           "Northwest Territories", "New Brunswick", "Nova Scotia",
           "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
           "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
           "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
           "Missouri", "Montana", "Nebraska", "Nevada", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
           "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "Wisconsin", "Wyoming",
           "Alberta", "Yukon", "Ontario", "Quebec", "Québec", "Nunavut", "Newfoundland", "Manitoba",
           "Saskatchewan", "Labrador"]
REGION_RE = re.compile(r"\b(" + "|".join(re.escape(r) for r in REGIONS) + r")\b")

# Text cues for intake fields that have no tag. Narrative mentions only, so sparse and approximate.
CUES = {
    "cue_gap": r"(?:hadn'?t climbed|had not climbed|first time (?:climbing )?in (?:years|months|a while)|returning to climbing"
               r"|time off from climbing|layoff|rusty|out of practice|away from climbing|first climb (?:of|since))",
    "cue_new_area": r"(?:first time (?:at|on|in|to|visiting)|unfamiliar with (?:the )?(?:area|route|terrain|rock)|first visit"
                    r"|new to the area|never been)",
    "cue_new_style": r"(?:first (?:time )?(?:ice|sport|trad|lead|multi-?pitch|alpine)|new to (?:ice|sport|trad|lead|climbing|alpine)"
                     r"|first lead|first time leading)",
}

OUTCOMES = [("fatal", "Fatal", "#7f1d2b"), ("serious", "Serious injury", "#c45a1c"),
            ("minor", "Minor injury", "#e0a43a"), ("none", "No injury reported", "#c9c2b2")]


def load():
    raw = pd.read_excel(SRC, sheet_name="data", engine="openpyxl", dtype=object)
    raw.columns = [str(c).strip() for c in raw.columns]
    tagcols = raw.columns[7:]
    # 'Y' in month columns means 1; age columns are headcounts
    flags = raw[tagcols].map(lambda v: 1 if v == "Y" else v).apply(pd.to_numeric, errors="raise").fillna(0)
    return raw, flags


def build():
    raw, num = load()
    assert len(raw) == 2770, len(raw)
    f = num > 0
    climbing = ~f["Non-climbing"]
    raw, num, f = raw[climbing].reset_index(drop=True), num[climbing].reset_index(drop=True), f[climbing].reset_index(drop=True)

    out = pd.DataFrame({
        "id": raw["ID"].astype(str),
        "pub_year": pd.to_numeric(raw["Publication Year"], errors="coerce").astype("Int64"),
        "title": raw["Accident Title"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip(),
    "text": raw["Text"].astype(str),
        "text_words": raw["Text"].astype(str).str.split().str.len(),
    })
    for key, col in DISC_COL.items():
        out[f"is_{key}"] = f[col].astype(int)
    out["is_aid_bigwall"] = f["Aid & Big Wall Climbing"].astype(int)
    discs = [[k for k in DISC_COL if f.at[i, DISC_COL[k]]] or ["unspecified"] for i in range(len(f))]
    out["disciplines"] = [";".join(d) for d in discs]
    out["n_disciplines"] = [len(d) for d in discs]
    out["discipline_weight"] = 1 / out["n_disciplines"]

    for c, k in [("Descent", "descent"), ("Roped", "roped"), ("Unroped", "unroped"),
                 ("Solo", "solo"), ("Climbing Alone", "climbing_alone")]:
        out[f"is_{k}"] = f[c].astype(int)
    out["activity"] = np.select([f["Descent"], f["Roped"], f["Unroped"] | f["Solo"]],
                                ["descent", "roped", "unroped"], "unclear")

    h, e = f[HUMAN].any(axis=1), f[ENVIRONMENT].any(axis=1)
    out["factor_mix"] = np.select([h & ~e, h & e, e & ~h], ["human", "both", "env"], "nofactor")
    out["n_human_factors"] = f[HUMAN].sum(axis=1)
    out["n_env_factors"] = f[ENVIRONMENT].sum(axis=1)
    out["factors"] = [";".join(t for t in HUMAN + ENVIRONMENT if f.at[i, t]) for i in range(len(f))]
    assert set(FAMILY_OF) == set(HUMAN + ENVIRONMENT), "every factor tag must be in exactly one family"
    fams = [[k for k, _, tags in FACTOR_FAMILIES if any(f.at[i, t] for t in tags)] or ["nofactor"] for i in range(len(f))]
    out["factor_families"] = [";".join(x) for x in fams]
    out["n_factor_families"] = [0 if x == ["nofactor"] else len(x) for x in fams]

    out["deadly"], out["serious"], out["minor"] = (f[c].astype(int) for c in ["Deadly", "Serious", "Minor"])
    out["head_injury"] = f["Head / Brain Injury"].astype(int)
    out["worst_outcome"] = np.select([f["Deadly"], f["Serious"], f["Minor"]], ["fatal", "serious", "minor"], "none")

    out["experience"] = [";".join(t for t in EXPERIENCE if f.at[i, t]) for i in range(len(f))]
    # party size proxy: climbers whose age band is reported. Blank when no ages given.
    ps = num[AGE].sum(axis=1).astype(int)
    out["party_size"] = ps.where(ps > 0).astype("Int64")
    out["months"] = [";".join(t for t in MONTHS if f.at[i, t]) for i in range(len(f))]
    out["n_tags"] = f.loc[:, "No/Little":"Miscommunication"].sum(axis=1)  # = source COUNT OF TAGS

    # ---- intake-matching fields
    first_line = raw["Text"].astype(str).str.strip().str.split("\n").str[0].str.strip()
    def region(i):
        for src in (first_line[i], str(raw["Accident Title"][i]), str(raw["Text"][i])[:400]):
            m = REGION_RE.search(src)
            if m: return "Quebec" if m.group(1) == "Québec" else m.group(1)
        return None
    out["region"] = [region(i) for i in range(len(raw))]
    out["location_line"] = [fl if len(fl) < 120 else "" for fl in first_line]
    for c, k in [("Large Group", "large_group"), ("Late in Day", "late_in_day"), ("Late Start", "late_start"),
                 ("Visibility", "visibility")]:
        out[f"is_{k}"] = f[c].astype(int)
    low = raw["Text"].astype(str).str.lower()
    for k, pat in CUES.items():
        out[k] = low.str.contains(pat, regex=True).astype(int)

    # long tag table
    long = (num.assign(id=out["id"]).melt(id_vars="id", var_name="tag", value_name="value"))
    long = long[long.value > 0].copy()
    long["family"] = long.tag.map(FAMILY).fillna("Type of climbing")
    long["value"] = long["value"].astype(int)
    long = long[["id", "family", "tag", "value"]].sort_values(["id", "family", "tag"])
    return out, long


def sankey(out):
    disc_nodes = [{"id": f"d:{k}", "label": lab, "stage": 0, "discipline": k} for k, lab, _, _ in DISCIPLINES]
    out_nodes = [{"id": f"o:{k}", "label": lab, "stage": 2} for k, lab, _ in OUTCOMES]
    exploded = out.assign(discipline=out.disciplines.str.split(";")).explode("discipline")
    views = {}
    for v, (title, mids) in MIDDLE.items():
        col = {"A": "factor_mix", "B": "activity", "C": "family"}[v]
        if v == "C":   # also split each accident across its factor families: weight = 1/n_disc * 1/n_fam
            ex = exploded.assign(family=exploded.factor_families.str.split(";")).explode("family")
            ex = ex.assign(w=ex.discipline_weight / ex.n_factor_families.clip(lower=1))
        else:
            ex = exploded.assign(w=exploded.discipline_weight)
        mid_nodes = [{"id": f"m{v}:{k}", "label": lab, "stage": 1, "slot": i} for i, (k, lab) in enumerate(mids)]
        links = []
        for (d, m), w in ex.groupby(["discipline", col]).w.sum().items():
            links.append({"source": f"d:{d}", "target": f"m{v}:{m}", "discipline": d, "value": round(float(w), 6)})
        for (d, m, o), w in ex.groupby(["discipline", col, "worst_outcome"]).w.sum().items():
            links.append({"source": f"m{v}:{m}", "target": f"o:{o}", "discipline": d, "value": round(float(w), 6)})
        order_d = {k: i for i, (k, *_r) in enumerate(DISCIPLINES)}
        order_m = {k: i for i, (k, _) in enumerate(mids)}
        order_o = {k: i for i, (k, *_r) in enumerate(OUTCOMES)}
        # Input order = band stacking order (site uses linkSort(null)).
        # disc->mid: by discipline then middle node. mid->outcome: by middle node, outcome, then discipline,
        # so bands leave each middle node grouped by outcome and cross as little as possible.
        def key(l):
            if l["source"].startswith("d:"):
                return (0, order_d[l["discipline"]], order_m[l["target"].split(":")[1]], 0)
            return (1, order_m[l["source"].split(":")[1]], order_o[l["target"].split(":")[1]], order_d[l["discipline"]])
        links.sort(key=key)
        if v == "C":   # n = weighted size (what the bar shows); n_any = accidents with any tag in the family
            per_acc = out.assign(family=out.factor_families.str.split(";")).explode("family")
            per_acc = per_acc.assign(w=1 / per_acc.n_factor_families.clip(lower=1))
            wsum, anyc = per_acc.groupby("family").w.sum(), per_acc.family.value_counts()
            for n in mid_nodes:
                k = n["id"].split(":")[1]
                n["n"], n["n_any"] = round(float(wsum.get(k, 0)), 1), int(anyc.get(k, 0))
        else:
            counts = out[col].value_counts()
            for n in mid_nodes:
                n["n"] = int(counts.get(n["id"].split(":")[1], 0))
        views[v] = {"title": title, "nodes": disc_nodes + mid_nodes + out_nodes, "links": links}

    any_tag = exploded.discipline.value_counts()
    weighted = exploded.groupby("discipline").discipline_weight.sum()
    oc = out.worst_outcome.value_counts()
    return {
        "meta": {
            "n_accidents": int(len(out)),
            "source": REPO_URL,
            "attribution": "Data: an analysis of the AAC's climbing accident reports by Eliot Caroom (CC BY 4.0)",
            "weighting": "Accidents with n disciplines contribute 1/n to each. In view C, each accident's share is also "
                         "split across its n factor families. Other middle stages and the outcome stage are exclusive.",
        },
        "disciplines": [{"id": k, "label": lab, "ramp": ramp, "outline": ramp is None,
                         "n_any": int(any_tag.get(k, 0)), "n_weighted": round(float(weighted.get(k, 0)), 1)}
                        for k, lab, _, ramp in DISCIPLINES],
        "outcomes": [{"id": k, "label": lab, "color": c, "n": int(oc.get(k, 0))} for k, lab, c in OUTCOMES],
        "views": views,
    }


def main():
    CLEAN.mkdir(parents=True, exist_ok=True); SITE.mkdir(parents=True, exist_ok=True)
    out, long = build()
    text = out.pop("text")
    out.to_csv(CLEAN / "accidents.csv", index=False, encoding="utf-8")
    long.to_csv(CLEAN / "accident_tags.csv", index=False, encoding="utf-8")
    (SITE / "sankey.json").write_text(json.dumps(sankey(out), indent=1), encoding="utf-8")
    lite = out[["id", "pub_year", "title", "disciplines", "activity", "factor_mix", "worst_outcome",
                "party_size", "n_tags", "factors", "factor_families", "region", "location_line", "months", "experience",
                "is_climbing_alone", "is_solo", "is_large_group", "is_late_in_day", "is_late_start", "is_visibility",
                "cue_gap", "cue_new_area", "cue_new_style"]].copy()
    lite["factor_families"] = lite.factor_families.str.split(";")
    lite["months"] = lite.months.map(lambda s: [t for t in s.split(";") if t])
    lite["experience"] = lite.experience.map(lambda s: [t for t in s.split(";") if t])
    lite["disciplines"] = lite.disciplines.str.split(";")
    lite["factors"] = lite.factors.map(lambda s: [t for t in s.split(";") if t])
    lite["env_factors"] = lite.factors.map(lambda fs: [t for t in fs if t in ENVIRONMENT])
    recs = json.loads(lite.to_json(orient="records"))
    # full report narratives, loaded lazily by the viewer pane for keyword search
    (SITE / "reports.json").write_text(json.dumps(dict(zip(out["id"], text.str.strip())), ensure_ascii=False,
                                                  separators=(",", ":")), encoding="utf-8")
    (SITE / "accidents.json").write_text(json.dumps(recs, separators=(",", ":")), encoding="utf-8")
    print(f"accidents.csv {len(out)} rows x {out.shape[1]} cols; accident_tags.csv {len(long)} rows; "
          f"sankey.json views {list(MIDDLE)}; accidents.json {len(recs)} records")


if __name__ == "__main__":
    main()
