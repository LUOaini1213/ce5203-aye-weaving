import sys
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "sumo"))
from control import Controller, Parameters, gap_occupancy, hysteresis
from metrics import legacy_metrics


class ControlTests(unittest.TestCase):
    def test_hysteresis_keeps_state_inside_band_and_at_boundaries(self):
        self.assertTrue(hysteresis(False, 0.21, 0.20, 0.7))
        self.assertTrue(hysteresis(True, 0.17, 0.20, 0.7))
        self.assertFalse(hysteresis(False, 0.17, 0.20, 0.7))
        self.assertFalse(hysteresis(True, 0.13, 0.20, 0.7))
        self.assertFalse(hysteresis(False, 0.20, 0.20, 0.7))
        self.assertTrue(hysteresis(True, 0.20 * 0.7, 0.20, 0.7))

    def test_gap_occupancy_counts_gaps_and_clips_each_lane_before_averaging(self):
        api = SimpleNamespace(
            lane=SimpleNamespace(getLength=lambda lane: 10,
                                 getLastStepVehicleIDs=lambda lane: ["a", "b"] if lane.endswith("_0") else []),
            vehicle=SimpleNamespace(getLength=lambda v: 5, getMinGap=lambda v: 2),
        )
        self.assertEqual(gap_occupancy(api), 0.25)  # capped 14/10 in one of four lanes

    def fake_api(self):
        actions = []
        api = SimpleNamespace(
            lane=SimpleNamespace(setMaxSpeed=lambda lane, speed: actions.append(("speed", lane, speed))),
            trafficlight=SimpleNamespace(
                Phase=lambda duration, state: (duration, state),
                Logic=lambda name, kind, phase, phases: (name, phases),
                setProgramLogic=lambda name, logic: actions.append(("logic", name, logic)),
                setProgram=lambda name, program: actions.append(("program", name, program)),
            ),
        )
        return api, actions

    def test_combined_upstream_actuators_and_release_restore_original_program(self):
        api, actions = self.fake_api()
        controller = Controller("vsl_up_rm", Parameters())
        self.assertEqual(controller.update(api, 0.30), ["vsl_on", "rm_on"])
        speeds = [a for a in actions if a[0] == "speed"]
        self.assertEqual(speeds, [("speed", f"E_main_in_{i}", 12.0) for i in range(3)])
        self.assertIn(("logic", "tls_node", ("metered", [(4.0, "G"), (2.0, "y"), (8.0, "r")])), actions)
        actions.clear()
        self.assertEqual(controller.update(api, 0.16), [])  # retain both; do not restart signal cycle
        self.assertEqual(actions, [])
        self.assertEqual(controller.update(api, 0.05), ["vsl_off", "rm_off"])
        self.assertIn(("program", "tls_node", "0"), actions)
        self.assertEqual([a[2] for a in actions if a[0] == "speed"], [25.0] * 3)

    def test_base_never_changes_actuators_even_when_congested(self):
        api, actions = self.fake_api()
        self.assertEqual(Controller("base", Parameters()).update(api, 1.0), [])
        self.assertEqual(actions, [])

    def test_in_section_controls_only_weaving_lane_zero(self):
        api, actions = self.fake_api()
        Controller("vsl", Parameters()).update(api, 0.30)
        self.assertEqual(actions, [("speed", "E_weaving_0", 12.0)])

    def test_invalid_fraction_and_nonintegral_control_step_rejected(self):
        for params in (Parameters(rm_threshold=20), Parameters(step=0.7), Parameters(release_ratio=1)):
            with self.assertRaises(ValueError):
                params.validate()

    def test_legacy_summary_reads_edge_observations_without_historical_table(self):
        xml = ('<meandata><interval begin="0" end="60">'
               '<edge id="E_weaving" density="100" speed="12.5" traveltime="30" '
               'sampledSeconds="120" waitingTime="4" timeLoss="25"/>'
               '<edge id="E_main_out" density="10" speed="20" timeLoss="5"/>'
               '</interval></meandata>')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "edges.xml"
            path.write_text(xml, encoding="utf-8")
            result = legacy_metrics(path, Parameters(), 2, 2)
        self.assertEqual(result["net_total_timeloss_veh_s"], 30)
        self.assertEqual(result["avg_net_delay_s_veh"], 15)
        self.assertEqual(result["avg_delay_s_veh"], 15.08)
        self.assertEqual(result["avg_time_in_queue_s_veh"], 2)
        self.assertEqual(result["capacity_veh_h"], 720)


if __name__ == "__main__":
    unittest.main()
