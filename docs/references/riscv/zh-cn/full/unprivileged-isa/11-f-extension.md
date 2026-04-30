# Chapter 11 `F` Standard Extension for Single-Precision Floating-Point, Version 2.2

本章定义标准单精度浮点扩展 `F`，版本 2.2。`F` 扩展按照 IEEE 754-2008 浮点算术标准提供单精度浮点计算、比较、转换、加载、存储以及浮点控制状态。除特别说明外，本章中的浮点操作采用 IEEE 754 语义；指令名、寄存器名、CSR 名和字段名保持原文。

## 11.1 `F` Register State

`F` 扩展在用户可见状态中增加 32 个浮点寄存器 `f0`-`f31`，每个寄存器宽度为 32 位，并增加一个浮点控制和状态寄存器 `fcsr`。若实现只支持 `F` 扩展，则浮点寄存器宽度 `FLEN` 为 32。后续更宽的浮点扩展会扩展同一组浮点寄存器的宽度。

单精度浮点值以 IEEE 754 binary32 格式保存在浮点寄存器中。`F` 扩展提供专门的浮点 load/store 指令，在浮点寄存器和内存之间移动单精度值；也提供在整数寄存器和浮点寄存器之间按位移动或数值转换的指令。

图 11.1：RISC-V 标准 `F` 扩展的单精度浮点寄存器状态。`f0`-`f31` 是 32 个 32 位浮点寄存器；`fcsr` 是浮点控制和状态寄存器。

> Commentary
>
> 本 ISA 将浮点寄存器组与整数寄存器组分离，而不是使用统一寄存器组。这种设计可以增加可由寄存器保存的总状态，简化支持较宽内部浮点表示的实现，并减少整数代码与浮点代码之间的寄存器端口竞争。分离寄存器组也让只需要整数执行单元的简单实现不必承担浮点寄存器端口和旁路网络的成本。代价是需要显式的浮点和整数寄存器间移动、转换指令，但这些指令在常见 ABI 和编译器生成代码中数量较少。

## 11.2 Floating-Point Control and Status Register

浮点控制和状态寄存器 `fcsr` 是 32 位读写 CSR。它保存动态舍入模式字段 `frm` 和累计异常标志字段 `fflags`。`frm` 控制使用动态舍入模式的浮点指令；`fflags` 记录浮点运算期间产生的 IEEE 754 异常标志。软件可以显式读取、写入或清除这些字段。

`fcsr` 的低 5 位是累计异常标志 `fflags`，位 7 到位 5 是动态舍入模式 `frm`。位 31 到位 8 保留用于其他标准扩展；如果不存在这些扩展，实现应保留这些位。软件在写 `fcsr` 时应避免破坏保留位，通常应通过读-改-写方式只修改已定义字段。

图 11.2：浮点控制和状态寄存器 `fcsr`。`fflags` 位于 `fcsr[4:0]`，`frm` 位于 `fcsr[7:5]`，其余高位保留。

为方便访问 `fcsr` 的不同部分，汇编器定义若干伪指令。`FRCSR` 读取整个 `fcsr`，`FSCSR` 交换整个 `fcsr`；`FRRM` 读取 `frm`，`FSRM` 交换 `frm`；`FRFLAGS` 读取 `fflags`，`FSFLAGS` 交换 `fflags`。这些伪指令通常扩展为 `Zicsr` 中定义的 CSR 指令。

位 31 到位 8 当前保留给其他标准扩展。如果这些扩展没有实现，这些位应在写入时被保留，在读取时返回 0 或实现定义的保留值；可移植软件不应依赖这些位的值。

浮点指令可以使用静态舍入模式，也可以使用动态舍入模式。大多数会产生舍入结果的浮点指令在指令编码中带有 `rm` 字段。当 `rm` 编码为 `111` 时，指令使用 `frm` 中的动态舍入模式；当 `rm` 编码为其他已定义值时，指令使用对应的静态舍入模式。`frm` 中的保留编码 `101`、`110` 和 `111` 是无效动态舍入模式。若指令因 `rm=111` 使用动态舍入模式，而 `frm` 的值为无效编码，则该指令应产生 illegal-instruction exception。

