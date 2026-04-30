# JiuTian APU v0.1 Draft Specification

Status: seed draft

## 1. Purpose

This specification defines a minimal agent-native architecture target suitable
for simulation and early RTL exploration.

## 2. Minimal Target

- 1-2 super cores.
- 8-16 agent cores.
- 2 hardware threads per agent core.
- Per-agent-core SPM.
- Shared cluster SRAM.
- Explicit DMA.
- Explicit barriers.
- Runtime-enforced task capabilities.

## 3. Execution Domains

### Super Domain

The super domain runs privileged software, the operating system, and the APU
runtime. It owns task admission, memory capabilities, scheduling, and exception
recovery.

### Agent Domain

The agent domain runs generated code fragments. Agent tasks are not assumed to
have POSIX process semantics, standard ABI semantics, or global cache-coherent
memory semantics.

## 4. Required Operations

The v0.1 model should include operations for:

- Local SPM load/store.
- Cluster SRAM load/store.
- DMA enqueue.
- DMA wait.
- Barrier arrive/wait.
- Flush.
- Invalidate.
- Yield.
- Trap.

## 5. APU-IR Contract

APU-IR is the stable interface above machine instructions. It must represent:

- Task graph topology.
- Memory regions and access modes.
- Placement preferences.
- Synchronization.
- DMA movement.
- Runtime capabilities.
- Expected resource budgets.

## 6. Benchmark Categories

- Agent-generated rule execution.
- Structured data transformation.
- Graph traversal.
- Short-lived JIT fragments.
- Tool-call orchestration logic.
- Irregular memory microbenchmarks.

## 7. Open Questions

- Should v0.1 agent cores be in-order, weakly out-of-order, or VLIW-like?
- What is the minimum useful SPM size?
- How much coherency should be available inside one cluster?
- What exception precision is required for debugging generated code?
- What is the first fair baseline for agentic workload comparisons?
