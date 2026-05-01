"""九天 v0.1 功能模拟器基础测试。

本文件覆盖原始最小 ISA/内存/同步能力；长期记忆高层任务的测试放在
test_long_term_memory.py。两组测试共同保证新增长期记忆语义不会破坏
copy_add、cluster barrier、capability trap 等基础行为。
"""

import json
import unittest
from pathlib import Path

from jiutian_sim import SimTrap, run_ir


ROOT = Path(__file__).resolve().parent


class SimulatorTests(unittest.TestCase):
    """基础模拟器行为测试。"""

    def load_example(self, name: str):
        """从 simulator/examples 读取 JSON IR。"""

        return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))

    def test_copy_add(self):
        """验证最小 DMA + load/add/store 流程。

        copy_add.json 把 host 输入搬到 SPM，加一后写回 host 输出区。
        """

        result = run_ir(self.load_example("copy_add.json"))
        self.assertEqual(result["host_words"]["8"], 42)
        self.assertEqual(result["tasks"][0]["status"], "completed")

    def test_cluster_barrier(self):
        """验证两个 task 通过 cluster SRAM 和 barrier 交接数据。"""

        result = run_ir(self.load_example("cluster_barrier.json"))
        self.assertEqual(result["host_words"]["16"], 12)
        self.assertEqual([task["status"] for task in result["tasks"]], ["completed", "completed"])
        self.assertTrue(any("barrier stage0 release" in item for item in result["trace"]))

    def test_capability_violation(self):
        """验证 host capability 越界会触发 SimTrap。"""

        ir = self.load_example("copy_add.json")
        ir["tasks"][0]["program"][0]["src"] = 16
        with self.assertRaises(SimTrap):
            run_ir(ir)

    def test_barrier_deadlock(self):
        """验证 barrier 参与者不足时调度器会报告 deadlock。"""

        ir = self.load_example("cluster_barrier.json")
        ir["barriers"][0]["participants"] = 3
        with self.assertRaises(SimTrap):
            run_ir(ir)


if __name__ == "__main__":
    unittest.main()
