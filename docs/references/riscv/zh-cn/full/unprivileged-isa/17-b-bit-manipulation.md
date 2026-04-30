# Chapter 17 `B` Standard Extension for Bit Manipulation, Version 0.0

本章是未来标准扩展的占位章。该未来扩展将提供 bit manipulation 指令，包括用于插入、提取和测试 bit fields 的指令，以及用于 rotations、funnel shifts、bit permutations 和 byte permutations 的指令。

虽然 bit manipulation 指令在某些应用领域非常有效，特别是在处理外部打包的数据结构时，但它们未被纳入基础 ISA。原因是这些指令并非在所有领域都有用，并且为了提供所有所需 operands，可能会增加额外复杂度或需要额外指令格式。

预计 `B` 扩展将在基础 30 位指令空间内采用 brownfield encoding。
