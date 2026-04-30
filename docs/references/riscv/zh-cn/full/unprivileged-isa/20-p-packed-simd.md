# Chapter 20 `P` Standard Extension for Packed-SIMD Instructions, Version 0.2

第 5 届 RISC-V workshop 上的讨论表明，有意放弃这个面向浮点寄存器的 packed-SIMD 提案，转而为大型浮点 SIMD 操作标准化 `V` 扩展。

不过，对于在小型 RISC-V 实现的整数寄存器中使用 packed-SIMD fixed-point 操作，仍然存在兴趣。一个 task group 正在定义新的 `P` 扩展。
