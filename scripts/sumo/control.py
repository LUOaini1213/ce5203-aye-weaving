"""Control rules recovered from the course submission's run_scenario.py.

Occupancy deliberately includes vehicle minGap; this is not detector occupancy.
"""
from dataclasses import dataclass

SCENARIOS = ("base", "vsl", "vsl_up", "rm", "vsl_rm", "vsl_up_rm")
WEAVING_LANES = tuple(f"E_weaving_{i}" for i in range(4))


@dataclass(frozen=True)
class Parameters:
    end: float = 5400.0
    step: float = 0.5
    seed: int = 42
    control_period: float = 30.0
    vsl_threshold: float = 0.15
    rm_threshold: float = 0.20
    release_ratio: float = 0.7
    free_speed: float = 25.0
    vsl_speed: float = 12.0
    time_to_teleport: float = 120.0
    report_weaving_length: float = 373.01

    def validate(self):
        if self.end <= 0 or self.step <= 0 or self.control_period <= 0:
            raise ValueError("end, step and control_period must be positive")
        if abs(self.control_period / self.step - round(self.control_period / self.step)) > 1e-8:
            raise ValueError("control_period must be a multiple of step")
        if not (0 < self.vsl_threshold <= 1 and 0 < self.rm_threshold <= 1):
            raise ValueError("occupancy thresholds must be fractions in (0, 1]")
        if not 0 < self.release_ratio < 1:
            raise ValueError("release_ratio must be in (0, 1)")
        if not 0 < self.vsl_speed <= self.free_speed:
            raise ValueError("vsl_speed must be positive and no higher than free_speed")


def hysteresis(active, occupancy, threshold, release_ratio):
    if occupancy > threshold:
        return True
    if occupancy < threshold * release_ratio:
        return False
    return active


def gap_occupancy(api):
    """Mean lane occupancy using (vehicle length + minGap), as in the archive."""
    values = []
    for lane in WEAVING_LANES:
        occupied = sum(
            api.vehicle.getLength(v) + api.vehicle.getMinGap(v)
            for v in api.lane.getLastStepVehicleIDs(lane)
        )
        values.append(min(1.0, occupied / api.lane.getLength(lane)))
    return sum(values) / len(values)


class Controller:
    def __init__(self, scenario, params):
        if scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario}")
        self.scenario = scenario
        self.params = params
        self.has_vsl = scenario in ("vsl", "vsl_up", "vsl_rm", "vsl_up_rm")
        self.has_rm = scenario in ("rm", "vsl_rm", "vsl_up_rm")
        self.vsl_lanes = (
            tuple(f"E_main_in_{i}" for i in range(3))
            if scenario in ("vsl_up", "vsl_up_rm") else ("E_weaving_0",)
        )
        self.vsl_active = False
        self.rm_active = False

    def update(self, api, occupancy):
        p = self.params
        transitions = []
        if self.has_vsl:
            active = hysteresis(self.vsl_active, occupancy, p.vsl_threshold, p.release_ratio)
            if active != self.vsl_active:
                for lane in self.vsl_lanes:
                    api.lane.setMaxSpeed(lane, p.vsl_speed if active else p.free_speed)
                self.vsl_active = active
                transitions.append("vsl_on" if active else "vsl_off")
        if self.has_rm:
            active = hysteresis(self.rm_active, occupancy, p.rm_threshold, p.release_ratio)
            if active != self.rm_active:
                if active:
                    phases = [api.trafficlight.Phase(4.0, "G"),
                              api.trafficlight.Phase(2.0, "y"),
                              api.trafficlight.Phase(8.0, "r")]
                    logic = api.trafficlight.Logic("metered", 0, 0, phases)
                    api.trafficlight.setProgramLogic("tls_node", logic)
                    api.trafficlight.setProgram("tls_node", "metered")
                else:
                    api.trafficlight.setProgram("tls_node", "0")
                self.rm_active = active
                transitions.append("rm_on" if active else "rm_off")
        return transitions
