# Recovered twelve-scenario SUMO runner

The control runner was recovered on **12 September 2026** from the original
course submission archive, `CE5203_Group12_Submission_FINAL.zip`, entry
`code/run_scenario.py`. The earlier README correctly described what was then
published, but the runner was still present inside that local archive. The
portable implementation under `scripts/sumo/` restores its actual control
rules. This is a recovery and new execution, not a newly invented controller
or a claim that the historical table has now been reproduced exactly.

The archived Python file has SHA-256:

```text
0b1ea5bf3609698c4c20063a3e61a2f05d8c3c4edf774164034292325cca8402
```

Both network files are byte-identical between the archive and this repository.
Both route files differ in whitespace but have identical XML element order,
tags and attributes. The archived and repository demand counts are **4,493
vehicles peak and 5,496 off-peak**. No private videos, student IDs, or group
report PDFs are needed or published for this recovery.

## Run the six controls in both demand periods

Install Eclipse SUMO and its Python TraCI tools. SUMO **1.24.0**, Python 3.11,
and the socket TraCI backend were used for the committed Windows rerun. A
SUMO distribution usually includes TraCI under `$SUMO_HOME/tools`; a separate
installation can instead use `pip install traci`. No YOLO or report-rendering
dependencies are needed for the simulation runner.

```bash
# SUMO on PATH, or SUMO_HOME pointing at its installation
python scripts/sumo/run_scenarios.py --all --jobs 2 --output runs/full --compress-xml
python scripts/sumo/check_run.py runs/full --require-complete
python scripts/sumo/compare_history.py runs/full
```

If SUMO is not on PATH, append `--sumo-binary /path/to/sumo` (on Windows,
`--sumo-binary D:/SUMO/bin/sumo.exe`, for example). Set `--sumo-home` if the
tools directory cannot be inferred. Each simulation uses its own process and
output directory. Existing output directories are refused. Neither the
historical `results/sumo_12scenarios_results.csv` nor the original `sumo/`
outputs are overwritten.

The default matrix is:

| Scenario | Speed control | Ramp signal |
|---|---|---|
| `base` | Original limits | Original programme |
| `vsl` | `E_weaving_0` | Original programme |
| `vsl_up` | All three `E_main_in` lanes | Original programme |
| `rm` | Original limits | Feedback metering |
| `vsl_rm` | `E_weaving_0` | Feedback metering |
| `vsl_up_rm` | All three `E_main_in` lanes | Feedback metering |

For a single run, use `--period peak --scenario rm`. Other exposed inputs are
`--end`, `--step`, `--seed`, `--vsl-threshold` and `--rm-threshold`; all values
are recorded in the run manifest and per-scenario provenance. The remaining
archived constants are explicit in `control.Parameters`.

## Recovered rules, fixed before the new run

- Step **0.5 s**, seed **42**, horizon **5,400 s**, lateral resolution **0.8 m**,
  time-to-teleport **120 s**. The published standalone `.sumocfg` files use
  0.1 s; the archived scenario runner explicitly overrides this to 0.5 s.
  This portable runner follows that scenario code.
- Occupancy is the mean across the four weaving lanes of
  `min(1, sum(vehicle.length + vehicle.minGap) / lane.length)`.
  It is **not** the induction-loop percentage, SUMO's occupancy getter, or a
  measured real-world detector value. Changing the definition changes when
  controls trigger, so this distinction is part of the recovered contract.
- Check every **30 s**. VSL activates above **0.15**, reduces the selected
  lanes to **12 m/s**, and restores **25 m/s** below **0.105**. Values in the
  hysteresis band retain state.
- RM activates above **0.20**, installing **4 s green / 2 s yellow / 8 s red**.
  It returns to original programme `0` (**81 G / 4 y / 5 r**) below **0.14**.
  This is the archive's two-state approximation, not a continuous ALINEA
  gain/rate controller. Four seconds of green does not guarantee exactly
  one departing vehicle; actual movements come from SUMO.
- The original code steps first and then uses `step * dt` as its control
  clock. That one-step offset is preserved: the first check occurs at actual
  simulation time **0.5 s**, then 30.5 s, etc. Both clocks are logged.
- End when demand clears or the configured horizon is reached, as the archive
  did. Incomplete demand is explicitly flagged instead of called a completed
  experiment.

Portability changes are argument parsing, path discovery, output isolation,
process parallelism, explicit failure records and added measurements. No
thresholds were searched to obtain the reported historical improvement.

## What is saved

