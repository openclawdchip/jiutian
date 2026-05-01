#!/usr/bin/env python3
"""九天 APU v0.1 功能模拟器。

这是早期参考模型，目标是验证 APU-IR、SPM、DMA、Barrier 与任务边界，
不是周期精确模拟器。
"""

from __future__ import annotations

import argparse
import json
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# v0.1 模拟器把普通 load/store 统一建模为 64-bit word。
# 这样可以让早期 ISA 语义足够简单，避免在第一版里引入复杂的
# byte/halfword/word 对齐规则；后续如需更细粒度访问，再扩展这里。
WORD_BYTES = 8

# Agent 核的寄存器数量。r0 按 RISC 风格固定为 0，写入 r0 会被忽略。
REGISTER_COUNT = 16


class SimTrap(Exception):
    """模拟器内部 trap。

    这里的 trap 不是 Python 程序崩溃，而是九天 Agent task 的架构异常：
    例如 capability 越界、SPM 越界、非法 op、预算耗尽等。测试和 CLI 都通过
    reason/detail 判断是哪类架构错误。
    """

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass
class MemoryRegion:
    """APU-IR 中声明的内存区域。

    MemoryRegion 既是“地址范围”，也是 task 的最小 capability 单位。
    Agent task 只能访问 capabilities 列表里出现的 region。对于长期记忆任务，
    kind/ledger_type 用来区分 transcript、artifact preview、ledger view、
    candidate delta 等不同语义，但底层仍先映射到 v0.1 的 host/cluster/spm 空间。
    """

    name: str
    space: str
    base: int
    bytes: int
    access: str
    kind: str | None = None
    ledger_type: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryRegion":
        """从 APU-IR JSON 字段构造内存区域。"""

        return cls(
            name=data["name"],
            space=data["space"],
            base=int(data["base"]),
            bytes=int(data["bytes"]),
            access=data["access"],
            kind=data.get("kind"),
            ledger_type=data.get("ledger_type"),
        )

    def allows(self, mode: str, space: str, addr: int, size: int) -> bool:
        """检查一次 host 访问是否被该 region 授权。

        v0.1 中 host 访问必须通过 capability；SPM/cluster 的容量边界由对应
        bytearray 的 bounds check 执行。这里要求访问范围完整落在 region 内，
        不做“自动截断”，因为截断会隐藏生成代码的真实错误。
        """

        if self.space != space:
            return False
        if mode == "read" and self.access not in {"read", "read_write"}:
            return False
        if mode == "write" and self.access not in {"write", "read_write"}:
            return False
        return self.base <= addr and addr + size <= self.base + self.bytes


@dataclass
class TaskState:
    """一个 Agent task 的运行态。

    program 非空时表示普通 Agent ISA 指令流；program 为空且 op_class 非空时，
    表示 v0.1 为长期记忆验证引入的高层无副作用任务，例如 ledger delta 提取、
    recovery anchor 选择、context projection 打包。两者共用同一套 capability、
    budget、placement 和 trace 机制。
    """

    name: str
    program: list[dict[str, Any]]
    capabilities: list[MemoryRegion]
    budget_cycles: int
    op_class: str | None = None
    op_config: dict[str, Any] = field(default_factory=dict)
    cluster: int = 0
    core: int = 0
    pc: int = 0
    regs: list[int] = field(default_factory=lambda: [0] * REGISTER_COUNT)
    halted: bool = False
    status: str = "created"
    waiting_barrier: str | None = None
    labels: dict[str, int] = field(default_factory=dict)

    def get_reg(self, name: str) -> int:
        """读取寄存器。r0 永远返回 0。"""

        index = parse_reg(name)
        if index == 0:
            return 0
        return self.regs[index]

    def set_reg(self, name: str, value: int) -> None:
        """写寄存器。写 r0 会被忽略，其他寄存器按 64-bit 截断。"""

        index = parse_reg(name)
        if index != 0:
            self.regs[index] = value & 0xFFFFFFFFFFFFFFFF


