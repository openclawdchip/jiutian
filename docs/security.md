# Security Model

Generated code must not imply unrestricted hardware access.

JiuTian treats each agent task as a bounded execution object with explicit
capabilities.

## Required Controls

- Capability tokens for memory, DMA, and device access.
- Bounds checks for SPM, cluster SRAM, and DMA descriptors.
- Per-task cycle budgets.
- Per-task memory budgets.
- Runtime-authorized code pages.
- Fast task kill and cleanup.
- SPM scrubbing after task termination when needed.

## Fault Model

Agent code may be incorrect, adversarial, or simply over-optimized. The
architecture should assume generated code can:

- Access invalid addresses.
- Loop indefinitely.
- Violate synchronization contracts.
- Overrun local memory.
- Emit malformed DMA descriptors.

The hardware and runtime must contain those failures within the task or cluster
where possible.
