"""Exploratory counts for Step 3 Sankey proposals. Reads data/raw only."""
import pandas as pd, numpy as np, itertools, collections
df = pd.read_csv('data/raw/accidents__00_data.csv', dtype=str, keep_default_na=False)
T = df.columns[7:]
f = df[T].replace({'':'0','Y':'1'}).apply(pd.to_numeric) > 0
f.columns = [c.strip() for c in f.columns]
f = f[~f['Non-climbing']].reset_index(drop=True); N = len(f)
print("N climbing", N)

# --- discipline (6 nodes); Aid/Bouldering/untagged -> Other only if none of the 5 main
MAIN = {'Ice Climbing':'Ice','Alpine/Mountaineering':'Mountaineering','Trad Climbing':'Trad','Sport':'Sport','Top-Rope':'Top-rope','Bouldering':'Bouldering'}
disc = f[list(MAIN)].rename(columns=MAIN).apply(lambda r: [k for k in r.index if r[k]] or ['Other'], axis=1)
print("discipline set size:", disc.map(len).value_counts().sort_index().to_dict())
print("Other breakdown: aid-only", int((disc.map(lambda d: d==['Other']) & f['Aid & Big Wall Climbing']).sum()),
      "boulder", int((disc.map(lambda d: d==['Other']) & f['Bouldering']).sum()),
      "untagged", int((disc.map(lambda d: d==['Other']) & ~f['Aid & Big Wall Climbing'] & ~f['Bouldering']).sum()))
def tally(lists, frac=True):
    c = collections.Counter()
    for L in lists:
        for x in L: c[x] += 1/len(L) if frac else 1
    return c
print("disc any-tag:", dict(tally(disc, False)))
print("disc 1/n   :", {k: round(v,1) for k,v in tally(disc).items()})
print("multi-disc combos:", collections.Counter(' + '.join(d) for d in disc if len(d)>1).most_common(8))

# --- worst outcome (exclusive)
worst = np.select([f.Deadly, f.Serious, f.Minor], ['Fatal','Serious injury','Minor injury'], 'No injury reported')
print("worst outcome:", pd.Series(worst).value_counts().to_dict())

# --- design A: factor-family mix (exclusive by construction)
HUM = ['Pendulum','Non-Ascent Illness','Off-route','Rushed','Run Out','Crowds','Inadequate Food/Water','No Helmet','Late in Day','Late Start','Party Separated','Ledge Fall','Gym / Artificial','Gym Climber','Fatigue','Large Group','Distracted','Object Dropped/Dislodged','Handhold/Foothold Broke','Knot & Tie-in Error','No Backup or End Knot','Gear Broke','Intoxicated','Inadequate Equipment','Inadequate Protection / Pulled','Anchor Failure / Error','Stranded / Lost / Overdue','Belay Error','Rappel Error','Lowering Error','Miscommunication',
       'Piton/Ice Screw','Ascent Illness','Crampon Issues','Glissading','Ski-related','Poor Position']
ENV = ['Visibility','Severe Weather','Wildlife','Natural Rockfall','Poor Cond/Seasonal Risk','Avalanche','Cornice / Snow Bridge Collapse','Bergschrund','Crevasse / Moat / Berschrund','Icefall / Serac / Ice Avalanche','Exposure']
h, e = f[HUM].any(axis=1), f[ENV].any(axis=1)
mix = np.select([h&~e, e&~h, h&e], ['Human only','Environment only','Human + environment'], 'No factor tagged')
print("factor mix:", pd.Series(mix).value_counts().to_dict())

# --- design B: phase at time of accident
ph = np.select([f.Descent, f.Roped, f['Unroped']|f.Solo], ['Descent','Roped ascent','Unroped / solo ascent'], 'Unclear')
print("phase:", pd.Series(ph).value_counts().to_dict(), " roped&unroped both:", int((f.Roped&f.Unroped).sum()), " descent&roped:", int((f.Descent&f.Roped).sum()))

# --- design C: specific factors, top 8 + other
fc = f[HUM+ENV].sum().sort_values(ascending=False); print("top factors:", fc.head(12).to_dict())
TOP = list(fc.head(8).index)
fl = f[HUM+ENV].apply(lambda r: [k for k in TOP if r[k]] + (['Other factors'] if r[[k for k in HUM+ENV if k not in TOP]].any() else []) or ['No factor tagged'], axis=1)
print("factor list size:", fl.map(len).value_counts().sort_index().to_dict())
print("factor 1/n:", {k: round(v,1) for k,v in sorted(tally(fl).items(), key=lambda x:-x[1])})
print("factor any:", dict(tally(fl, False)), "sum any =", sum(tally(fl,False).values()))

# cross-tabs for designs (fractional on discipline)
def flows(a_lists, b, c):
    ab, bc = collections.Counter(), collections.Counter()
    for A, B, C in zip(a_lists, b, c):
        for x in A: ab[(x,B)] += 1/len(A)
        bc[(B,C)] += 1
    return ab, bc
for name, mid in [('A factor mix', mix), ('B phase', ph)]:
    ab, bc = flows(disc, mid, worst)
    print(f"\n{name} disc->mid:"); [print("  ", k, round(v,1)) for k,v in sorted(ab.items())]
    print(f"{name} mid->outcome:"); [print("  ", k, v) for k,v in sorted(bc.items())]
# fatality rate by discipline (1/n)
fat = collections.Counter(); tot = collections.Counter()
for A, W in zip(disc, worst):
    for x in A: tot[x]+=1/len(A); fat[x]+= (W=='Fatal')/len(A)
print("\nfatal share by disc:", {k: f"{fat[k]/tot[k]:.0%}" for k in tot})