@dataclass
class Machine:
    """九天 v0.1 功能模拟器的整机状态。

    这里故意只保存功能语义需要的最小状态：host/cluster/spm 三类内存、
    barrier 等待集合、trace，以及长期记忆高层任务产生的候选输出。
    注意 ledger_deltas/context_projections/recovery_anchors 都只是候选记录，
    它们模拟 Agent Domain 的输出，不代表 Super Domain 已经提交长期记忆。
    """

    spm_bytes: int
    cluster_bytes: int
    host: bytearray
    cluster: bytearray
    spm: dict[tuple[int, int], bytearray]
    barriers: dict[str, int]
    ledger_versions: dict[str, str] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    barrier_waiting: dict[str, set[str]] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    ledger_deltas: list[dict[str, Any]] = field(default_factory=list)
    context_projections: list[dict[str, Any]] = field(default_factory=list)
    recovery_anchors: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def create(cls, ir: dict[str, Any]) -> "Machine":
        """根据 APU-IR 顶层配置创建整机。

        host_init 用来把输入数据放入 host 空间；长期记忆示例会把 transcript
        window、artifact preview、trace window 这些文本化 JSON 放到 host 中，
        再通过 region capability 暴露给高层任务读取。
        """

        config = ir.get("config", {})
        host_bytes = int(config.get("host_bytes", 4096))
        cluster_bytes = int(config.get("cluster_bytes", 4096))
        spm_bytes = int(config.get("spm_bytes", 65536))
        host = bytearray(host_bytes)
        for item in ir.get("host_init", []):
            addr = int(item["addr"])
            if "value" in item:
                write_u64(host, addr, int(item["value"]))
            elif "text" in item:
                write_bytes(host, addr, item["text"].encode("utf-8"))
            elif "bytes" in item:
                write_bytes(host, addr, bytes(item["bytes"]))
            else:
                raise SimTrap("bad_host_init", f"addr={addr}")
        barriers = {
            b["name"]: int(b["participants"])
            for b in ir.get("barriers", [])
        }
        return cls(
            spm_bytes=spm_bytes,
            cluster_bytes=cluster_bytes,
            host=host,
            cluster=bytearray(cluster_bytes),
            spm={},
            barriers=barriers,
            ledger_versions=dict(ir.get("ledger_versions", {})),
            evidence_refs=list(ir.get("evidence_refs", [])),
            barrier_waiting={name: set() for name in barriers},
        )

    def spm_for(self, task: TaskState) -> bytearray:
        """取得 task 所在 core 的 SPM。

        SPM 按 (cluster, core) 分配。第一次访问时懒创建，符合 v0.1 功能模型；
        真实 RTL 里这会对应每个 Agent core 固定存在的本地 SRAM。
        """

        key = (task.cluster, task.core)
        if key not in self.spm:
            self.spm[key] = bytearray(self.spm_bytes)
        return self.spm[key]


def parse_reg(name: str) -> int:
    """解析 r0-r15 寄存器名，并在非法寄存器名时触发架构 trap。"""

    if not name.startswith("r"):
        raise SimTrap("bad_register", name)
    index = int(name[1:])
    if index < 0 or index >= REGISTER_COUNT:
        raise SimTrap("bad_register", name)
    return index


def read_u64(mem: bytearray, addr: int) -> int:
    """从 bytearray 中读取 little-endian 64-bit word。"""

    check_bounds(mem, addr, WORD_BYTES)
    return struct.unpack_from("<Q", mem, addr)[0]


def write_u64(mem: bytearray, addr: int, value: int) -> None:
    """向 bytearray 写入 little-endian 64-bit word。"""

    check_bounds(mem, addr, WORD_BYTES)
    struct.pack_into("<Q", mem, addr, value & 0xFFFFFFFFFFFFFFFF)


def write_bytes(mem: bytearray, addr: int, data: bytes) -> None:
    """写入任意字节串，主要用于 host_init 和 JSON 输出区。"""

    check_bounds(mem, addr, len(data))
    mem[addr:addr + len(data)] = data


