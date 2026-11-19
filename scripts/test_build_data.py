"""Assertions on build_data.py outputs. Run after build:
    .venv/bin/python scripts/build_data.py && .venv/bin/python scripts/test_build_data.py
Plain asserts, no pytest needed. Exits non-zero on the first failure."""
import json, pathlib, collections
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOL = 1e-3  # link values are rounded to 6 dp
acc = pd.read_csv(ROOT / "data/clean/accidents.csv", dtype={"id": str})
raw = pd.read_csv(ROOT / "data/raw/accidents__00_data.csv", dtype=str, keep_default_na=False)
sk = json.loads((ROOT / "site/sankey.json").read_text())
passed = []

def check(name, cond, detail=""):
    assert cond, f"FAIL {name} {detail}"
    passed.append(name)

# ---- row counts
check("raw rows = 2770", len(raw) == 2770, len(raw))
check("non-climbing = 46", (raw["Non-climbing"] != "").sum() == 46)
check("clean rows = 2724", len(acc) == 2724, len(acc))
check("ids unique", acc.id.is_unique)
check("no non-climbing ids leak", not set(acc.id) & set(raw.loc[raw["Non-climbing"] != "", "ID"]))
check("meta n_accidents", sk["meta"]["n_accidents"] == 2724)

# ---- per-accident weighting
check("weights = 1/n", ((acc.discipline_weight * acc.n_disciplines - 1).abs() < 1e-9).all())
check("each accident in exactly one activity / mix / outcome",
      acc.activity.notna().all() and acc.factor_mix.notna().all() and acc.worst_outcome.notna().all())
check("outcome counts", acc.worst_outcome.value_counts().to_dict() == {"serious": 1776, "fatal": 544, "minor": 215, "none": 189})

# ---- sankey reconciliation, per view
expected_mid = {"A": acc.factor_mix.value_counts(), "B": acc.activity.value_counts()}
for v, view in sk["views"].items():
    nodes = {n["id"]: n for n in view["nodes"]}
    inflow, outflow = collections.Counter(), collections.Counter()
    for l in view["links"]:
        check(f"{v} link endpoints exist", l["source"] in nodes and l["target"] in nodes, l)
        check(f"{v} link value > 0", l["value"] > 0, l)
        outflow[l["source"]] += l["value"]; inflow[l["target"]] += l["value"]
    for stage, flow in [(0, outflow), (2, inflow)]:
        tot = sum(flow[n] for n in nodes if nodes[n]["stage"] == stage)
        check(f"{v} stage {stage} sums to 2724", abs(tot - 2724) < TOL, tot)
    for nid, n in nodes.items():
        if n["stage"] == 1:
            check(f"{v} {nid} in == out", abs(inflow[nid] - outflow[nid]) < TOL, (inflow[nid], outflow[nid]))
            check(f"{v} {nid} == accident count", abs(inflow[nid] - expected_mid[v][nid.split(':')[1]]) < TOL)
            check(f"{v} {nid} n field", n["n"] == expected_mid[v][nid.split(':')[1]])
    for o in sk["outcomes"]:
        check(f"{v} outcome {o['id']}", abs(inflow[f"o:{o['id']}"] - o["n"]) < TOL, (inflow[f"o:{o['id']}"], o["n"]))
    # per discipline: weighted outflow from discipline == weighted inflow to outcomes for that discipline
    by_d_left, by_d_right = collections.Counter(), collections.Counter()
    for l in view["links"]:
        if nodes[l["source"]]["stage"] == 0: by_d_left[l["discipline"]] += l["value"]
        else: by_d_right[l["discipline"]] += l["value"]
    for d in sk["disciplines"]:
        check(f"{v} {d['id']} conserved", abs(by_d_left[d["id"]] - by_d_right[d["id"]]) < TOL)
        check(f"{v} {d['id']} == n_weighted", abs(by_d_left[d["id"]] - d["n_weighted"]) < 0.06)

# ---- discipline any-tag counts match flags
for d in sk["disciplines"]:
    if d["id"] != "unspecified":
        check(f"n_any {d['id']}", d["n_any"] == acc[f"is_{d['id']}"].sum())
check("unspecified n_any", sk["disciplines"][-1]["n_any"] == (acc.disciplines == "unspecified").sum())

# ---- n_tags matches the source workbook's COUNT OF TAGS column
src = raw.loc[raw["Non-climbing"] == "", ["ID", "COUNT OF TAGS"]].set_index("ID")["COUNT OF TAGS"].astype(int)
check("n_tags == COUNT OF TAGS", (acc.set_index("id").n_tags == src.reindex(acc.id).values).all())

print(f"OK: {len(passed)} checks passed")
