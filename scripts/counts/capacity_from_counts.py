#!/usr/bin/env python3
"""Recompute the empirical weaving capacity from the field count workbook.

The capacity quoted in the report comes from one tally sheet, and until now the
only way to check it was to open the spreadsheet and read a formula. This
script re-derives it from the file itself, with the standard library only
(an .xlsx is a zip of XML), so it runs in CI next to the other checks.

What it does, for `data/counts/peak_merge.xlsx` by default:

* finds the sheet whose header row declares a `total (w/o motorcycles)` column;
* re-adds every populated one-minute row from the per-class columns;
* cross-checks that against the totals the workbook itself stores;
* reads the survey duration out of the workbook's own `* 60 / <minutes>`
  formula rather than assuming it;
* reports the negative entries, because they change the total and a reader
  who opens the sheet will find them.

    python scripts/counts/capacity_from_counts.py
    python scripts/counts/capacity_from_counts.py --workbook data/counts/offpeak_merge.xlsx
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

TOTAL_HEADER = "total (w/o motorcycles)"
CLASS_HEADER = re.compile(r"^(?P<group>[^_]+)_(?P<vehicle>cars|motorcycles|buses|trucks)$")
PER_HOUR_FORMULA = re.compile(r"\*\s*60\s*/\s*(?P<minutes>\d+(?:\.\d+)?)")
CELL_REF = re.compile(r"^(?P<column>[A-Z]+)(?P<row>\d+)$")

EXCLUDED_VEHICLE = "motorcycles"


def _text(element):
    return "".join(node.text or "" for node in element.iter(f"{{{MAIN_NS}}}t"))


def _shared_strings(archive):
    try:
        raw = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    return [_text(item) for item in ET.fromstring(raw)]


def _worksheet_parts(archive):
    """Sheet name -> archive path, in workbook order."""
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {r.attrib["Id"]: r.attrib["Target"] for r in rels.iter(f"{{{PKG_REL_NS}}}Relationship")}
    parts = {}
    for sheet in workbook.iter(f"{{{MAIN_NS}}}sheet"):
        target = targets[sheet.attrib[f"{{{DOC_REL_NS}}}id"]]
        parts[sheet.attrib["name"]] = "xl/" + target.lstrip("/")
    return parts


def read_sheet(archive, part, shared):
    """{cell reference: {'value': str|None, 'formula': str|None}} for one sheet."""
    sheet = ET.fromstring(archive.read(part))
    cells = {}
    for cell in sheet.iter(f"{{{MAIN_NS}}}c"):
        ref = cell.attrib["r"]
        kind = cell.attrib.get("t")
        formula = cell.find(f"{{{MAIN_NS}}}f")
        value_node = cell.find(f"{{{MAIN_NS}}}v")
        value = value_node.text if value_node is not None else None
        if kind == "s" and value is not None:
            value = shared[int(value)]
        elif kind == "inlineStr":
            inline = cell.find(f"{{{MAIN_NS}}}is")
            value = _text(inline) if inline is not None else None
        cells[ref] = {"value": value,
                      "formula": formula.text if formula is not None else None}
    return cells


def _repo_relative(path):
    """Print paths relative to the repository so output is machine-independent."""
    path = Path(path).resolve()
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def split_ref(ref):
    match = CELL_REF.match(ref)
    if match is None:
        raise ValueError(f"Unexpected cell reference: {ref}")
    return match.group("column"), int(match.group("row"))


def find_header_row(cells):
    """The row that declares the total column, and that column's letter."""
    for ref, cell in cells.items():
        if isinstance(cell["value"], str) and cell["value"].strip() == TOTAL_HEADER:
            column, row = split_ref(ref)
            return row, column
    raise ValueError(f"No {TOTAL_HEADER!r} header in this sheet")


def analyse(workbook_path):
    archive = zipfile.ZipFile(workbook_path)
    shared = _shared_strings(archive)
    for name, part in _worksheet_parts(archive).items():
        cells = read_sheet(archive, part, shared)
        try:
            header_row, total_column = find_header_row(cells)
        except ValueError:
            continue
        return _analyse_sheet(workbook_path, name, cells, header_row, total_column)
    raise SystemExit(f"{workbook_path}: no sheet declares a {TOTAL_HEADER!r} column")