表 11.1 给出舍入模式编码。

| `rm` 编码 | 名称 | 含义 |
|---|---|---|
| `000` | `RNE` | 舍入到最接近值；若距离相等，选择偶数尾数 |
| `001` | `RTZ` | 向 0 舍入 |
| `010` | `RDN` | 向下舍入，即向负无穷舍入 |
| `011` | `RUP` | 向上舍入，即向正无穷舍入 |
| `100` | `RMM` | 舍入到最接近值；若距离相等，选择绝对值较大者 |
| `101` | - | 保留，作为静态舍入模式无效 |
| `110` | - | 保留，作为静态舍入模式无效 |
| `111` | `DYN` | 在指令 `rm` 字段中表示使用 `frm` 动态舍入模式；在 `frm` 中为无效值 |

> Commentary
>
> C99 语言标准实际要求支持动态舍入模式。将舍入模式编码在指令中可以让常见静态舍入操作避免修改 `frm`，但仍保留通过 `frm` 支持动态舍入的能力。修改动态舍入模式可能导致流水线串行化，因为实现必须保证后续浮点指令看到新的模式。

累计异常标志记录浮点操作中发生的异常条件。标志为累计式：一旦某个异常标志被置位，它会保持置位，直到软件显式清除。浮点异常不会在基础浮点 ISA 中自动触发 trap。

表 11.2 给出异常标志编码。

| 位 | 助记名 | 含义 |
|---|---|---|
| 4 | `NV` | Invalid Operation，无效操作 |
| 3 | `DZ` | Divide by Zero，除以零 |
| 2 | `OF` | Overflow，上溢 |
| 1 | `UF` | Underflow，下溢 |
| 0 | `NX` | Inexact，不精确 |

> Commentary
>
> 基础 ISA 不支持浮点异常上的硬件 trap。标准做法是让软件在需要时显式检查 `fflags`。曾经考虑过增加基于异常标志的分支指令以加速检查，但这会增加 ISA 状态和指令复杂度；对于常见代码，显式读标志的方式已经足够。

## 11.3 NaN Generation and Propagation

除非某条指令另有规定，任何产生 NaN 结果的浮点操作都返回默认的规范 NaN。对于单精度，规范 NaN 的符号位为正，指数位全为 1，有效数字字段除最高有效位即 quiet bit 之外全为 0，其位模式为 `0x7fc00000`。

当一个操作数为 NaN，或操作由于无效条件需要返回 NaN 时，结果采用该规范 NaN。指令语义中若要求保留原始位模式，例如某些 move 指令或 load/store 指令，则不适用此规范化规则。

> Commentary
>
> IEEE 754 允许实现传播 NaN payload，使结果中保留关于产生 NaN 原因的信息。RISC-V 基础浮点 ISA 选择要求规范 NaN，以降低实现成本并保持结果可预测。实现可以在非标准模式中支持 NaN payload 传播，但标准模式必须支持并默认采用规范 NaN。

IEEE 754 为异常条件定义默认结果，这允许用户软件在没有异常处理程序介入时继续执行。RISC-V 基础浮点 ISA 采用这些默认结果，并通过 `fflags` 记录异常。机器模式软件仍可通过其他机制模拟更复杂的异常处理策略，但这不属于基础用户级浮点 ISA 的直接语义。

## 11.4 Subnormal Arithmetic

`F` 扩展要求支持 subnormal 数，并遵循 IEEE 754-2008 对 subnormal 算术的要求。subnormal 数参与运算时应按照标准语义处理，而不是被强制清零。

tininess 的检测在舍入之后进行。也就是说，下溢异常的判定基于舍入后的结果是否 tiny，并结合是否发生不精确。

