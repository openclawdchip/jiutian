# RTL

This directory will hold synthesizable hardware modules once the v0.1
architecture is stable enough to implement.

Planned modules:

- Agent core frontend.
- Agent core execution pipeline.
- Scratchpad memory.
- DMA engine.
- Barrier unit.
- Cluster SRAM interface.
- NoC packet interface.
- Capability and bounds-check unit.

Until then, architecture behavior should be prototyped in `simulator/`.
