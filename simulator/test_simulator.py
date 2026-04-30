import json
import unittest
from pathlib import Path

from jiutian_sim import SimTrap, run_ir


ROOT = Path(__file__).resolve().parent


class SimulatorTests(unittest.TestCase):
    def load_example(self, name: str):
        return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))

    def test_copy_add(self):
        result = run_ir(self.load_example("copy_add.json"))
        self.assertEqual(result["host_words"]["8"], 42)
        self.assertEqual(result["tasks"][0]["status"], "completed")

    def test_cluster_barrier(self):
        result = run_ir(self.load_example("cluster_barrier.json"))
        self.assertEqual(result["host_words"]["16"], 12)
        self.assertEqual([task["status"] for task in result["tasks"]], ["completed", "completed"])
        self.assertTrue(any("barrier stage0 release" in item for item in result["trace"]))

    def test_capability_violation(self):
        ir = self.load_example("copy_add.json")
        ir["tasks"][0]["program"][0]["src"] = 16
        with self.assertRaises(SimTrap):
            run_ir(ir)

    def test_barrier_deadlock(self):
        ir = self.load_example("cluster_barrier.json")
        ir["barriers"][0]["participants"] = 3
        with self.assertRaises(SimTrap):
            run_ir(ir)


if __name__ == "__main__":
    unittest.main()
