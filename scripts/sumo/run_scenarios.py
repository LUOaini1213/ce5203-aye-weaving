#!/usr/bin/env python3
"""Portable recovery of the course runner; outputs always go to a new directory."""
import argparse
import concurrent.futures
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from control import Controller, Parameters, SCENARIOS, gap_occupancy
from metrics import legacy_metrics, trip_metrics

ROOT = Path(__file__).resolve().parents[2]
ARCHIVED_RUNNER_SHA256 = "0b1ea5bf3609698c4c20063a3e61a2f05d8c3c4edf774164034292325cca8402"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    if rows:
        with Path(path).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def resolve_sumo(binary, home):
    home_path = Path(home or os.environ.get("SUMO_HOME", "")) if (home or os.environ.get("SUMO_HOME")) else None
    candidate = binary or (str(home_path / "bin" / ("sumo.exe" if os.name == "nt" else "sumo")) if home_path else "sumo")
    resolved = shutil.which(candidate)
    if not resolved:
        raise RuntimeError("SUMO binary not found; set SUMO_HOME or pass --sumo-binary")
    if home_path is None:
        home_path = Path(resolved).resolve().parents[1]
    return str(Path(resolved).resolve()), str(home_path.resolve())


def load_traci(home):
    tools = Path(home) / "tools"
    if tools.is_dir():
        sys.path.insert(0, str(tools))
    try:
        import traci
    except ImportError as exc:
        raise RuntimeError("TraCI not found; set SUMO_HOME to the SUMO distribution or pip install traci") from exc
    return traci


def prepare_inputs(out, period, params):
    source = ROOT / "sumo" / period
    additional = ET.Element("additional")
    detectors = (("main_in", "E_main_in_1"), ("weaving", "E_weaving_1"),
                 ("main_out", "E_main_out_1"), ("on_ramp", "E_on_ramp_1_0"),
                 ("off_ramp_0", "E_off_ramp_0"), ("off_ramp_1", "E_off_ramp_1"))
    for name, lane in detectors:
        ET.SubElement(additional, "inductionLoop", id=f"det_{name}", lane=lane,
                      pos="0", period="60", file=f"{name}.xml")
    ET.SubElement(additional, "edgeData", id="edge_dump", period="60",
                  file="edge_data_output.xml", excludeEmpty="true")
    ET.ElementTree(additional).write(out / "additional.add.xml", encoding="utf-8", xml_declaration=True)
    config = ET.Element("configuration")
    groups = {
        "input": {"net-file": os.path.relpath(source / "aye_bottleneck_net.xml", out).replace(os.sep, "/"),
                  "route-files": os.path.relpath(source / f"{period}_demand_rou.xml", out).replace(os.sep, "/"),
                  "additional-files": "additional.add.xml"},
        "time": {"begin": 0, "end": params.end, "step-length": params.step},
        "processing": {"lateral-resolution": 0.8, "collision.action": "warn",
                       "collision.mingap-factor": 0, "time-to-teleport": params.time_to_teleport},
        "report": {"verbose": "false", "no-step-log": "true", "log": "sumo.log", "error-log": "warnings.log"},
        "random_number": {"seed": params.seed},
        "output": {"tripinfo-output": "tripinfo.xml", "tripinfo-output.write-unfinished": "true"},
    }
    for group, values in groups.items():
        node = ET.SubElement(config, group)
        for key, value in values.items():
            ET.SubElement(node, key, value=str(value))
    ET.ElementTree(config).write(out / "scenario.sumocfg", encoding="utf-8", xml_declaration=True)
    return {str(path.relative_to(ROOT)).replace(os.sep, "/"): sha256(path)
            for path in (source / "aye_bottleneck_net.xml", source / f"{period}_demand_rou.xml")}