Each `period_scenario/` directory contains:

- `scenario.sumocfg` and `additional.add.xml`: the actual configuration;
- `control_trace.csv`: occupancy, control state, transitions, selected lanes,
  speed command and the observed SUMO traffic-light programme every 30 s;
- `edge_data_output.xml[.gz]`, six detector outputs and `tripinfo.xml[.gz]`:
  raw simulator observations;
- `legacy_summary.csv` and `metrics.json`: metrics computed from this run's
  XML, plus arrivals, unfinished demand, teleports, collision events and
  activation counts;
- `provenance.json`: parameters, Python/SUMO versions, input SHA-256 hashes,
  network lane lengths and raw/derived artifact hashes;
- `warnings.log`, `sumo.log` and `stdout.log`: runtime evidence, including
  emergency-braking warnings rather than silently hiding them.

The top-level manifest records code hashes and completion status. `summary.csv`
is updated as each scenario completes. `check_run.py` verifies actual traffic,
VSL/RM activation, signal programme, lane placement, trip counts and artifact
hashes. A result table alone is insufficient to pass it. `compare_history.py`
only reads the historical table **after** the simulation, to display differences.

## Metric definitions and limitations

The old-column names in `legacy_summary.csv` are preserved to compare the
archived formulas, but their interpretation has limitations:

- `capacity_veh_h` is the maximum interval sum of `density × speed` on the
  downstream mainline and off-ramp; `throughput_veh_h` is its interval mean.
  These are **flow proxies**, not vehicle-count throughput or a separately
  estimated physical capacity.
- Delay and queue summaries are unweighted means over available 60-second
  edge intervals. The queue is a density/speed proxy. They are not direct
  per-vehicle delay/queue measurements.
- `avg_time_in_queue_s_veh` divides interval waiting seconds by
  `sampledSeconds / 60`, as the archive did. It is a proxy normalized by
  average vehicle presence, not a true mean across individual trip records.
- The archived calculations use **373.01 m** as the weaving length; the
  shipped network's four weaving lanes are **357.32 m**. The original value
  is retained only for comparison. Measured lane lengths are included in
  provenance, and this difference must not be concealed.
- `net_total_timeloss_veh_s` sums the edgeData `timeLoss` fields. Additional
  `tripinfo_completed_*` metrics report completed-trip time loss, waiting and
  departure delay separately. They need not equal edge-interval summaries;
  incomplete trips, definitions and rounding differ.
- This is one fixed seed on one simulator version. It does not establish
  robustness across SUMO releases, operating systems or seeds, and is not a
  deployment result.

## New result versus the historical claim

Committed evidence: [12 September rerun](../results/reproduction-2026-09-12/summary.csv)
and [historical comparison](../results/reproduction-2026-09-12/comparison.md).
The rerun uses recovered controls with matching demand semantics, but **does
not numerically reproduce the historical table**. The difference remains
unresolved. The original environment was hardcoded to an unavailable Python
3.10/Linux libsumo installation; this run records SUMO 1.24.0 on Windows via
TraCI. That is a difference in provenance, **not a demonstrated explanation**
of the score gap.

As a separate refactoring check, the archived script was also executed for
peak `base` and `rm` on this machine, changing only its hardcoded SUMO path
and selecting its existing socket TraCI backend. Every legacy summary field
matches the portable runner for both scenarios, including **183,708.2** and
**82,697.5 veh-s** network time loss. This checks these two portable runs
against the recovered source; it does not recover the original environment
or explain the historical discrepancy. The field-by-field check is saved in
[`archive_runner_crosscheck.json`](../results/reproduction-2026-09-12/archive_runner_crosscheck.json).

The report's **−22.7% network time loss / −7.7% delay** remains a historical
reported result. It must not be presented as reproduced by this new run.
The new within-run comparison is in `comparison.md`; no historical result
has been overwritten or relabelled as the new measurement.

## Regression and CI

```bash
python -m unittest discover -s tests -v
python scripts/sumo/run_scenarios.py --all --end 120 --jobs 2 --vsl-threshold 0.01 --rm-threshold 0.01 --output runs/smoke --compress-xml
python scripts/sumo/check_run.py runs/smoke
```

The smoke run deliberately lowers both thresholds so the short traffic sample
activates every controller. **It is a software integration check, not a
performance experiment**. The full committed run uses the original 0.15/0.20
thresholds and completes all demand. CI runs the seven regression tests and
all twelve smoke scenarios, then uploads their raw outputs and control traces.
