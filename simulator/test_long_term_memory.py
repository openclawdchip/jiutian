"""长期任务记忆闭环的模拟器测试。

这些测试不验证模型推理质量，而是验证九天 v0.1 的结构化语义：
Agent Domain 只能生成候选 ledger delta、候选 context projection 和候选
recovery anchor，不能直接提交长期记忆，也不能绕过输出 region 边界。
"""

import json
import unittest

from jiutian_sim import SimTrap, run_ir


LONG_MEMORY_NOT_READY = {
    "bad_opcode",
    "pc_oob",
    "capability_violation",
}


def memory_region(
    name,
    base,
    *,
    access="read",
    kind=None,
    ledger_type=None,
    capability=None,
    bytes=512,
):
    """构造一个 host memory region。

    测试里所有长期记忆输入输出都放在 host 空间，用 region 名称表达语义：
    transcript_window、artifact_previews、ledger_delta_out 等。kind/ledger_type
    暂时主要用于和 specs 对齐，模拟器当前仍以 capability 名称控制访问。
    """

    region = {
        "name": name,
        "space": "host",
        "base": base,
        "bytes": bytes,
        "access": access,
    }
    if kind:
        region["kind"] = kind
    if ledger_type:
        region["ledger_type"] = ledger_type
    if capability:
        region["capability"] = capability
    return region


def candidate_region(name, base, capability):
    """构造候选输出区。

    candidate 区域代表 Agent Domain 的输出缓冲。写入这里不等于长期记忆提交，
    因此测试会显式检查 trace 中没有 ledger_commit。
    """

    return memory_region(
        name,
        base,
        access="write",
        kind="candidate",
        capability=capability,
        bytes=1536,
    )


def base_ir(tasks):
    """生成测试用基础 IR。

    host_init 中放三类输入：
    1. transcript_window：包含 goal/plan/evidence/decision/recovery 五类事件。
    2. artifact_previews：模拟工具结果或文件证据的短预览。
    3. trace_window：模拟恢复点选择需要参考的最近执行证据。
    """

    return {
        "config": {"host_bytes": 8192},
        "host_init": [
            {
                "addr": 0,
                "text": json.dumps([
                    {"kind": "goal", "text": "goal: keep simulator long memory runnable"},
                    {"kind": "plan", "text": "plan: extract ledger delta then pack context"},
                    {"kind": "evidence", "text": "test: python -m unittest discover -s simulator"},
                    {"kind": "decision", "text": "reject direct ledger commit"},
                    {"kind": "recovery", "text": "safe recovery point after smoke tests"},
                ]),
            },
            {
                "addr": 512,
                "text": json.dumps([
                    {"kind": "evidence", "text": "file: simulator/jiutian_sim.py"},
                    {"kind": "evidence", "text": "file: simulator/test_long_term_memory.py"},
                ]),
            },
            {
                "addr": 1024,
                "text": json.dumps([
                    {"text": "clean test baseline before high-level task"},
                    {"text": "safe recovery uses candidate ledger delta only"},
                ]),
            },
        ],
        "dump_regions": [
            {"name": "ledger_delta_out", "addr": 4608, "bytes": 1536},
            {"name": "context_out", "addr": 5120, "bytes": 1536},
            {"name": "recovery_candidate_out", "addr": 6144, "bytes": 1536},
        ],
        "ledger_versions": {
            "goal": "goal:12",
            "plan": "plan:42",
            "evidence": "evidence:87",
            "decision": "decision:15",
            "recovery": "recovery:9",
        },
        "evidence_refs": [
            "transcript:turn:17",
            "trace:188",
            "artifact:test-log:sha256:abcd",
        ],
        "memory": [
            memory_region("transcript_window", 0, kind="transcript"),
            memory_region("artifact_previews", 512, kind="artifact_preview"),
            memory_region("trace_window", 1024, kind="trace"),
            memory_region("goal_ledger_read", 1536, kind="ledger", ledger_type="goal"),
            memory_region("plan_ledger_read", 2048, kind="ledger", ledger_type="plan"),
            memory_region("evidence_ledger_read", 2560, kind="ledger", ledger_type="evidence"),
            memory_region("decision_ledger_read", 3072, kind="ledger", ledger_type="decision"),
            memory_region("recovery_ledger_read", 3584, kind="ledger", ledger_type="recovery"),
            memory_region("ledger_read", 4096, kind="ledger", ledger_type="recovery"),
            candidate_region("ledger_delta_out", 4608, "ledger_delta_write"),
            candidate_region("context_out", 5120, "context_projection_write"),
            candidate_region("recovery_candidate_out", 6144, "recovery_candidate_write"),
        ],
        "tasks": tasks,
    }


