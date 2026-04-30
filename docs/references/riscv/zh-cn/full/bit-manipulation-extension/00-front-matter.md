# RISC-V Bit-Manipulation ISA 扩展

Version 1.0.0-38-g865e7a7，2021-06-28：候选发布版。

## 目录

- Colophon
- Acknowledgments
- Bit-manipulation a, b, c and s extensions grouped for public review and ratification
- Word Instructions
- Pseudocode for instruction semantics
- 1. Extensions
  - 1.1. Zba extension
  - 1.2. Zbb: Basic bit-manipulation
    - 1.2.1. Logical with negate
    - 1.2.2. Count leading/trailing zero bits
    - 1.2.3. Count population
    - 1.2.4. Integer minimum/maximum
    - 1.2.5. Sign- and zero-extension
    - 1.2.6. Bitwise rotation
    - 1.2.7. OR Combine
    - 1.2.8. Byte-reverse
  - 1.3. Zbc: Carry-less multiplication
  - 1.4. Zbs: Single-bit instructions
- 2. Instructions (in alphabetical order)
  - 2.1. add.uw
  - 2.2. andn
  - 2.3. bclr
  - 2.4. bclri
  - 2.5. bext
  - 2.6. bexti
  - 2.7. binv
  - 2.8. binvi
  - 2.9. bset
  - 2.10. bseti
  - 2.11. clmul
  - 2.12. clmulh
  - 2.13. clmulr
  - 2.14. clz
  - 2.15. clzw
  - 2.16. cpop
  - 2.17. cpopw
  - 2.18. ctz
  - 2.19. ctzw
  - 2.20. max
  - 2.21. maxu
  - 2.22. min
  - 2.23. minu
  - 2.24. orc.b
  - 2.25. orn
  - 2.26. rev8
  - 2.27. rol
  - 2.28. rolw
  - 2.29. ror
  - 2.30. rori
  - 2.31. roriw
  - 2.32. rorw
  - 2.33. sext.b
  - 2.34. sext.h
  - 2.35. sh1add
  - 2.36. sh1add.uw
  - 2.37. sh2add
  - 2.38. sh2add.uw
  - 2.39. sh3add
  - 2.40. sh3add.uw
  - 2.41. slli.uw
  - 2.42. xnor
  - 2.43. zext.h
- Appendix A: Software optimization guide
  - A.1. strlen
  - A.2. strcmp

## Colophon

本文档依据 Creative Commons Attribution 4.0 International License 发布。

它描述了提交公开审阅的 BitManip `Zba`、`Zbb`、`Zbc` 和 `Zbs` 扩展。

## Acknowledgments

本规范的贡献者包括如下人员，按字母顺序列出：

Jacob Bachmeyer, Allen Baum, Ari Ben, Alex Bradbury, Steven Braeger, Rogier Brussee, Michael Clark, Ken Dockser, Paul Donahue, Dennis Ferguson, Fabian Giesen, John Hauser, Robert Henry, Bruce Hoult, Po-wei Huang, Ben Marshall, Rex McCrary, Lee Moore, Jiří Moravec, Samuel Neves, Markus Oberhumer, Christopher Olson, Nils Pipenbrinck, Joseph Rahmeh, Xue Saw, Tommy Thorn, Philipp Tomsich, Avishai Tvila, Andrew Waterman, Thomas Wicki, and Claire Wolf.

我们感谢所有通过评论和问题为本规范作出贡献、审阅或改进本规范的人。

## Bit-manipulation a, b, c and s extensions grouped for public review and ratification

bit-manipulation（bitmanip）扩展集合由若干面向 RISC-V 基础架构的组件扩展构成，目标是以某种组合方式降低代码大小、提升性能并减少能耗。虽然这些指令旨在具有通用用途，但某些指令在特定领域中比在其他领域更有用。因此，本规范提供若干较小的 bitmanip 扩展，而不是一个大型扩展。这些较小扩展中的每一个都按共同功能和使用场景分组，并且每个扩展都有自己的 `Zb*` 扩展名称。

每个 bitmanip 扩展都包含一组用途相近、且通常可以共享相同逻辑的 bitmanip 指令。有些指令只在一个扩展中可用，另一些指令则在多个扩展中可用。指令的助记符和编码独立于它们出现在哪些扩展中。因此，在实现包含重叠指令的扩展时，逻辑或编码上不存在冗余。

bitmanip 扩展针对 RV32 和 RV64 定义。预计大多数指令将向前兼容 RV128。虽然移位立即数指令被定义为至多具有 6 位立即数字段，但如果 RV128 需要，编码空间中还可使用第 7 位。

## Word Instructions

bitmanip 扩展遵循 RV64 中关于带 `w` 后缀指令的约定：带 `w` 后缀的指令（`w` 前没有点号）忽略输入的高 32 位，将最低有效 32 位作为有符号值操作，并产生一个 32 位有符号结果，该结果符号扩展到 `XLEN`。

带 `.uw` 后缀的 bitmanip 指令有一个操作数是无符号 32 位值，该值从指定寄存器的最低有效 32 位中提取。除此之外，这些指令执行完整的 `XLEN` 操作。

带 `.b`、`.h` 和 `.w` 后缀的 bitmanip 指令分别只查看输入的最低有效 8 位、16 位和 32 位，并根据具体指令产生一个符号扩展或零扩展到 `XLEN` 宽度的结果。

## Pseudocode for instruction semantics

`Instructions (in alphabetical order)` 中每条指令的语义均用类似 SAIL 的语法表达。