def check_bounds(mem: bytearray, addr: int, size: int) -> None:
    """统一的容量边界检查。

    所有内存访问最终都会落到 bytearray。这里确保访问不会越过对应空间容量。
    host 的权限边界由 capability 先检查，bytearray 负责最后的物理容量边界。
    """

    if addr < 0 or addr + size > len(mem):
        raise SimTrap("memory_oob", f"addr={addr} size={size} limit={len(mem)}")


def validate_cap(task: TaskState, mode: str, space: str, addr: int, size: int) -> None:
    """检查 task 是否拥有指定访问权限。

    v0.1 对 host 强制 capability；SPM/cluster 暂时视为 task 本地或 cluster 内资源，
    由空间容量控制。后续若加入 cluster slice capability，可在这里扩展。
    """

    if space in {"spm", "cluster"}:
        return
    for cap in task.capabilities:
        if cap.allows(mode, space, addr, size):
            return
    raise SimTrap("capability_violation", f"{mode} {space}:{addr}+{size}")


def memory_for(machine: Machine, task: TaskState, space: str) -> bytearray:
    """把逻辑空间名映射为实际 bytearray。"""

    if space == "host":
        return machine.host
    if space == "cluster":
        return machine.cluster
    if space == "spm":
        return machine.spm_for(task)
    raise SimTrap("bad_space", space)


def capability_by_name(task: TaskState, name: str) -> MemoryRegion:
    """按 region 名称取得 task capability。

    高层长期记忆任务用 region 名称表达输入输出，例如 transcript_window、
    ledger_delta_out、context_out。若名称未授权，必须 trap，而不是返回空数据。
    """

    for cap in task.capabilities:
        if cap.name == name:
            return cap
    raise SimTrap("capability_violation", f"region {name}")


def read_region_text(machine: Machine, task: TaskState, name: str) -> str:
    """读取一个 region，并按 UTF-8 文本解释。

    长期记忆任务处理的是 transcript、artifact preview、ledger delta 等文本化
    JSON 或行文本。读取时会在第一个 NUL 处截断，模拟固定大小 host buffer
    中的字符串区域。
    """

    region = capability_by_name(task, name)
    validate_cap(task, "read", region.space, region.base, region.bytes)
    data = bytes(memory_for(machine, task, region.space)[region.base:region.base + region.bytes])
    data = data.split(b"\x00", 1)[0]
    return data.decode("utf-8", errors="replace")


