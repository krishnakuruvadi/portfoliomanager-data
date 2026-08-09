#!/usr/bin/env python3
"""
Retroactively apply helpers.amfi_taxonomy.apply_known_amfi_aliases to every
row already in mf.csv, not just newly-fetched data. get_details_amfi
corrects known upstream drift (e.g. "Equity Schemes" -> "Equity Scheme",
"Sectoral Fund" -> "Sectoral/ Thematic") going forward, but mf.csv already
had rows written before that correction existed; this brings those in
line so the file only ever contains the canonical values.

Edits are done as a plain raw split on each line (no csv module) so that
rows are otherwise byte-for-byte unchanged - only the amfi_fund_type and
amfi_category columns are rewritten, and only on rows an alias applies to.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from helpers.amfi_taxonomy import apply_known_amfi_aliases


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "mf.csv")
    with path.open(newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split(",")
    idx_type = header.index("amfi_fund_type")
    idx_category = header.index("amfi_category")

    changed = 0
    out_lines = [lines[0]]
    for line in lines[1:]:
        fields = line.rstrip("\n").split(",")
        if len(fields) <= max(idx_type, idx_category):
            out_lines.append(line)
            continue

        new_type, new_category = apply_known_amfi_aliases(fields[idx_type], fields[idx_category])
        if new_type != fields[idx_type] or new_category != fields[idx_category]:
            fields[idx_type] = new_type
            fields[idx_category] = new_category
            out_lines.append(",".join(fields) + "\n")
            changed += 1
        else:
            out_lines.append(line)

    with path.open("w", encoding="utf-8") as f:
        f.writelines(out_lines)

    print(f"Normalized {changed} row(s) in {path}")


if __name__ == "__main__":
    main()
