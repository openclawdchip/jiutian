# Runtime

This directory will hold the agent runtime and APU-IR prototype.

Runtime responsibilities:

- Accept generated task graphs.
- Validate capabilities.
- Allocate SPM and cluster SRAM regions.
- Schedule agent tasks.
- Program DMA descriptors.
- Handle traps, timeouts, and task cleanup.

APU-IR should describe what the generated program needs without forcing it to
pretend it is conventional human-written software.
