#!/usr/bin/env python3
"""Validate a real 12-scenario run, including recorded actions and raw output hashes."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from control import SCENARIOS


def check_run(output, require_complete=False):
    output = Path(output)
    manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    if manifest["status"] != "complete" or manifest["completed"] != 12:
        raise ValueError("A completed twelve-scenario run is required")
    checked = []
    for period in ("peak", "offpeak"):
        for scenario in SCENARIOS:
            folder = output / f"{period}_{scenario}"
            metrics = json.loads((folder / "metrics.json").read_text(encoding="utf-8"))
            provenance = json.loads((folder / "provenance.json").read_text(encoding="utf-8"))
            if metrics["departed"] <= 0 or metrics["arrived"] <= 0:
                raise ValueError(f"No actual traffic simulated: {folder.name}")
            if metrics["tripinfo_completed"] != metrics["arrived"]:
                raise ValueError(f"Trip output disagrees with TraCI arrivals: {folder.name}")
            if require_complete and (not metrics["completed_demand"] or metrics["departed"] != metrics["arrived"]):
                raise ValueError(f"Demand unfinished: {folder.name}")
            if scenario.startswith("vsl") and metrics["vsl_activation_count"] < 1:
                raise ValueError(f"VSL was never activated: {folder.name}")
            if "rm" in scenario and metrics["rm_activation_count"] < 1:
                raise ValueError(f"Ramp meter was never activated: {folder.name}")
            if scenario == "base" and (metrics["vsl_activation_count"] or metrics["rm_activation_count"]):
                raise ValueError(f"Base case applied a control: {folder.name}")
            with (folder / "control_trace.csv").open(encoding="utf-8", newline="") as handle:
                events = list(csv.DictReader(handle))
            if "rm" in scenario and not any(e["signal_program"] == "metered" for e in events):
                raise ValueError(f"No SUMO metered programme observed: {folder.name}")
            if scenario.startswith("vsl"):
                expected = "E_main_in_0;E_main_in_1;E_main_in_2" if "up" in scenario else "E_weaving_0"
                if not all(e["vsl_lanes"] == expected for e in events):
                    raise ValueError(f"Wrong VSL placement: {folder.name}")
            for filename, digest in provenance["artifact_sha256"].items():
                actual = hashlib.sha256((folder / filename).read_bytes()).hexdigest()
                if actual != digest:
                    raise ValueError(f"Artifact hash mismatch: {folder.name}/{filename}")
            if not any((folder / name).is_file() for name in ("edge_data_output.xml", "edge_data_output.xml.gz")):
                raise ValueError(f"Raw edge output missing: {folder.name}")
            checked.append(folder.name)
    return checked


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    print(f"PASS: {len(check_run(args.output, args.require_complete))} real scenarios, controls, trip counts and artifact hashes")
