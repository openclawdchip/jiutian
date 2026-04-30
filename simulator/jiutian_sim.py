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


WORD_BYTES = 8
REGISTER_COUNT = 16


class SimTrap(Exception):
    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass
class MemoryRegion:
    name: str
    space: str
    base: int
    bytes: int
    access: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryRegion":
        return cls(
            name=data["name"],
            space=data["space"],
            base=int(data["base"]),
            bytes=int(data["bytes"]),
            access=data["access"],
        )

    def allows(self, mode: str, space: str, addr: int, size: int) -> bool:
        if self.space != space:
            return False
        if mode == "read" and self.access not in {"read", "read_write"}:
            return False
        if mode == "write" and self.access not in {"write", "read_write"}:
            return False
        return self.base <= addr and addr + size <= self.base + self.bytes


@dataclass
class TaskState:
    name: str
    program: list[dict[str, Any]]
    capabilities: list[MemoryRegion]
    budget_cycles: int
    cluster: int = 0
    core: int = 0
    pc: int = 0
    regs: list[int] = field(default_factory=lambda: [0] * REGISTER_COUNT)
    halted: bool = False
    status: str = "created"
    waiting_barrier: str | None = None
    labels: dict[str, int] = field(default_factory=dict)

    def get_reg(self, name: str) -> int:
        index = parse_reg(name)
        if index == 0:
            return 0
        return self.regs[index]

    def set_reg(self, name: str, value: int) -> None:
        index = parse_reg(name)
        if index != 0:
            self.regs[index] = value & 0xFFFFFFFFFFFFFFFF


@dataclass
class Machine:
    spm_bytes: int
    cluster_bytes: int
    host: bytearray
    cluster: bytearray
    spm: dict[tuple[int, int], bytearray]
    barriers: dict[str, int]
    barrier_waiting: dict[str, set[str]] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, ir: dict[str, Any]) -> "Machine":
        config = ir.get("config", {})
        host_bytes = int(config.get("host_bytes", 4096))
        cluster_bytes = int(config.get("cluster_bytes", 4096))
        spm_bytes = int(config.get("spm_bytes", 65536))
        host = bytearray(host_bytes)
        for item in ir.get("host_init", []):
            write_u64(host, int(item["addr"]), int(item["value"]))
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
            barrier_waiting={name: set() for name in barriers},
        )

    def spm_for(self, task: TaskState) -> bytearray:
        key = (task.cluster, task.core)
        if key not in self.spm:
            self.spm[key] = bytearray(self.spm_bytes)
        return self.spm[key]


def parse_reg(name: str) -> int:
    if not name.startswith("r"):
        raise SimTrap("bad_register", name)
    index = int(name[1:])
    if index < 0 or index >= REGISTER_COUNT:
        raise SimTrap("bad_register", name)
    return index


def read_u64(mem: bytearray, addr: int) -> int:
    check_bounds(mem, addr, WORD_BYTES)
    return struct.unpack_from("<Q", mem, addr)[0]


def write_u64(mem: bytearray, addr: int, value: int) -> None:
    check_bounds(mem, addr, WORD_BYTES)
    struct.pack_into("<Q", mem, addr, value & 0xFFFFFFFFFFFFFFFF)


def check_bounds(mem: bytearray, addr: int, size: int) -> None:
    if addr < 0 or addr + size > len(mem):
        raise SimTrap("memory_oob", f"addr={addr} size={size} limit={len(mem)}")


def validate_cap(task: TaskState, mode: str, space: str, addr: int, size: int) -> None:
    if space in {"spm", "cluster"}:
        return
    for cap in task.capabilities:
        if cap.allows(mode, space, addr, size):
            return
    raise SimTrap("capability_violation", f"{mode} {space}:{addr}+{size}")


def memory_for(machine: Machine, task: TaskState, space: str) -> bytearray:
    if space == "host":
        return machine.host
    if space == "cluster":
        return machine.cluster
    if space == "spm":
        return machine.spm_for(task)
    raise SimTrap("bad_space", space)


def build_labels(program: list[dict[str, Any]]) -> dict[str, int]:
    labels: dict[str, int] = {}
    for pc, inst in enumerate(program):
        if inst.get("op") == "label":
            labels[inst["name"]] = pc
    return labels


def start_task(machine: Machine, task: TaskState) -> None:
    task.labels = build_labels(task.program)
    task.status = "running"
    machine.trace.append(f"task {task.name} start cluster={task.cluster} core={task.core}")


def step_task(machine: Machine, task: TaskState, tasks_by_name: dict[str, TaskState]) -> bool:
    if task.status != "running":
        return False
    if task.budget_cycles <= 0:
        raise SimTrap("cycle_budget_exhausted", task.name)
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


def run_tasks(machine: Machine, tasks: list[TaskState]) -> None:
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
            cluster=int(placement.get("cluster", 0)),
            core=int(placement.get("core", 0)),
        ))
    return tasks


def run_ir(ir: dict[str, Any]) -> dict[str, Any]:
    machine = Machine.create(ir)
    tasks = load_tasks(ir)
    run_tasks(machine, tasks)
    dump_words = ir.get("dump_words", [])
    return {
        "tasks": [{"name": t.name, "status": t.status, "pc": t.pc} for t in tasks],
        "host_words": {str(addr): read_u64(machine.host, int(addr)) for addr in dump_words},
        "trace": machine.trace,
    }


def main() -> int:
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
