# Contributing to JiuTian APU

JiuTian is an architecture-stage project. The best contributions are precise,
testable, and tied to a concrete design question.

## Contribution Areas

- Architecture specification and terminology.
- APU-IR semantics.
- Agent-core ISA and execution model.
- Scratchpad memory and DMA programming model.
- NoC topology, routing, and QoS.
- Security model for generated code.
- Simulator prototypes and benchmark harnesses.
- RTL modules once the v0.1 spec stabilizes.

## Ground Rules

- Prefer measurable claims over broad marketing language.
- Separate assumptions from verified results.
- Keep compatibility and agent-native execution as distinct domains.
- Include benchmark methodology with performance claims.
- Avoid introducing global cache-coherent SMP semantics into the agent plane
  unless the tradeoff is explicitly justified.

## Pull Requests

Before opening a pull request, please include:

- The problem being solved.
- The design choice or implementation change.
- Alternatives considered.
- Any tests, simulations, or validation steps.

Small, focused pull requests are easier to review than sweeping rewrites.
