# Chapter 15 `L` Standard Extension for Decimal Floating-Point, Version 0.0

本章是一个尚未由 Foundation 批准的草案提案。

本章是名为 `L` 的标准扩展规范占位章。该扩展设计用于支持 IEEE 754-2008 标准所定义的 decimal floating-point 算术。

## 15.1 Decimal Floating-Point Registers

现有浮点寄存器用于保存 64 位和 128 位 decimal floating-point 值，并使用现有浮点 load 和 store 指令在寄存器与内存之间移动这些值。

由于 fused multiply-add 指令需要大量 opcode 空间，decimal floating-point 指令扩展将需要在 30 位编码空间中使用五个 25 位 major opcodes。
