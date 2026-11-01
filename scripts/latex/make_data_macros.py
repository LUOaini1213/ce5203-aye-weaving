#!/usr/bin/env python3
"""Generate latex/data_macros.tex from the historical twelve-scenario table.

`report.tex` pulls every number through these macros, so they are the join
between the LaTeX source and `results/sumo_12scenarios_results.csv`. The file
called itself auto-generated while no generator was published; this is it.

    python scripts/latex/make_data_macros.py --check   # CI: fail if it drifted
    python scripts/latex/make_data_macros.py           # rewrite the file

`--check` is what `tests/test_documented_numbers.py` asserts, so a hand-edited
macro or an edited CSV row turns the test suite red instead of silently
changing the report.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_CSV = ROOT / "results" / "sumo_12scenarios_results.csv"
TARGET = ROOT / "latex" / "data_macros.tex"

HEADER = ("% Auto-generated from results/sumo_12scenarios_results.csv\n"
          "% by scripts/latex/make_data_macros.py -- do not edit by hand.\n")

PERIOD_PREFIX = (("peak", "dP"), ("offpeak", "dO"))
SCENARIO_SUFFIX = (("base", "Base"), ("vsl", "Vsl"), ("vsl_up", "VslUp"),
                   ("rm", "Rm"), ("vsl_rm", "VslRm"), ("vsl_up_rm", "VslUpRm"))
METRIC_SUFFIX = (
    ("capacity_veh_h", "Cap"),
    ("throughput_veh_h", "Thr"),
    ("avg_delay_s_veh", "Delay"),
    ("peak_delay_s_veh", "PkDelay"),
    ("avg_queue_veh", "Queue"),
    ("peak_queue_veh", "PkQueue"),
    ("avg_time_in_queue_s_veh", "TimeQ"),
    ("avg_excess_acc_veh", "ExcAcc"),
    ("peak_excess_acc_veh", "PkExcAcc"),
    ("net_total_timeloss_veh_s", "TimeLoss"),
    ("avg_speed_weaving_kmh", "Speed"),
    ("avg_net_delay_s_veh", "NetDelay"),
)


def load_rows(csv_path=SOURCE_CSV):
    with Path(csv_path).open(encoding="utf-8", newline="") as handle:
        rows = {(r["period"], r["scenario"]): r for r in csv.DictReader(handle)}
    missing = [(p, s) for p, _ in PERIOD_PREFIX for s, _ in SCENARIO_SUFFIX
               if (p, s) not in rows]
    if missing:
        raise ValueError(f"Missing rows in {csv_path}: {missing}")
    return rows


def render(rows):
    """The exact text of data_macros.tex, values copied verbatim from the CSV."""
    lines = [HEADER]
    for period, prefix in PERIOD_PREFIX:
        for scenario, scenario_suffix in SCENARIO_SUFFIX:
            row = rows[(period, scenario)]
            for column, metric_suffix in METRIC_SUFFIX:
                name = f"{prefix}{scenario_suffix}{metric_suffix}"
                lines.append(f"\\newcommand{{\\{name}}}{{{row[column]}}}\n")
    return "".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", type=Path, default=SOURCE_CSV)
    parser.add_argument("--output", type=Path, default=TARGET)
    parser.add_argument("--check", action="store_true",
                        help="do not write; fail if the file is out of date")
    args = parser.parse_args(argv)

    expected = render(load_rows(args.csv))
    if args.check:
        try:
            current = args.output.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"MISSING: {args.output}", file=sys.stderr)
            return 1
        if current != expected:
            print(f"STALE: {args.output} does not match {args.csv}", file=sys.stderr)
            return 1
        print(f"OK: {args.output.name} matches {args.csv.name}")
        return 0
    args.output.write_text(expected, encoding="utf-8", newline="\n")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