def _analyse_sheet(workbook_path, sheet_name, cells, header_row, total_column):
    counted_columns = {}
    for ref, cell in cells.items():
        column, row = split_ref(ref)
        if row != header_row or not isinstance(cell["value"], str):
            continue
        match = CLASS_HEADER.match(cell["value"].strip())
        if match:
            counted_columns[column] = (match.group("group"), match.group("vehicle"))

    included = {c: h for c, h in counted_columns.items() if h[1] != EXCLUDED_VEHICLE}
    if not included:
        raise SystemExit(f"{workbook_path}: no per-class columns found on sheet {sheet_name!r}")

    per_column = {column: 0 for column in included}
    negatives = []
    rows_with_data = 0
    for row in range(header_row + 1, max(split_ref(ref)[1] for ref in cells) + 1):
        values = {}
        for column in included:
            cell = cells.get(f"{column}{row}")
            if cell is None or cell["value"] is None:
                continue
            values[column] = int(float(cell["value"]))
        if not values:
            continue
        rows_with_data += 1
        for column, value in values.items():
            per_column[column] += value
            if value < 0:
                group, vehicle = included[column]
                negatives.append({"cell": f"{column}{row}", "column": f"{group}_{vehicle}",
                                  "value": value})

    total = sum(per_column.values())

    # The workbook's own cached sums, for a like-for-like cross-check.
    stored_total = None
    minutes = None
    for row in range(1, header_row):
        cell = cells.get(f"{total_column}{row}")
        if cell is None or cell["value"] is None:
            continue
        if cell["formula"] and cell["formula"].upper().startswith("SUM("):
            stored_total = int(float(cell["value"]))
        elif cell["formula"]:
            match = PER_HOUR_FORMULA.search(cell["formula"])
            if match:
                minutes = float(match.group("minutes"))
    if stored_total is None:
        raise SystemExit(f"{workbook_path}: the {TOTAL_HEADER!r} column stores no SUM total")
    if minutes is None:
        raise SystemExit(f"{workbook_path}: no '* 60 / minutes' rate formula above the total column")

    by_group = {}
    for column, count in per_column.items():
        group = included[column][0]
        by_group[group] = by_group.get(group, 0) + count

    return {
        "workbook": _repo_relative(workbook_path),
        "sheet": sheet_name,
        "counted_classes": sorted({included[c][1] for c in included}),
        "excluded_class": EXCLUDED_VEHICLE,
        "rows_with_data": rows_with_data,
        "per_column": {f"{included[c][0]}_{included[c][1]}": per_column[c]
                       for c in sorted(per_column)},
        "by_group": by_group,
        "total_veh": total,
        "workbook_total_veh": stored_total,
        "survey_minutes": minutes,
        "capacity_veh_h": total * 60.0 / minutes,
        # The sheet divides by its formula's minutes even though some one-minute
        # rows are empty; the mean over the rows that do hold data is reported
        # alongside so the effect of that denominator choice is visible.
        "rate_over_rows_with_data_veh_h": total * 60.0 / rows_with_data,
        "negative_cells": sorted(negatives, key=lambda n: n["cell"]),
        "negative_net_veh": sum(n["value"] for n in negatives),
    }


def format_report(result):
    lines = [
        f"workbook            {result['workbook']}  (sheet {result['sheet']!r})",
        f"counted classes     {', '.join(result['counted_classes'])}"
        f"   [excluded: {result['excluded_class']}]",
        f"one-minute rows     {result['rows_with_data']}",
    ]
    for name in sorted(result["per_column"]):
        lines.append(f"  {name:<28}{result['per_column'][name]:>8}")
    for name in sorted(result["by_group"]):
        lines.append(f"  subtotal {name:<19}{result['by_group'][name]:>8}")
    lines += [
        f"total               {result['total_veh']} veh"
        f"   (workbook stores {result['workbook_total_veh']})",
        f"survey duration     {result['survey_minutes']:g} min (from the workbook formula)",
        f"capacity            {result['capacity_veh_h']:.4f} veh/h"
        f"   (total / {result['survey_minutes']:g} min, as the workbook does)",
        f"mean over data rows {result['rate_over_rows_with_data_veh_h']:.4f} veh/h"
        f"   (total / {result['rows_with_data']} rows that hold data)",
    ]
    if result["negative_cells"]:
        cells = ", ".join(f"{n['cell']}={n['value']}" for n in result["negative_cells"])
        lines.append(f"negative entries    {cells}"
                     f"  (net {result['negative_net_veh']} veh)")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workbook", type=Path,
                        default=ROOT / "data" / "counts" / "peak_merge.xlsx")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)
    result = analyse(args.workbook)
    print(json.dumps(result, indent=2) if args.json else format_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
