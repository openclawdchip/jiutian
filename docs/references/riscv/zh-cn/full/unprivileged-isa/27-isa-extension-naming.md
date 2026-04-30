# Chapter 27 ISA Extension Naming Conventions

本章描述 RISC-V ISA extension naming scheme。该命名方案用于简洁描述硬件实现中存在的指令集合，或 application binary interface（ABI）所使用的指令集合。

RISC-V ISA 被设计为支持各种实现以及各种 experimental instruction-set extensions。实践表明，有组织的命名方案可以简化软件工具和文档。

## 27.1 Case Sensitivity

ISA naming strings 不区分大小写。

## 27.2 Base Integer ISA

RISC-V ISA strings 以 `RV32I`、`RV32E`、`RV64I` 或 `RV128I` 开始，用来表示 base integer ISA 支持的 address space size，单位为位。

## 27.3 Instruction-Set Extension Names

standard ISA extensions 使用单个字母组成的名称。例如，整数 bases 的前四个 standard extensions 是：`M` 表示 integer multiplication and division，`A` 表示 atomic memory instructions，`F` 表示 single-precision floating-point instructions，`D` 表示 double-precision floating-point instructions。任何 RISC-V instruction-set variant 都可以通过把 base integer prefix 与所包含 extensions 的名称连接起来简洁描述，例如 `RV64IMAFD`。

本规范还定义了缩写 `G`，表示 `IMAFDZicsr_Zifencei` base 和 extensions，因为它旨在表示标准 general-purpose ISA。

RISC-V ISA 的 standard extensions 还分配了其他保留字母，例如 `Q` 表示 quad-precision floating-point，`C` 表示 16-bit compressed instruction format。

一些 ISA extensions 依赖其他 extensions 的存在，例如 `D` 依赖 `F`，`F` 依赖 `Zicsr`。这些依赖可以隐含在 ISA name 中：例如，`RV32IF` 等价于 `RV32IFZicsr`，`RV32ID` 等价于 `RV32IFD` 和 `RV32IFDZicsr`。

## 27.4 Version Numbers

考虑到指令集可能随时间扩展或改变，extension version numbers 被编码在 extension name 之后。版本号分为 major 和 minor version numbers，并用 `p` 分隔。如果 minor version 是 `0`，则可以从版本字符串中省略 `p0`。major version number 的变化意味着丧失 backwards compatibility；而仅 minor version number 的变化必须保持 backwards-compatible。例如，本手册 1.0 版中定义的原始 64 位 standard ISA 可以完整写为 `RV64I1p0M1p0A1p0F1p0D1p0`，更简洁地写为 `RV64I1M1A1F1D1`。

版本编号方案是在第二版中引入的。因此，本规范把 standard extension 的默认版本定义为当时存在的版本，例如 `RV32I` 等价于 `RV32I2`。

## 27.5 Underscores

可以使用 underscores `_` 分隔 ISA extensions，以提高可读性并提供消歧，例如 `RV32I2_M2_A2`。

由于 Packed SIMD 的 `P` 扩展可能与版本号中的小数点混淆，如果 `P` 跟在数字之后，则必须在它前面加 underscore。例如，`rv32i2p2` 表示 RV32I 的 2.2 版，而 `rv32i2_p2` 表示 RV32I 的 2.0 版加上 `P` 扩展的 2.0 版。

## 27.6 Additional Standard Extension Names

standard extensions 也可以使用单个 `Z` 后跟 alphabetical name 和可选 version number 来命名。例如，`Zifencei` 命名第 3 章描述的 instruction-fetch fence extension；`Zifencei2` 和 `Zifencei2p0` 命名同一扩展的 2.0 版。

