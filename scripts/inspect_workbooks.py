"""Report workbook structure: sheets, visibility, dims, header row guess,
merged cells, hidden rows/cols, formula cells. Read-only on ./source."""
import sys, openpyxl
from openpyxl.utils import get_column_letter
from collections import Counter

for path in sys.argv[1:]:
    print("=" * 80); print(path)
    wb = openpyxl.load_workbook(path, data_only=False)
    for ws in wb.worksheets:
        print("-" * 60)
        print(f"sheet={ws.title!r} state={ws.sheet_state} dims={ws.dimensions} max_row={ws.max_row} max_col={ws.max_column}")
        print("  merged:", list(ws.merged_cells.ranges)[:20], f"(total {len(ws.merged_cells.ranges)})")
        hc = [k for k, d in ws.column_dimensions.items() if d.hidden]
        hr = [k for k, d in ws.row_dimensions.items() if d.hidden]
        print("  hidden cols:", hc[:40], f"(total {len(hc)})")
        print("  hidden rows:", hr[:20], f"(total {len(hr)})")
        print("  autofilter:", ws.auto_filter.ref, " freeze:", ws.freeze_panes)
        fcols = Counter(); nform = 0; examples = {}
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("="):
                    nform += 1; fcols[c.column_letter] += 1
                    examples.setdefault(c.column_letter, (c.coordinate, c.value[:160]))
        print(f"  formula cells: {nform} across {len(fcols)} cols")
        for col, n in sorted(fcols.items(), key=lambda x: openpyxl.utils.column_index_from_string(x[0]))[:80]:
            print(f"    {col}: {n}  e.g. {examples[col]}")
        for r in range(1, min(ws.max_row, 5) + 1):
            vals = [ws.cell(r, c).value for c in range(1, min(ws.max_column, 60) + 1)]
            print(f"  row{r}:", [str(v)[:40] if v is not None else None for v in vals])
