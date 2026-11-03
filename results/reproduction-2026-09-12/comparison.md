# Historical report versus the recovered runner

New values are a fresh SUMO run. Historical values are retained unchanged; agreement is not an acceptance criterion.

| Period | Scenario | Historical network time loss (veh-s) | New network time loss (veh-s) | New vs historical |
|---|---|---:|---:|---:|
| peak | base | 143,396.6 | 183,708.2 | +28.11% |
| peak | vsl | 173,427.1 | 192,840.8 | +11.19% |
| peak | vsl_up | 142,331.4 | 184,815.0 | +29.85% |
| peak | rm | 110,833.5 | 82,697.5 | -25.39% |
| peak | vsl_rm | 173,335.5 | 189,317.3 | +9.22% |
| peak | vsl_up_rm | 123,997.1 | 102,461.3 | -17.37% |
| offpeak | base | 89,050.3 | 130,361.1 | +46.39% |
| offpeak | vsl | 167,590.0 | 182,911.5 | +9.14% |
| offpeak | vsl_up | 99,602.3 | 122,339.8 | +22.83% |
| offpeak | rm | 86,585.3 | 83,313.7 | -3.78% |
| offpeak | vsl_rm | 140,242.1 | 121,888.2 | -13.09% |
| offpeak | vsl_up_rm | 107,329.5 | 105,287.6 | -1.90% |

## Ramp-metering effect within each run

| Period | Historical RM vs base | New RM vs base |
|---|---:|---:|
| peak | -22.71% | -54.98% |
| offpeak | -2.77% | -36.09% |

## New run: edge time loss plus entry delay

The table above, like the historical one, counts only time lost on modelled edges. Vehicles held before entry (ramp metering's queue) appear in tripinfo `departDelay` instead. Rank 1 is the lowest of the six strategies in that period. This is one run with one seed; the seed and simulator version are in run_manifest.json and each provenance.json.

| Period | Scenario | Edge time loss (veh-s) | Entry delay (veh-s) | Edge + entry (veh-s) | Edge vs base | Edge + entry vs base | Rank, edge | Rank, edge + entry |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| peak | base | 183,708.2 | 645,635.7 | 829,343.9 | +0.00% | +0.00% | 3 | 2 |
| peak | vsl | 192,840.8 | 1,336,566.7 | 1,529,407.5 | +4.97% | +84.41% | 6 | 5 |
| peak | vsl_up | 184,815.0 | 595,833.7 | 780,648.7 | +0.60% | -5.87% | 4 | 1 |
| peak | rm | 82,697.5 | 868,079.7 | 950,777.2 | -54.98% | +14.64% | 1 | 4 |
| peak | vsl_rm | 189,317.3 | 1,391,122.2 | 1,580,439.5 | +3.05% | +90.57% | 5 | 6 |
| peak | vsl_up_rm | 102,461.3 | 829,655.7 | 932,117.0 | -44.23% | +12.39% | 2 | 3 |
| offpeak | base | 130,361.1 | 86,202.4 | 216,563.5 | +0.00% | +0.00% | 5 | 2 |
| offpeak | vsl | 182,911.5 | 688,559.9 | 871,471.4 | +40.31% | +302.41% | 6 | 5 |
| offpeak | vsl_up | 122,339.8 | 66,550.4 | 188,890.2 | -6.15% | -12.78% | 4 | 1 |
| offpeak | rm | 83,313.7 | 439,107.9 | 522,421.6 | -36.09% | +141.23% | 1 | 3 |
| offpeak | vsl_rm | 121,888.2 | 1,055,045.4 | 1,176,933.6 | -6.50% | +443.46% | 3 | 6 |
| offpeak | vsl_up_rm | 105,287.6 | 711,373.9 | 816,661.5 | -19.23% | +277.10% | 2 | 4 |

peak: lowest edge time loss `rm`; lowest edge + entry `vsl_up`.

offpeak: lowest edge time loss `rm`; lowest edge + entry `vsl_up`.

The numerical disagreement remains unresolved. No thresholds or demand inputs were tuned to match the old table.
See ../../docs/REPRODUCTION.md for provenance, input equivalence, simulator version and the legacy metric definitions.