> Commentary
>
> 在舍入之后检测 tininess 可以减少虚假的 underflow 信号。某些中间结果在舍入前看起来非常小，但舍入后可能成为正常数；若在舍入前检测，就会报告软件通常不关心的下溢。

## 11.5 Single-Precision Load and Store Instructions

浮点 load/store 指令使用与整数基础 ISA 相同的基址加偏移地址计算方式。有效地址由整数寄存器 `rs1` 的值与符号扩展的 12 位字节偏移相加得到。

`FLW` 从内存加载一个单精度浮点值，并写入浮点寄存器 `rd`。`FSW` 将浮点寄存器 `rs2` 中的单精度值存入内存。

`FLW` 和 `FSW` 的编码位于 `LOAD-FP` 和 `STORE-FP` 主操作码空间中。`width` 字段选择单精度宽度 `W`。

| 指令类别 | 编码字段 | 含义 |
|---|---|---|
| `LOAD-FP` | `imm[11:0] rs1 width rd opcode` | 使用 `rs1` 加 12 位偏移形成地址，将宽度为 `W` 的单精度值加载到目的浮点寄存器 |
| `STORE-FP` | `imm[11:5] rs2 rs1 width imm[4:0] opcode` | 使用 `rs1` 加 12 位偏移形成地址，将源浮点寄存器中的单精度值存储到内存 |

`FLW` 和 `FSW` 只有在有效地址自然对齐时才保证原子性。单精度自然对齐要求地址按 4 字节对齐。未对齐访问的行为遵循执行环境和内存系统对未对齐 load/store 的规定。

`FLW` 和 `FSW` 不会修改所搬运位模式中的任何位。因此，非规范 NaN 的 payload 会在 load/store 过程中被保留。

## 11.6 Single-Precision Floating-Point Computational Instructions

单精度浮点计算指令使用 `OP-FP` 主操作码。大多数二元计算指令采用 R-type 格式，源操作数来自浮点寄存器 `rs1` 和 `rs2`，结果写入浮点寄存器 `rd`。`fmt` 字段指示浮点格式；对于 `F` 扩展中的单精度操作，`fmt=S`。

表 11.3 给出标准浮点格式编码。

| `fmt` 编码 | 名称 | 浮点格式 |
|---|---|---|
| `00` | `S` | 32 位单精度 |
| `01` | `D` | 64 位双精度 |
| `10` | `H` | 16 位半精度 |
| `11` | `Q` | 128 位四精度 |

`FADD.S` 和 `FSUB.S` 分别执行单精度浮点加法和减法。`FMUL.S` 执行单精度浮点乘法。`FDIV.S` 执行单精度浮点除法。`FSQRT.S` 执行单精度平方根运算，只有一个源操作数，第二源字段编码为 0。

这些会舍入结果的运算使用 `rm` 字段指定舍入模式。`rm` 可以给出静态舍入模式，也可以编码为 `111` 以使用 `frm` 中的动态舍入模式。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FADD.S` | `FADD S src2 src1 RM dest OP-FP` | `rd = rs1 + rs2`，按 `RM` 舍入 |
| `FSUB.S` | `FSUB S src2 src1 RM dest OP-FP` | `rd = rs1 - rs2`，按 `RM` 舍入 |
| `FMUL.S` | `FMUL S src2 src1 RM dest OP-FP` | `rd = rs1 * rs2`，按 `RM` 舍入 |
| `FDIV.S` | `FDIV S src2 src1 RM dest OP-FP` | `rd = rs1 / rs2`，按 `RM` 舍入 |
| `FSQRT.S` | `FSQRT S 0 src RM dest OP-FP` | `rd = sqrt(rs1)`，按 `RM` 舍入 |

`FMIN.S` 和 `FMAX.S` 分别返回两个单精度操作数中的最小值和最大值。对于有符号零，`-0.0` 小于 `+0.0`。如果两个输入都是 NaN，结果为规范 NaN。如果只有一个输入是 NaN，结果为另一个非 NaN 输入。若任一输入是 signaling NaN，则设置 invalid operation 标志，即使结果不是 NaN。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FMIN.S` | `FMIN-MAX S src2 src1 MIN dest OP-FP` | 选择 `rs1` 与 `rs2` 中较小的单精度值 |
| `FMAX.S` | `FMIN-MAX S src2 src1 MAX dest OP-FP` | 选择 `rs1` 与 `rs2` 中较大的单精度值 |

