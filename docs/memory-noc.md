# Memory and NoC Model

The Honeycomb architecture uses explicit local memory and clustered transport
instead of assuming one fully coherent shared memory fabric for all cores.

## Memory Tiers

1. Per-core scratchpad memory (SPM).
2. Shared cluster SRAM.
3. Distributed on-chip SRAM slices.
4. External memory such as HBM or host-attached DRAM.

## Programming Model

Agent tasks should describe:

- Input and output regions.
- Local working-set size.
- Placement preferences.
- DMA transfer schedule.
- Barrier and dependency points.
- Lifetime of temporary data.

## Coherency

The super-core domain may use conventional hardware coherency. The agent domain
uses explicit coherency operations by default:

- `flush` publishes written data.
- `invalidate` discards stale local copies.
- `barrier` establishes ordering among tasks.
- `fence` establishes ordering for DMA and memory-visible effects.

## NoC Direction

The NoC should support separate traffic classes:

- Control messages.
- DMA transfers.
- Agent-to-agent messages.
- External memory traffic.
- Exceptions and kill signals.

Control traffic must be able to preempt data traffic so the runtime can always
retain supervision over generated code.
