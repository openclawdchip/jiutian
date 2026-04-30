# Architecture Overview

JiuTian APU uses a split execution model.

## Control Plane

The control plane runs on a small number of high-performance super cores. It is
responsible for:

- Boot and operating system execution.
- Device management and I/O.
- Runtime policy.
- Agent-task admission control.
- Memory protection and capability assignment.
- Exception handling and task termination.

The control plane favors compatibility, precise exceptions, mature tooling, and
standard software semantics.

## Agent Plane

The agent plane runs on many simpler agent-native cores. It is responsible for:

- Short-lived generated logic.
- High-concurrency task graphs.
- Explicit SPM allocation.
- Explicit DMA data movement.
- Explicit synchronization.
- Weak or software-managed coherency.

The agent plane favors execution density, predictable local memory behavior, and
low overhead task dispatch.

## Why Split the Planes?

Human-written software needs compatibility, debuggability, and stable
interfaces. Agent-generated software can expose dataflow, lifetime, and memory
placement information directly to the runtime and hardware.

JiuTian treats that difference as a first-class architecture boundary.
