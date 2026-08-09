#!/usr/bin/env python3
"""
Repair rows in mf.csv where the fund `name` field contains an unescaped
comma (e.g. "... Direct Plan, IDCW Option"). Since the file has no CSV
quoting, such commas get parsed as extra field delimiters, shifting every
column after `name` out of place (or, if the row already happened to have
a trailing blank field to spare, silently misaligning isin/isin2/fund_house
without changing the total field count).

Detection: a row is flagged when its `isin` column doesn't look like a
real ISIN (12-char alphanumeric starting with 2 letters), isn't blank, and
isn't the literal "-" placeholder used elsewhere in this file for "no ISIN".

Repair: locate the `inception_date` field (matches DD-MM-YYYY) by scanning
forward - it's a reliable anchor since it always keeps its schema position.
`fund_house` is the field immediately before it. Within the fields between
`name` and `fund_house`, any that match the ISIN pattern are taken as
isin/isin2 (in schema order); everything else is rejoined back into `name`
using " - " as the separator (this file's existing convention for plan/
option suffixes, e.g. "... Direct Plan - Growth Option") rather than a
literal comma, since the file has no CSV quoting and a comma would just
re-break the next naive parse. If the row is left short of the expected 16
columns (some of these rows are also missing their final trailing empty
field), it's padded with empty strings at the end.
"""
import csv
import re
import sys
from pathlib import Path

ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
DATE_RE = re.compile(r"^\d{2}-\d{2}-\d{4}$")


def is_bad_isin(value: str) -> bool:
    v = value.strip()
    if not v or v == "-":
        return False
    return not ISIN_RE.match(v)


def fix_row(fields: list[str], header_len: int) -> list[str] | None:
    code = fields[0]
    d = None
    for idx in range(2, len(fields)):
        if DATE_RE.match(fields[idx].strip()):
            d = idx
            break
    if d is None:
        return None

    fund_house = fields[d - 1]
    region = fields[1:d - 1]
    isin_positions = [i for i, v in enumerate(region) if ISIN_RE.match(v.strip())]

    if len(isin_positions) >= 2:
        i1, i2 = isin_positions[-2], isin_positions[-1]
        isin, isin2 = region[i1], region[i2]
        name_parts = region[:i1]
    elif len(isin_positions) == 1:
        i1 = isin_positions[0]
        isin = region[i1]
        rest_after = region[i1 + 1:]
        isin2 = rest_after[0] if rest_after else ""
        name_parts = region[:i1]
    else:
        isin, isin2 = "", ""
        name_parts = region[:]

    name = " - ".join(part.strip() for part in name_parts)
    new_fields = [code, name, isin, isin2, fund_house] + fields[d:]

    if len(new_fields) < header_len:
        new_fields += [""] * (header_len - len(new_fields))
    if len(new_fields) != header_len:
        return None
    return new_fields


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "mf.csv")
    with path.open(newline="", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].rstrip("\n").split(",")
    header_len = len(header)
    idx_isin = header.index("isin")

    fixed_count = 0
    unfixable = []
    out_lines = [lines[0]]

    for lineno, line in enumerate(lines[1:], start=2):
        raw = line.rstrip("\n")
        fields = raw.split(",")
        needs_fix = len(fields) != header_len or (
            len(fields) > idx_isin and is_bad_isin(fields[idx_isin])
        )
        if not needs_fix:
            out_lines.append(line)
            continue

        fixed = fix_row(fields, header_len)
        if fixed is None:
            unfixable.append((lineno, raw))
            out_lines.append(line)
            continue

        fixed_count += 1
        out_lines.append(",".join(fixed) + "\n")

    with path.open("w", encoding="utf-8") as f:
        f.writelines(out_lines)

    print(f"Fixed {fixed_count} row(s) in {path}")
    if unfixable:
        print(f"Could not auto-fix {len(unfixable)} row(s):")
        for lineno, raw in unfixable:
            print(f"  line {lineno}: {raw}")


if __name__ == "__main__":
    main()