按照惯例，`Z` 后面的第一个字母表示最接近相关的 alphabetical extension category，即 `IMAFDQLCBJTPVN`。例如，对于 misaligned atomics 的 `Zam` 扩展，字母 `a` 表示该扩展与 `A` standard extension 相关。如果命名了多个 `Z` extensions，它们应先按 category 排序，再在 category 内按字母顺序排序，例如 `Zicsr_Zifencei_Zam`。

带 `Z` prefix 的 extensions 必须通过 underscore 与其他 multi-letter extensions 分隔，例如 `RV32IMACZicsr_Zifencei`。

## 27.7 Supervisor-level Instruction-Set Extensions

standard supervisor-level instruction-set extensions 在 Volume II 中定义，但命名时使用 `S` 作为 prefix，后跟 alphabetical name 和可选 version number。Supervisor-level extensions 必须通过 underscore 与其他 multi-letter extensions 分隔。

standard supervisor-level extensions 应列在 standard unprivileged extensions 之后。如果列出多个 supervisor-level extensions，它们应按字母顺序排序。

## 27.8 Hypervisor-level Instruction-Set Extensions

standard hypervisor-level instruction-set extensions 的命名方式与 supervisor-level extensions 相同，但以字母 `H` 开始，而不是字母 `S`。

standard hypervisor-level extensions 应列在 standard lesser-privileged extensions 之后。如果列出多个 hypervisor-level extensions，它们应按字母顺序排序。

## 27.9 Machine-level Instruction-Set Extensions

standard machine-level instruction-set extensions 使用三个字母 `Zxm` 作为 prefix。

standard machine-level extensions 应列在 standard lesser-privileged extensions 之后。如果列出多个 machine-level extensions，它们应按字母顺序排序。

## 27.10 Non-Standard Extension Names

non-standard extensions 使用单个 `X` 后跟 alphabetical name 和可选 version number 来命名。例如，`Xhwacha` 命名 Hwacha vector-fetch ISA extension；`Xhwacha2` 和 `Xhwacha2p0` 命名同一扩展的 2.0 版。

non-standard extensions 必须列在所有 standard extensions 之后。它们必须通过 underscore 与其他 multi-letter extensions 分隔。例如，带有 non-standard extensions Argle 和 Bargle 的 ISA 可以命名为 `RV64IZifencei_Xargle_Xbargle`。

如果列出多个 non-standard extensions，它们应按字母顺序排序。

## 27.11 Subset Naming Convention

表 27.1 总结标准化 extension names。

表 27.1：standard ISA extension names。本表也定义 extension names 必须在 name string 中出现的 canonical order；表中从上到下表示 name string 中从前到后。例如，`RV32IMACV` 是合法的，而 `RV32IMAVC` 不是。

| Subset | Name | Implies |
|---|---|---|
| Base ISA: Integer | `I` |  |
| Base ISA: Reduced Integer | `E` |  |
| Integer Multiplication and Division | `M` |  |
| Atomics | `A` |  |
| Single-Precision Floating-Point | `F` | `Zicsr` |
| Double-Precision Floating-Point | `D` | `F` |
| General | `G` | `IMADZifencei` |
| Quad-Precision Floating-Point | `Q` | `D` |
| Decimal Floating-Point | `L` |  |
| 16-bit Compressed Instructions | `C` |  |
| Bit Manipulation | `B` |  |
| Dynamic Languages | `J` |  |
| Transactional Memory | `T` |  |
| Packed-SIMD Extensions | `P` |  |
| Vector Extensions | `V` |  |
| User-Level Interrupts | `N` |  |
| Control and Status Register Access | `Zicsr` |  |
| Instruction-Fetch Fence | `Zifencei` |  |
| Misaligned Atomics | `Zam` | `A` |
| Total Store Ordering | `Ztso` |  |
| Standard Supervisor-Level extension `def` | `Sdef` |  |
| Standard Hypervisor-Level extension `ghi` | `Hghi` |  |
| Standard Machine-Level extension `jkl` | `Zxmjkl` |  |
| Non-standard extension `mno` | `Xmno` |  |
