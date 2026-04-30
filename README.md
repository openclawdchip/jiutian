# JiuTian APU

JiuTian APU is an open, agent-native processor architecture project.

It explores a post-Von-Neumann software model where human-written software and
agent-generated code are treated as different execution domains:

- 8 super cores run the operating system, compatibility layer, runtime,
  scheduling, safety supervision, and human-facing software.
- 128 agent cores run high-throughput agent-generated logic streams with
  explicit memory placement, explicit synchronization, and weak coherency.
- 256 agent hardware threads target fragmented, dynamic, short-lived workloads
  that sit between conventional CPU control flow and GPU tensor throughput.

The project goal is not to replace CPUs, GPUs, or NPUs. It is to define and
prototype the missing execution tier for agentic workloads: code that is
branchy, generated on demand, data-local, highly concurrent, and too irregular
for traditional accelerator stacks.

## Positioning

JiuTian is the product name. Honeycomb is the architecture codename.

```text
Human software
    |
8x JiuTian Super cores
Linux / runtime / safety / scheduling
    |
APU-IR compiler and agent runtime
    |
128x JiuTian Agent cores
SPM / explicit DMA / weak coherency / mesh NoC
    |
Distributed SRAM / HBM / host memory
```

## Repository Layout

- `docs/` - Architecture notes and design rationale.
- `specs/` - Versioned architecture specifications.
- `rtl/` - RTL design entry point and future hardware modules.
- `simulator/` - ISA and architecture simulator entry point.
- `runtime/` - Agent runtime, compiler IR, and scheduling notes.
- `benchmarks/` - Workload definitions and benchmark methodology.
- `tools/` - Project scripts and utilities.

## Initial Design Targets

- Open architecture for research and implementation.
- RISC-V-compatible control plane.
- Agent-native execution plane with explicit scratchpad memory.
- Clustered 128-core topology with distributed SRAM slices.
- Software-controlled coherency for agent domains.
- Hardware-enforced sandboxing, task budgets, and DMA bounds.
- APU-IR as the stable contract between agents and silicon.

## Non-Goals

- Running arbitrary legacy software on all cores.
- Recreating CUDA, POSIX, or full cache-coherent SMP semantics.
- Optimizing only synthetic peak FLOPS.
- Claiming universal replacement of existing accelerators.

## Current Status

This repository is at architecture seed stage. The first milestone is a
minimal, simulatable v0.1 architecture:

- 1-2 super cores.
- 8-16 agent cores.
- Per-core scratchpad memory.
- Shared cluster SRAM.
- Explicit DMA and barriers.
- APU-IR prototype.
- Benchmark harness for agentic logic workloads.

## License

Software, documentation, and examples are licensed under Apache-2.0 unless a
subdirectory states otherwise. Hardware-specific licensing may be refined when
RTL is introduced.