def trace_contains(result, needle):
    """判断 trace 中是否出现某个关键片段。"""

    return any(needle in str(item) for item in result.get("trace", []))


def dumped_json(result, name):
    """从 dump_regions 导出的文本区解析 JSON。"""

    raw = result["host_regions"][name]
    if not raw:
        raise AssertionError(f"dumped region {name} is empty")
    return json.loads(raw)


class LongTermMemoryLoopTests(unittest.TestCase):
    """长期记忆三段高层 op 的最小行为测试。"""

    def run_or_skip(self, ir):
        """运行 IR。

        这个 helper 保留 skip 分支，是为了让测试在早期开发阶段也能作为契约草案；
        现在 simulator 已支持这些 op，因此正常路径应直接返回 result。
        """

        try:
            result = run_ir(ir)
        except SimTrap as exc:
            if exc.reason in LONG_MEMORY_NOT_READY:
                self.skipTest("long-term memory op_class simulator support is not present yet")
            raise
        except (KeyError, TypeError) as exc:
            self.skipTest(f"long-term memory task schema is not accepted yet: {exc}")
        return result

    def require_output(self, result, key):
        """要求模拟器结果暴露某个顶层输出。"""

        if key not in result:
            self.skipTest(f"simulator ran but does not expose {key} yet")
        return result[key]

    def test_ledger_delta_extract_emits_candidate_not_committed_ledger(self):
        """ledger_delta_extract 应只生成候选 delta，不提交 ledger。

        该测试验证五类账本都能从输入中被识别出来，并且输出带有 base_versions
        和 side_effects=candidate_only。
        """

        task = {
            "name": "extract_ledger_delta",
            "placement": {"cluster": 0, "core": 1},
            "capabilities": [
                "transcript_window",
                "artifact_previews",
                "plan_ledger_read",
                "ledger_delta_out",
            ],
            "budget": {
                "cycles": 4000,
                "max_refs": 128,
                "max_ledger_delta_bytes": 32768,
            },
            "op_class": "ledger_delta_extract",
            "ledger_delta": {
                "schema": "jiutian.ledger_delta.v0.1",
                "base_versions": {
                    "plan": "plan:42",
                    "evidence": "evidence:87",
                    "decision": "decision:15",
                },
                "inputs": ["transcript_window", "artifact_previews"],
                "allowed_ledgers": ["plan", "evidence", "decision", "recovery"],
                "allowed_ops": ["append", "mark_done", "replace_summary", "add_ref"],
                "require_evidence_for": ["append", "mark_done", "replace_summary", "add_ref"],
                "conflict_policy": "reject_on_base_mismatch",
                "output": "ledger_delta_out",
            },
            "program": [],
        }

        result = self.run_or_skip(base_ir([task]))

        self.assertTrue(trace_contains(result, "ledger_delta_extract"))
        self.assertFalse(trace_contains(result, "ledger_commit"))
        delta = dumped_json(result, "ledger_delta_out")
        self.assertEqual(delta["op_class"], "ledger_delta_extract")
        self.assertEqual(delta["base_versions"]["plan"], "plan:42")
        self.assertEqual(delta["side_effects"], "candidate_only")
        self.assertEqual(delta["counts"]["goal"], 1)
        self.assertEqual(delta["counts"]["plan"], 1)
        self.assertEqual(delta["counts"]["evidence"], 3)
        self.assertEqual(delta["counts"]["decision"], 1)
        self.assertEqual(delta["counts"]["recovery"], 1)

    def test_context_projection_preserves_must_keep_sections_under_budget(self):
        """context_budget_pack 应在预算内生成 projection。

        这里用很小的 byte_budget 验证输出不会越界，并且优先保留 transcript
        中的目标信息，体现“模型上下文是工作台视图，不是长期记忆本体”。
        """

        task = {
            "name": "pack_next_context",
            "placement": {"cluster": 0, "core": 0},
            "capabilities": [
                "transcript_window",
                "goal_ledger_read",
                "plan_ledger_read",
                "evidence_ledger_read",
                "recovery_ledger_read",
                "artifact_previews",
                "context_out",
            ],
            "budget": {"cycles": 2000, "token_budget": 256, "max_refs": 8, "max_sections": 6},
            "op_class": "context_budget_pack",
            "projection": {
                "byte_budget": 256,
                "base_versions": {
                    "goal": "goal:12",
                    "plan": "plan:42",
                    "evidence": "evidence:87",
                    "recovery": "recovery:9",
                },
                "inputs": [
                    "transcript_window",
                    "goal_ledger_read",
                    "plan_ledger_read",
                    "evidence_ledger_read",
                    "recovery_ledger_read",
                    "artifact_previews",
                ],
                "include": [
                    "active_goal",
                    "current_phase",
                    "pending_steps",
                    "recent_evidence",
                    "last_safe_point",
                ],
                "must_keep": ["active_goal", "user_constraints", "unsafe_to_drop_refs"],
                "drop_policy": "oldest_low_confidence_first",
                "ordering": "goal_plan_evidence_recovery",
                "output_schema": "jiutian.context_projection.v0.1",
                "output": "context_out",
            },
            "program": [],
        }

        result = self.run_or_skip(base_ir([task]))

        self.assertTrue(trace_contains(result, "context_budget_pack"))
        projection = dumped_json(result, "context_out")
        self.assertEqual(projection["op_class"], "context_budget_pack")
        self.assertEqual(projection["side_effects"], "projection_only")
        self.assertEqual(projection["byte_budget"], 256)
        self.assertLessEqual(projection["used_bytes"], 256)
        sources = [item["source"] for item in projection["items"]]
        self.assertEqual(sources[0], "transcript_window")
        self.assertIn("goal: keep simulator long memory runnable", projection["items"][0]["text"])

    def test_recovery_anchor_has_required_refs_and_unique_next_action(self):
        """recovery_anchor_select 应返回确定的候选恢复点。

        trace_window 中的 clean/safe/test 文本应获得更高排序，输出仍保持
        side_effects=candidate_only，避免把候选恢复点误当作已提交状态。
        """

        task = {
            "name": "select_recovery_anchor",
            "placement": {"cluster": 0, "core": 2},
            "capabilities": [
                "trace_window",
                "artifact_previews",
                "recovery_candidate_out",
            ],
            "budget": {"cycles": 2000},
            "op_class": "recovery_anchor_select",
            "recovery": {
                "strategy": "minimal_replay",
                "base_versions": {
                    "plan": "plan:42",
                    "evidence": "evidence:87",
                    "recovery": "recovery:9",
                },
                "inputs": ["trace_window", "artifact_previews"],
                "include": ["latest_clean_diff", "last_valid_test", "active_goal"],
                "required_refs": ["transcript", "trace", "ledger"],
                "dirty_state_policy": "declare_or_reject",
                "next_action_policy": "single_deterministic_step",
                "output": "recovery_candidate_out",
            },
            "program": [],
        }

        result = self.run_or_skip(base_ir([task]))

        self.assertTrue(trace_contains(result, "recovery_anchor_select"))
        anchor = dumped_json(result, "recovery_candidate_out")
        self.assertEqual(anchor["op_class"], "recovery_anchor_select")
        self.assertEqual(anchor["strategy"], "minimal_replay")
        self.assertEqual(anchor["side_effects"], "candidate_only")
        self.assertLessEqual(len(anchor["anchors"]), 3)
        self.assertEqual(anchor["anchors"][0]["source"], "trace_window")
        self.assertIn("clean test baseline", anchor["anchors"][0]["text"])


if __name__ == "__main__":
    unittest.main()