def write_region_json(
    machine: Machine,
    task: TaskState,
    name: str,
    value: dict[str, Any],
) -> None:
    """把高层任务结果写入一个授权 region。

    输出区通常是 candidate delta、candidate recovery anchor 或 context projection。
    这些输出只代表 Agent Domain 的候选结果。若 payload 超过 region 容量，
    模拟器会写入一个最小截断标记；如果连截断标记都放不下，再触发 overflow trap。
    """

    region = capability_by_name(task, name)
    validate_cap(task, "write", region.space, region.base, region.bytes)
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(payload) > region.bytes:
        payload = json.dumps(
            {
                "truncated": True,
                "op_class": value.get("op_class"),
                "schema": value.get("schema"),
                "task": value.get("task"),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(payload) > region.bytes:
            raise SimTrap("region_overflow", f"{name} payload={len(payload)} limit={region.bytes}")
    mem = memory_for(machine, task, region.space)
    mem[region.base:region.base + region.bytes] = b"\x00" * region.bytes
    write_bytes(mem, region.base, payload)


def build_labels(program: list[dict[str, Any]]) -> dict[str, int]:
    """扫描指令流中的 label，供 jmp/beqz 使用。"""

    labels: dict[str, int] = {}
    for pc, inst in enumerate(program):
        if inst.get("op") == "label":
            labels[inst["name"]] = pc
    return labels


def start_task(machine: Machine, task: TaskState) -> None:
    """启动 task，并写入 trace。

    v0.1 没有复杂 admission 阶段，load_tasks 后直接 start；文档中保留
    admitted 状态，是为了后续 runtime 能区分“验证通过”和“已经派发”。
    """

    task.labels = build_labels(task.program)
    task.status = "running"
    machine.trace.append(f"task {task.name} start cluster={task.cluster} core={task.core}")


def step_task(machine: Machine, task: TaskState, tasks_by_name: dict[str, TaskState]) -> bool:
    """执行一个 task 的一步。

    普通 task 每次执行一条 Agent ISA JSON 指令；高层 op_class task 则在一步内
    完成整个无副作用投影任务。这样做是为了让 v0.1 先验证长期记忆数据流，
    暂不把这些高层操作展开成完整微指令序列。
    """

    if task.status != "running":
        return False
    if task.budget_cycles <= 0:
        raise SimTrap("cycle_budget_exhausted", task.name)
    if not task.program and task.op_class:
        task.budget_cycles -= 1
        execute_high_level_task(machine, task)
        task.status = "completed"
        task.halted = True
        task.pc = 1
        machine.trace.append(f"task {task.name} completed")
        return True
    if task.pc < 0 or task.pc >= len(task.program):
        raise SimTrap("pc_oob", str(task.pc))

    inst = task.program[task.pc]
    task.budget_cycles -= 1
    machine.trace.append(f"{task.name} pc={task.pc} {inst}")
    next_pc = task.pc + 1
    op = inst["op"]

    if op == "label":
        pass
    elif op == "li":
        task.set_reg(inst["dst"], int(inst["imm"]))
    elif op == "add":
        task.set_reg(inst["dst"], task.get_reg(inst["src1"]) + task.get_reg(inst["src2"]))
    elif op == "sub":
        task.set_reg(inst["dst"], task.get_reg(inst["src1"]) - task.get_reg(inst["src2"]))
    elif op == "jmp":
        next_pc = task.labels[inst["label"]]
    elif op == "beqz":
        if task.get_reg(inst["src"]) == 0:
            next_pc = task.labels[inst["label"]]
    elif op == "load":
        space = inst["space"]
        addr = int(inst["addr"])
        validate_cap(task, "read", space, addr, WORD_BYTES)
        task.set_reg(inst["dst"], read_u64(memory_for(machine, task, space), addr))
    elif op == "store":
        space = inst["space"]
        addr = int(inst["addr"])
        validate_cap(task, "write", space, addr, WORD_BYTES)
        write_u64(memory_for(machine, task, space), addr, task.get_reg(inst["src"]))
    elif op == "dma_copy":
        execute_dma(machine, task, inst)
    elif op == "dma_wait":
        machine.trace.append(f"{task.name} dma_wait complete")
    elif op == "barrier":
        execute_barrier(machine, task, inst["name"], tasks_by_name)
        task.regs[0] = 0
        return True
    elif op in {"flush", "invalidate", "fence"}:
        machine.trace.append(f"{task.name} {op} {inst.get('space', '')}".rstrip())
    elif op == "trap":
        raise SimTrap("explicit_trap", inst.get("reason", "trap"))
    elif op == "halt":
        task.halted = True
        task.pc = next_pc
        task.status = "completed"
        machine.trace.append(f"task {task.name} completed")
    else:
        raise SimTrap("bad_opcode", op)

    task.regs[0] = 0
    if task.status == "running":
        task.pc = next_pc
    return True


def execute_dma(machine: Machine, task: TaskState, inst: dict[str, Any]) -> None:
    """执行同步 DMA copy。

    文档中的长期语义把 DMA 视为可异步排队；当前功能模拟器为了保持简单，
    立即完成拷贝，并用 trace 标出数据移动路径。后续加入 NoC 延迟时，可把
    这里替换成队列模型而不改变 APU-IR。
    """

    src_space = inst["src_space"]
    dst_space = inst["dst_space"]
    src = int(inst["src"])
    dst = int(inst["dst"])
    size = int(inst["bytes"])
    validate_cap(task, "read", src_space, src, size)
    validate_cap(task, "write", dst_space, dst, size)
    src_mem = memory_for(machine, task, src_space)
    dst_mem = memory_for(machine, task, dst_space)
    check_bounds(src_mem, src, size)
    check_bounds(dst_mem, dst, size)
    dst_mem[dst:dst + size] = src_mem[src:src + size]
    machine.trace.append(f"{task.name} dma_copy {src_space}:{src} -> {dst_space}:{dst} bytes={size}")


def execute_barrier(
    machine: Machine,
    task: TaskState,
    name: str,
    tasks_by_name: dict[str, TaskState],
) -> None:
    """执行显式 barrier。

    barrier 只建立顺序点，不自动搬运数据，也不替代 flush/invalidate。
    当等待者数量达到 participants 时，释放所有等待 task，并让它们 PC 前进。
    """

    if name not in machine.barriers:
        raise SimTrap("bad_barrier", name)
    waiters = machine.barrier_waiting[name]
    waiters.add(task.name)
    task.status = "waiting"
    task.waiting_barrier = name
    machine.trace.append(
        f"{task.name} barrier {name} arrived={len(waiters)}/{machine.barriers[name]}"
    )
    if len(waiters) >= machine.barriers[name]:
        released = sorted(waiters)
        waiters.clear()
        for task_name in released:
            waiting_task = tasks_by_name[task_name]
            waiting_task.status = "running"
            waiting_task.waiting_barrier = None
            waiting_task.pc += 1
        machine.trace.append(f"barrier {name} release {','.join(released)}")


def execute_high_level_task(machine: Machine, task: TaskState) -> None:
    """分派长期记忆相关高层 op_class。

    这些 op 是 v0.1 为 Claude Code 类 Agent 长任务记忆闭环准备的最小语义：
    从授权输入中提取候选 ledger delta，选择恢复点，再在预算内打包下一轮上下文。
    """

    if task.op_class == "ledger_delta_extract":
        execute_ledger_delta_extract(machine, task)
    elif task.op_class == "recovery_anchor_select":
        execute_recovery_anchor_select(machine, task)
    elif task.op_class in {"context_budget_pack", "context_projection"}:
        execute_context_budget_pack(machine, task)
    else:
        raise SimTrap("bad_op_class", task.op_class or "")


def parse_records(text: str) -> list[dict[str, Any]]:
    """把 region 文本解析成记录列表。

    输入优先按 JSON 解析：list 表示多条事件，dict 表示单条或包含 events/items。
    如果不是 JSON，就按非空行拆分。这让 benchmark 可以同时使用结构化 JSON
    和简易文本日志。
    """

    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return [{"text": line.strip()} for line in text.splitlines() if line.strip()]
    if isinstance(data, list):
        return [item if isinstance(item, dict) else {"text": item} for item in data]
    if isinstance(data, dict):
        for key in ("events", "records", "items", "deltas"):
            if isinstance(data.get(key), list):
                return [
                    item if isinstance(item, dict) else {"text": item}
                    for item in data[key]
                ]
        return [data]
    return [{"text": data}]


def record_text(record: dict[str, Any]) -> str:
    """从一条记录中取最适合作为摘要的文本。"""

    for key in ("text", "summary", "message", "body", "path", "command"):
        if key in record:
            return str(record[key])
    return json.dumps(record, ensure_ascii=False, sort_keys=True)


def classify_record(record: dict[str, Any]) -> str:
    """把输入记录粗分类到五类长期记忆账本。

    真实系统会由更严格的 schema 和模型/规则协同完成分类；v0.1 模拟器采用
    显式字段优先、关键词兜底的方式，目标是验证 ledger delta 数据流，不是
    证明分类算法本身已经完备。
    """

    explicit = record.get("ledger") or record.get("ledger_type") or record.get("kind") or record.get("type")
    if isinstance(explicit, str):
        explicit = explicit.lower()
        if explicit in {"goal", "plan", "evidence", "decision", "recovery"}:
            return explicit
    text = record_text(record).lower()
    keyword_map = {
        "goal": ("goal", "目标", "success", "成功标准"),
        "plan": ("plan", "todo", "step", "计划", "步骤", "待办"),
        "evidence": ("evidence", "file", "test", "command", "证据", "测试", "命令"),
        "decision": ("decision", "decide", "choose", "reject", "决策", "决定", "拒绝"),
        "recovery": ("recovery", "anchor", "safe point", "rollback", "恢复", "回滚"),
    }
    for ledger_type, keywords in keyword_map.items():
        if any(keyword in text for keyword in keywords):
            return ledger_type
    return "evidence"


def execute_ledger_delta_extract(machine: Machine, task: TaskState) -> None:
    """执行 ledger_delta_extract 高层任务。

    该任务读取 transcript/artifact preview 等授权输入，分类为 goal/plan/evidence/
    decision/recovery 五类候选 delta，然后写入 output region。它不会修改
    Machine.ledger_versions，也不会提交长期记忆，严格模拟“Agent Domain 只产
    生候选，Super Domain 负责审核提交”的安全边界。
    """

    config = task.op_config.get("ledger_delta", task.op_config)
    output = config.get("output")
    if not output:
        raise SimTrap("bad_high_level_task", f"{task.name} missing output")
    inputs = config.get("inputs", [])
    deltas: dict[str, list[dict[str, Any]]] = {
        key: [] for key in ("goal", "plan", "evidence", "decision", "recovery")
    }
    for region_name in inputs:
        for index, record in enumerate(parse_records(read_region_text(machine, task, region_name))):
            ledger_type = classify_record(record)
            deltas[ledger_type].append({
                "source": region_name,
                "index": index,
                "text": record_text(record),
            })
    seed_deltas = list(config.get("seed_deltas", []))
    extracted = [
        {"ledger": ledger_type, "op": "append", "value": item}
        for ledger_type, items in deltas.items()
        for item in items
    ]
    result = {
        "schema": config.get("schema", "jiutian.ledger_delta.v0.1"),
        "op_class": "ledger_delta_extract",
        "task": task.name,
        "base_versions": config.get("base_versions", {}),
        "output": output,
        "deltas": seed_deltas + extracted,
        "counts": {key: len(items) for key, items in deltas.items()},
        "side_effects": "candidate_only",
    }
    write_region_json(machine, task, output, result)
    machine.ledger_deltas.append(result)
    machine.trace.append(f"{task.name} ledger_delta_extract ledger_delta_emit inputs={len(inputs)} output={output}")


def execute_recovery_anchor_select(machine: Machine, task: TaskState) -> None:
    """执行 recovery_anchor_select 高层任务。

    恢复点选择从输入记录中寻找更适合断点续跑的证据。当前评分规则很朴素：
    包含 safe/test/clean/recovery/恢复/测试 等关键词的记录得分更高。输出仍是
    candidate_only，表示它只是恢复点候选，不代表控制面已经采用。
    """

    config = task.op_config.get("recovery", task.op_config)
    output = config.get("output")
    if not output:
        raise SimTrap("bad_high_level_task", f"{task.name} missing output")
    candidates: list[dict[str, Any]] = []
    for region_name in config.get("inputs", []):
        for index, record in enumerate(parse_records(read_region_text(machine, task, region_name))):
            text = record_text(record)
            score = sum(token in text.lower() for token in ("safe", "test", "clean", "recovery", "恢复", "测试"))
            candidates.append({"source": region_name, "index": index, "score": score, "text": text})
    candidates.sort(key=lambda item: (-int(item["score"]), str(item["source"]), int(item["index"])))
    refs = refs_by_kind(machine, config.get("base_versions", {}), config.get("required_refs", []))
    anchor = {
        "task": task.name,
        "strategy": config.get("strategy", "minimal_replay"),
        "output": output,
        "refs": refs,
        "next_actions": [config.get("next_action", "resume_from_recovery_anchor")],
        "anchors": candidates[: int(config.get("max_anchors", 3))],
        "side_effects": "candidate_only",
    }
    result = {
        "op_class": "recovery_anchor_select",
        **anchor,
    }
    write_region_json(machine, task, output, result)
    machine.recovery_anchors.append(anchor)
    machine.trace.append(f"{task.name} recovery_anchor_select recovery_anchor_emit candidates={len(candidates)} output={output}")


def execute_context_budget_pack(machine: Machine, task: TaskState) -> None:
    """执行 context_budget_pack/context_projection 高层任务。

    该任务把若干输入 region 的文本按字节预算打包成模型下一轮可见的投影。
    它故意不复制完整长期记忆，只生成“工作台视图”。真正的账本仍保存在
    ledger/artifact/transcript 中，projection 被 compact 也不应破坏长期状态。
    """

    config = task.op_config.get("context_pack", task.op_config.get("projection", task.op_config))
    output = config.get("output")
    if not output:
        raise SimTrap("bad_high_level_task", f"{task.name} missing output")
    budget = task.op_config.get("budget", {})
    token_budget = int(config.get("token_budget", budget.get("token_budget", 4096)))
    byte_budget = int(config.get("byte_budget", token_budget))
    packed: list[dict[str, Any]] = []
    used = 0
    for region_name in config.get("inputs", []):
        text = read_region_text(machine, task, region_name)
        remain = byte_budget - used
        if remain <= 0:
            break
        excerpt = text.encode("utf-8")[:remain].decode("utf-8", errors="ignore")
        used += len(excerpt.encode("utf-8"))
        packed.append({"source": region_name, "text": excerpt})
    sections = {name: "" for name in config.get("include", [])}
    for name in config.get("must_keep", []):
        sections.setdefault(name, "")
    if not sections:
        sections = {"projection": ""}
    for item in packed:
        target = next(iter(sections))
        sections[target] = (sections[target] + "\n" + item["text"]).strip()
    projection = {
        "schema": config.get("output_schema", "jiutian.context_projection.v0.1"),
        "task": task.name,
        "budget": {"tokens": min(token_budget, used), "bytes": byte_budget},
        "base_versions": config.get("base_versions", machine.ledger_versions),
        "sections": sections,
        "active_evidence": machine.evidence_refs or ["simulator:synthetic-evidence"],
        "output": output,
        "side_effects": "projection_only",
    }
    result = {
        "op_class": "context_budget_pack",
        "byte_budget": byte_budget,
        "used_bytes": used,
        "items": packed,
        "side_effects": "projection_only",
        **projection,
    }
    write_region_json(machine, task, output, result)
    machine.context_projections.append(projection)
    machine.trace.append(f"{task.name} context_budget_pack_start budget={token_budget}")
    machine.trace.append(f"{task.name} context_projection_emit used={used}/{byte_budget} output={output}")


def refs_by_kind(
    machine: Machine,
    base_versions: dict[str, Any],
    required_refs: list[str],
) -> dict[str, Any]:
    """根据 required_refs 构造恢复点引用集合。

    ledger 引用来自 base_versions 或机器已知版本；其他引用从 evidence_refs 中
    按前缀挑选。找不到真实引用时返回 synthetic 占位，方便 v0.1 测试稳定表达
    “需要这种引用”的结构。
    """

    refs: dict[str, Any] = {}
    for kind in required_refs:
        if kind == "ledger":
            refs["ledger"] = base_versions or machine.ledger_versions
            continue
        prefix = f"{kind}:"
        refs[kind] = next(
            (ref for ref in machine.evidence_refs if str(ref).startswith(prefix)),
            f"{kind}:synthetic",
        )
    if "ledger" not in refs:
        refs["ledger"] = base_versions or machine.ledger_versions
    return refs


def run_tasks(machine: Machine, tasks: list[TaskState]) -> None:
    """运行所有 task，直到全部完成或发生 trap/deadlock。

    调度器采用简单 round-robin：每轮让 runnable task 前进一步。这个策略不追求
    性能最优，而是让 trace 容易解释，适合 v0.1 验证 task 状态机和同步语义。
    """

    tasks_by_name = {task.name: task for task in tasks}
    for task in tasks:
        start_task(machine, task)

    try:
        while True:
            active = [task for task in tasks if task.status in {"running", "waiting"}]
            if not active:
                return
            progressed = False
            for task in tasks:
                if task.status == "running":
                    progressed = step_task(machine, task, tasks_by_name) or progressed
            if not progressed:
                waiting = [task.name for task in tasks if task.status == "waiting"]
                raise SimTrap("deadlock", "waiting=" + ",".join(waiting))
    except SimTrap as exc:
        for task in tasks:
            if task.status in {"running", "waiting"}:
                task.status = "trapped"
        machine.trace.append(f"scheduler trap reason={exc.reason} detail={exc.detail}")
        raise


def load_tasks(ir: dict[str, Any]) -> list[TaskState]:
    """从 APU-IR 加载 task 列表并绑定 capability。"""

    regions = {m["name"]: MemoryRegion.from_dict(m) for m in ir.get("memory", [])}
    tasks: list[TaskState] = []
    for item in ir.get("tasks", []):
        placement = item.get("placement", {})
        caps = [regions[name] for name in item.get("capabilities", [])]
        budget = item.get("budget", {})
        tasks.append(TaskState(
            name=item["name"],
            program=item["program"],
            capabilities=caps,
            budget_cycles=int(budget.get("cycles", 1000)),
            op_class=item.get("op_class"),
            op_config=item,
            cluster=int(placement.get("cluster", 0)),
            core=int(placement.get("core", 0)),
        ))
    return tasks


def run_ir(ir: dict[str, Any]) -> dict[str, Any]:
    """执行一份 APU-IR，并返回可测试的结果对象。"""

    machine = Machine.create(ir)
    tasks = load_tasks(ir)
    run_tasks(machine, tasks)
    dump_words = ir.get("dump_words", [])
    dump_regions = ir.get("dump_regions", [])
    return {
        "tasks": [{"name": t.name, "status": t.status, "pc": t.pc} for t in tasks],
        "host_words": {str(addr): read_u64(machine.host, int(addr)) for addr in dump_words},
        "host_regions": dump_host_regions(machine, dump_regions),
        "ledger_deltas": machine.ledger_deltas,
        "context_projections": machine.context_projections,
        "recovery_anchors": machine.recovery_anchors,
        "trace": machine.trace,
    }


def dump_host_regions(machine: Machine, regions: list[dict[str, Any]]) -> dict[str, str]:
    """按 dump_regions 配置导出 host 中的文本区域。

    长期记忆示例用它读取 ledger_delta_out、context_out、recovery_candidate_out，
    便于测试直接解析 JSON 输出。
    """

    result: dict[str, str] = {}
    for item in regions:
        name = item.get("name", f"{item['addr']}:{item['bytes']}")
        addr = int(item["addr"])
        size = int(item["bytes"])
        check_bounds(machine.host, addr, size)
        result[name] = bytes(machine.host[addr:addr + size]).split(b"\x00", 1)[0].decode(
            "utf-8",
            errors="replace",
        )
    return result


def main() -> int:
    """命令行入口。"""

    parser = argparse.ArgumentParser(description="九天 APU v0.1 功能模拟器")
    parser.add_argument("ir", type=Path, help="APU-IR JSON 文件")
    parser.add_argument("--trace", action="store_true", help="输出完整 trace")
    args = parser.parse_args()

    ir = json.loads(args.ir.read_text(encoding="utf-8"))
    result = run_ir(ir)
    if not args.trace:
        result = {k: v for k, v in result.items() if k != "trace"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
