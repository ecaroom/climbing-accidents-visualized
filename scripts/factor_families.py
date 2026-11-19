"""Exploratory: candidate factor-family schemes for Sankey view A. Reads data/clean/accidents.csv."""
import pandas as pd, collections, itertools
a = pd.read_csv("data/clean/accidents.csv", keep_default_na=False)
F = a.factors.map(lambda s: set(t for t in s.split(";") if t))
N = len(a)

SCHEMES = {
 "S7 (seven families)": {
  "Rope & belay systems": ["Belay Error", "Rappel Error", "Lowering Error", "Knot & Tie-in Error", "No Backup or End Knot",
                           "Anchor Failure / Error", "Miscommunication", "Pendulum"],
  "Protection & gear": ["Inadequate Protection / Pulled", "Gear Broke", "Piton/Ice Screw", "Crampon Issues",
                        "Inadequate Equipment", "No Helmet", "Run Out"],
  "Decisions & timing": ["Off-route", "Rushed", "Late Start", "Late in Day", "Party Separated", "Large Group", "Crowds",
                         "Distracted", "Intoxicated", "Stranded / Lost / Overdue", "Poor Position", "Gym Climber",
                         "Gym / Artificial", "Climbing Alone"],
  "Body & health": ["Fatigue", "Inadequate Food/Water", "Ascent Illness", "Non-Ascent Illness"],
  "Movement & terrain": ["Handhold/Foothold Broke", "Ledge Fall", "Glissading", "Ski-related", "Object Dropped/Dislodged"],
  "Mountain hazards": ["Avalanche", "Icefall / Serac / Ice Avalanche", "Cornice / Snow Bridge Collapse",
                       "Crevasse / Moat / Berschrund", "Bergschrund", "Natural Rockfall", "Wildlife"],
  "Weather & conditions": ["Severe Weather", "Visibility", "Exposure", "Poor Cond/Seasonal Risk"],
 },
}
S7 = SCHEMES["S7 (seven families)"]
SCHEMES["S5 (five families)"] = {
  "Rope, belay & gear": S7["Rope & belay systems"] + S7["Protection & gear"],
  "Decisions & timing": S7["Decisions & timing"],
  "Body & health": S7["Body & health"],
  "Movement & terrain": S7["Movement & terrain"],
  "Mountain & weather": S7["Mountain hazards"] + S7["Weather & conditions"],
}
all_f = set(t for s in F for t in s)
for name, fam in SCHEMES.items():
    tags = [t for v in fam.values() for t in v]
    missing = all_f - set(tags); dup = [t for t, c in collections.Counter(tags).items() if c > 1]
    inv = {t: k for k, v in fam.items() for t in v}
    fams = F.map(lambda s: sorted({inv[t] for t in s if t in inv}))
    n = fams.map(len)
    print(f"\n===== {name}  (unassigned: {sorted(missing)}, duplicated: {dup})")
    print("families per accident:", {k: f"{v} ({v/N:.0%})" for k, v in n.value_counts().sort_index().items()})
    anyc = collections.Counter(f for fs in fams for f in fs)
    frac = collections.Counter()
    for fs in fams:
        for f in fs: frac[f] += 1 / len(fs)
    single = collections.Counter(fs[0] for fs in fams if len(fs) == 1)
    fatal = collections.Counter(); 
    for fs, w in zip(fams, a.worst_outcome):
        for f in fs: fatal[f] += (w == "fatal") / len(fs)
    print(f"{'family':24} {'any tag':>8} {'1/n':>8} {'only this':>10} {'fatal(1/n)':>10}")
    for k in fam:
        print(f"{k:24} {anyc[k]:8} {frac[k]:8.0f} {single[k]:10} {fatal[k]/frac[k]:10.0%}")
    print(f"{'(no factor)':24} {int((n==0).sum()):8} {int((n==0).sum()):8} {int((n==0).sum()):10}")
    print(f"{'(2+ families)':24} {'':8} {'':8} {int((n>=2).sum()):10}")
    pairs = collections.Counter(p for fs in fams if len(fs) == 2 for p in [" + ".join(fs)])
    print("top 2-family combos:", pairs.most_common(6))