> Commentary
>
> 版本 2.2 修改了 `FMIN.S` 和 `FMAX.S` 对 signaling NaN 的处理，使其匹配 IEEE 754-201x 中的 `minimumNumber` 和 `maximumNumber` 操作，而不是 IEEE 754-2008 中的 `minNum` 和 `maxNum`。关键差异在于 signaling NaN 会设置 invalid operation 标志。

融合乘加指令使用 R4-type 格式，包含三个源浮点寄存器 `rs1`、`rs2`、`rs3` 和一个目的浮点寄存器 `rd`。这些指令在无限精度下计算乘积和加数的组合，然后只进行一次舍入。

`FMADD.S` 计算 `(rs1 * rs2) + rs3`。`FMSUB.S` 计算 `(rs1 * rs2) - rs3`。`FNMSUB.S` 计算 `-(rs1 * rs2) + rs3`。`FNMADD.S` 计算 `-(rs1 * rs2) - rs3`。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FMADD.S` | `src3 S src2 src1 RM dest FMADD` | `rd = (rs1 * rs2) + rs3`，融合计算并按 `RM` 舍入 |
| `FMSUB.S` | `src3 S src2 src1 RM dest FMSUB` | `rd = (rs1 * rs2) - rs3`，融合计算并按 `RM` 舍入 |
| `FNMSUB.S` | `src3 S src2 src1 RM dest FNMSUB` | `rd = -(rs1 * rs2) + rs3`，融合计算并按 `RM` 舍入 |
| `FNMADD.S` | `src3 S src2 src1 RM dest FNMADD` | `rd = -(rs1 * rs2) - rs3`，融合计算并按 `RM` 舍入 |

R4-type 编码字段顺序为 `rs3 fmt rs2 rs1 rm rd opcode`。`fmt=S` 表示单精度，`rm` 指定舍入模式。

> Commentary
>
> 这些指令名称可能显得不直观，这是因为它们继承了 MIPS-IV 中的命名风格。RISC-V 的 `FNMSUB.S` 和 `FNMADD.S` 语义与 x86 和 ARM 中对应硬件操作一致，但名称中的否定位置与某些其他 ISA 的助记名约定不同。标准选择当前命名是为了与早期 RISC 浮点 ISA 的传统保持一致。

> Commentary
>
> 融合乘加指令使用独立 R4 编码空间，是为了保持三个源寄存器的正交性，并避免把 `rd` 强制复用为某个源寄存器。设计过程中也考虑过其他格式，例如将加数放在 `rd` 中，或减少静态舍入字段，但这些方案会降低编译器调度自由度或牺牲 IEEE 754 操作的通用性。保留静态舍入字段也让数值库可以在不修改 `frm` 的情况下选择舍入模式。

如果融合乘加中的乘法部分为无穷乘以零，则即使加数是 quiet NaN，也应设置 invalid operation 标志。IEEE 754 对 `∞ × 0 + qNaN` 是否必须报告 invalid 留有一定选择；RISC-V 指定设置该标志，以获得确定行为。

## 11.7 Single-Precision Floating-Point Conversion and Move Instructions

浮点到整数转换指令将单精度浮点源操作数转换为整数结果，并写入整数寄存器 `rd`。`FCVT.W.S` 将单精度浮点数转换为有符号 32 位整数，`FCVT.WU.S` 转换为无符号 32 位整数。`FCVT.L.S` 和 `FCVT.LU.S` 分别转换为有符号和无符号 64 位整数，它们只在 RV64 及更宽 XLEN 中定义。

整数到浮点转换指令将整数寄存器源操作数转换为单精度浮点结果，并写入浮点寄存器 `rd`。`FCVT.S.W` 和 `FCVT.S.WU` 分别从有符号和无符号 32 位整数转换；`FCVT.S.L` 和 `FCVT.S.LU` 分别从有符号和无符号 64 位整数转换，并且只在 RV64 及更宽 XLEN 中定义。

当 `XLEN > 32` 时，`FCVT.W.S` 和 `FCVT.WU.S` 的 32 位整数结果会符号扩展到整数寄存器的 XLEN 位宽。浮点到整数转换和整数到浮点转换都按照 `rm` 字段指定的舍入模式执行。

若浮点到整数转换的舍入结果不能由目标整数类型表示，则结果被裁剪到最接近的可表示值，并设置 invalid operation 标志。表 11.4 给出不同转换的输入范围和无效转换结果。

| 条件 | `FCVT.W.S` | `FCVT.WU.S` | `FCVT.L.S` | `FCVT.LU.S` |
|---|---:|---:|---:|---:|
| 舍入后的最小有效输入 | `-2^31` | `0` | `-2^63` | `0` |
| 舍入后的最大有效输入 | `2^31 - 1` | `2^32 - 1` | `2^63 - 1` | `2^64 - 1` |
| 小于范围的负输入的输出 | `-2^31` | `0` | `-2^63` | `0` |
| `-∞` 的输出 | `-2^31` | `0` | `-2^63` | `0` |
| 大于范围的正输入的输出 | `2^31 - 1` | `2^32 - 1` | `2^63 - 1` | `2^64 - 1` |
| `+∞` 或 NaN 的输出 | `2^31 - 1` | `2^32 - 1` | `2^63 - 1` | `2^64 - 1` |

| 指令类别 | 编码概要 | 语义 |
|---|---|---|
| `FCVT.int.fmt` | `FCVT.int.fmt S W[U]/L[U] src RM dest OP-FP` | 将单精度浮点源转换为整数目的寄存器 |
| `FCVT.fmt.int` | `FCVT.fmt.int S W[U]/L[U] src RM dest OP-FP` | 将整数源寄存器转换为单精度浮点目的寄存器 |

浮点寄存器可以通过 `FCVT.S.W rd, x0` 初始化为 `+0.0`，该转换不会设置任何异常标志。

符号注入指令 `FSGNJ.S`、`FSGNJN.S` 和 `FSGNJX.S` 从 `rs1` 复制除符号位以外的所有位，并根据 `rs2` 的符号位生成结果符号。`FSGNJ.S` 使用 `rs2` 的符号位；`FSGNJN.S` 使用 `rs2` 符号位的反；`FSGNJX.S` 使用 `rs1` 和 `rs2` 符号位的异或。这些指令不设置异常标志，也不会把 NaN 规范化。

当两个源寄存器相同时，符号注入指令可作为常用伪指令使用：`FSGNJ.S rx, ry, ry` 是 `FMV.S rx, ry`；`FSGNJN.S rx, ry, ry` 是 `FNEG.S rx, ry`；`FSGNJX.S rx, ry, ry` 是 `FABS.S rx, ry`。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FSGNJ.S` | `FSGNJ S src2 src1 J dest OP-FP` | 复制 `rs1` 的数值位，符号来自 `rs2` |
| `FSGNJN.S` | `FSGNJ S src2 src1 JN dest OP-FP` | 复制 `rs1` 的数值位，符号为 `rs2` 符号取反 |
| `FSGNJX.S` | `FSGNJ S src2 src1 JX dest OP-FP` | 复制 `rs1` 的数值位，符号为 `rs1` 与 `rs2` 符号异或 |

