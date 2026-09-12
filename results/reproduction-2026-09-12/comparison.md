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

The numerical disagreement remains unresolved. No thresholds or demand inputs were tuned to match the old table.
See ../../docs/REPRODUCTION.md for provenance, input equivalence, simulator version and the legacy metric definitions.
