# Roadmap

## Phase 0: Architecture Seed

- Define JiuTian/Honeycomb terminology.
- Draft v0.1 architecture specification.
- Define the agent execution domain.
- Define the control-plane and agent-plane boundary.
- Establish benchmark categories.

## Phase 1: Minimal Simulator

- Implement a functional simulator for a small cluster.
- Model super-core task dispatch at a high level.
- Model agent-core execution, SPM, DMA, barriers, and exceptions.
- Add trace output for memory movement and synchronization.

## Phase 2: APU-IR Prototype

- Define an initial task graph IR.
- Add memory placement annotations.
- Add explicit DMA and barrier operations.
- Lower simple kernels into simulator instructions.

## Phase 3: Hardware Microarchitecture Prototype

- Specify a single agent core.
- Specify a cluster with local SRAM.
- Add basic NoC packet format and routing behavior.
- Create synthesizable RTL for selected modules.

## Phase 4: Benchmark and Evaluation

- Build agentic logic workloads.
- Compare against conventional CPU baselines where fair.
- Measure throughput, latency, memory traffic, and energy proxies.
- Publish reproducible benchmark scripts and traces.