def run_one(task):
    period, scenario, output, binary, home, param_dict, compress = task
    params = Parameters(**param_dict)
    out = Path(output) / f"{period}_{scenario}"
    out.mkdir(parents=True, exist_ok=False)
    hashes = prepare_inputs(out, period, params)
    api = load_traci(home)
    controller = Controller(scenario, params)
    started = time.monotonic()
    departed = arrived = teleports = collision_vehicles = step = 0
    last_control = -1e9
    control_rows = []
    previous_dir = Path.cwd()
    old_sha = sha256(ROOT / "results" / "sumo_12scenarios_results.csv")
    os.chdir(out)
    connected = False
    try:
        with Path("stdout.log").open("w", encoding="utf-8") as stdout:
            api.start([binary, "-c", "scenario.sumocfg"], stdout=stdout)
            connected = True
            api_version, version = api.getVersion()
            lane_lengths = {f"E_weaving_{i}": api.lane.getLength(f"E_weaving_{i}") for i in range(4)}
            # Preserve the archive's timing: observe after stepping, label time as
            # step*dt (first action at simulation time 0.5, then 30.5, ...).
            while api.simulation.getMinExpectedNumber() > 0 and step * params.step < params.end:
                api.simulationStep()
                departed += api.simulation.getDepartedNumber()
                arrived += api.simulation.getArrivedNumber()
                teleports += api.simulation.getStartingTeleportNumber()
                collision_vehicles += api.simulation.getCollidingVehiclesNumber()
                control_time = step * params.step
                if control_time - last_control >= params.control_period - 1e-9:
                    last_control = control_time
                    occupancy = gap_occupancy(api)
                    transitions = controller.update(api, occupancy)
                    control_rows.append({
                        "simulation_time_s": round((step + 1) * params.step, 6),
                        "archive_control_time_s": round(control_time, 6),
                        "gap_occupancy": round(occupancy, 8),
                        "vsl_active": int(controller.vsl_active),
                        "rm_active": int(controller.rm_active),
                        "vsl_lanes": ";".join(controller.vsl_lanes) if controller.has_vsl else "",
                        "vsl_limit_m_s": params.vsl_speed if controller.vsl_active else params.free_speed,
                        "signal_program": api.trafficlight.getProgram("tls_node"),
                        "transitions": ";".join(transitions),
                    })
                step += 1
            remaining = api.simulation.getMinExpectedNumber()
            end_time = api.simulation.getTime()
            api.close()
            connected = False
        legacy = {"period": period, "scenario": scenario,
                  **legacy_metrics("edge_data_output.xml", params, departed, arrived)}
        summary = {
            **legacy, **trip_metrics("tripinfo.xml"),
            "completed_demand": remaining == 0,
            "remaining_expected": remaining,
            "simulation_end_s": end_time,
            "teleport_starts": teleports,
            "collision_vehicle_events": collision_vehicles,
            "vsl_activation_count": sum("vsl_on" in r["transitions"] for r in control_rows),
            "rm_activation_count": sum("rm_on" in r["transitions"] for r in control_rows),
            "wall_seconds": round(time.monotonic() - started, 3),
        }
        write_csv("control_trace.csv", control_rows)
        dump_json("metrics.json", summary)
        write_csv("legacy_summary.csv", [legacy])
        if compress:
            for xml in Path.cwd().glob("*.xml"):
                if xml.name == "additional.add.xml":
                    continue
                with xml.open("rb") as src, gzip.GzipFile(filename=str(xml) + ".gz", mode="wb", mtime=0) as dest:
                    shutil.copyfileobj(src, dest)
                xml.unlink()
        artifacts = {p.name: sha256(p) for p in Path.cwd().iterdir() if p.is_file()}
        dump_json("provenance.json", {
            "kind": "September 2026 rerun using recovered course control rules; not the historical result table",
            "archived_runner_sha256": ARCHIVED_RUNNER_SHA256,
            "parameters": param_dict, "sumo_version": version, "traci_api_version": api_version,
            "input_sha256": hashes, "network_weaving_lane_lengths_m": lane_lengths,
            "historical_csv_sha256": old_sha, "artifact_sha256": artifacts,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "python": sys.version.split()[0],
        })
        if old_sha != sha256(ROOT / "results" / "sumo_12scenarios_results.csv"):
            raise RuntimeError("Historical CSV changed during execution")
        return summary
    except Exception as exc:
        dump_json("FAILED.json", {"period": period, "scenario": scenario, "error": str(exc)})
        raise
    finally:
        if connected:
            api.close()
        os.chdir(previous_dir)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="run both periods and all six scenarios")
    parser.add_argument("--period", choices=("peak", "offpeak"), default="peak")
    parser.add_argument("--scenario", choices=SCENARIOS, default="base")
    parser.add_argument("--output", type=Path, help="new directory; existing paths are refused")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--sumo-binary")
    parser.add_argument("--sumo-home")
    parser.add_argument("--end", type=float, default=5400)
    parser.add_argument("--step", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--vsl-threshold", type=float, default=0.15)
    parser.add_argument("--rm-threshold", type=float, default=0.20)
    parser.add_argument("--compress-xml", action="store_true")
    args = parser.parse_args(argv)
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    params = Parameters(end=args.end, step=args.step, seed=args.seed,
                        vsl_threshold=args.vsl_threshold, rm_threshold=args.rm_threshold)
    params.validate()
    binary, home = resolve_sumo(args.sumo_binary, args.sumo_home)
    output = (args.output or ROOT / "runs" / datetime.now().strftime("%Y%m%d-%H%M%S")).resolve()
    if output.exists():
        parser.error(f"Output already exists; choose a new directory: {output}")
    output.mkdir(parents=True)
    pairs = [(p, s) for p in ("peak", "offpeak") for s in SCENARIOS] if args.all else [(args.period, args.scenario)]
    tasks = [(p, s, str(output), binary, home, asdict(params), args.compress_xml) for p, s in pairs]
    dump_json(output / "run_manifest.json", {
        "status": "running", "scenario_count": len(tasks), "parameters": asdict(params),
        "runner_sha256": sha256(__file__),
        "control_sha256": sha256(Path(__file__).with_name("control.py")),
        "metrics_sha256": sha256(Path(__file__).with_name("metrics.py")),
    })
    summaries = []
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.jobs) as pool:
            futures = {pool.submit(run_one, task): task[:2] for task in tasks}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                summaries.append(result)
                summaries.sort(key=lambda r: pairs.index((r["period"], r["scenario"])))
                write_csv(output / "summary.csv", summaries)
                print(json.dumps({"finished": f"{result['period']}_{result['scenario']}",
                                  "arrived": result["arrived"], "vsl_on": result["vsl_activation_count"],
                                  "rm_on": result["rm_activation_count"], "wall_s": result["wall_seconds"]}), flush=True)
        manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
        manifest.update(status="complete", completed=len(summaries), all_demand_completed=all(r["completed_demand"] for r in summaries))
        dump_json(output / "run_manifest.json", manifest)
    except Exception as exc:
        manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
        manifest.update(status="failed", completed=len(summaries), error=str(exc))
        dump_json(output / "run_manifest.json", manifest)
        raise
    print(f"Results: {output}")


if __name__ == "__main__":
    main()