> Commentary
>
> 符号注入指令支持 move、negate、absolute value 以及 `copySign` 这类操作，也能服务于某些超越函数库。微架构可以检测两个源寄存器相同的情形，并把这些常用形式实现为更简单的数据移动、取反或取绝对值操作。

按位移动指令在整数寄存器和浮点寄存器之间移动单精度位模式。`FMV.X.W` 将浮点寄存器 `rs1` 的单精度位模式移动到整数寄存器 `rd` 的低 32 位；在 RV64 中，高位用单精度符号位填充。`FMV.W.X` 将整数寄存器 `rs1` 的低 32 位移动到浮点寄存器 `rd`。这些指令保留所有位，包括非规范 NaN payload。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FMV.X.W` | `FMV.X.W S 0 src 000 dest OP-FP` | 将浮点寄存器中的 32 位模式移到整数寄存器 |
| `FMV.W.X` | `FMV.W.X S 0 src 000 dest OP-FP` | 将整数寄存器低 32 位模式移到浮点寄存器 |

这些指令曾称为 `FMV.X.S` 和 `FMV.S.X`。后来改名为使用 `W` 后缀，以便更清楚地表示移动的是 32 位字宽位模式。工具链可以继续接受旧助记名作为别名。

> Commentary
>
> 某些实现会在浮点寄存器内部使用重新编码的浮点格式。ISA 尽量避免要求整数值长期驻留在浮点寄存器中；数值转换和比较结果直接与整数寄存器组交互，可以减少在整数寄存器组和浮点寄存器组之间搬运数据的需求。

## 11.8 Single-Precision Floating-Point Compare Instructions

单精度比较指令比较浮点寄存器 `rs1` 和 `rs2`，并把布尔结果写入整数寄存器 `rd`。如果比较为真，`rd` 写入 1；否则写入 0。

`FEQ.S` 测试 `rs1` 是否等于 `rs2`。`FLT.S` 测试 `rs1` 是否小于 `rs2`。`FLE.S` 测试 `rs1` 是否小于或等于 `rs2`。

`FLT.S` 和 `FLE.S` 是 signaling comparisons：如果任一输入为 NaN，则设置 invalid operation 标志。`FEQ.S` 是 quiet comparison：只有当输入为 signaling NaN 时才设置 invalid operation 标志。如果任一操作数为 NaN，三种比较都返回 0。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FEQ.S` | `FCMP S src2 src1 EQ dest OP-FP` | 若 `rs1 == rs2`，整数 `rd=1`，否则 `rd=0` |
| `FLT.S` | `FCMP S src2 src1 LT dest OP-FP` | 若 `rs1 < rs2`，整数 `rd=1`，否则 `rd=0` |
| `FLE.S` | `FCMP S src2 src1 LE dest OP-FP` | 若 `rs1 <= rs2`，整数 `rd=1`，否则 `rd=0` |

> Commentary
>
> `F` 扩展包含小于或等于比较，而基础整数 ISA 中的条件分支提供的是大于或等于形式。这种不一致不会导致明显性能问题，因为整数寄存器中的比较结果可以由后续分支使用，但从 ISA 设计美感上看并不理想。

## 11.9 Single-Precision Floating-Point Classify Instruction

`FCLASS.S` 检查浮点寄存器 `rs1` 中的单精度值类别，并将一个 10 位掩码写入整数寄存器 `rd`。结果中恰好有一个位被置 1，其余位为 0。该指令不设置浮点异常标志。

编码概要为 `FCLASS S 0 src 001 dest OP-FP`。

表 11.5 给出 `FCLASS.S` 结果位含义。

| `rd` 位 | 条件 |
|---:|---|
| 0 | `rs1` 为 `-∞` |
| 1 | `rs1` 为负正规数 |
| 2 | `rs1` 为负 subnormal 数 |
| 3 | `rs1` 为 `-0` |
| 4 | `rs1` 为 `+0` |
| 5 | `rs1` 为正 subnormal 数 |
| 6 | `rs1` 为正正规数 |
| 7 | `rs1` 为 `+∞` |
| 8 | `rs1` 为 signaling NaN |
| 9 | `rs1` 为 quiet NaN |
