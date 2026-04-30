# Chapter 12 `D` Standard Extension for Double-Precision Floating-Point, Version 2.2

本章描述标准双精度浮点指令集扩展，扩展名为 `D`。`D` 扩展增加符合 IEEE 754-2008 算术标准的双精度浮点计算指令。`D` 扩展依赖基础单精度指令子集 `F`。

## 12.1 `D` Register State

`D` 扩展将 32 个浮点寄存器 `f0`-`f31` 扩宽到 64 位，即 `FLEN=64`。这些 `f` 寄存器现在可以保存 32 位或 64 位浮点值，具体表示方式见 12.2 节。

`FLEN` 可以是 32、64 或 128，取决于实现支持 `F`、`D` 和 `Q` 扩展中的哪些扩展。一个实现最多可以支持四种不同的浮点精度，包括 `H`、`F`、`D` 和 `Q`。

## 12.2 NaN Boxing of Narrower Values

当支持多种浮点精度时，有效的较窄 `n` 位类型值，其中 `n < FLEN`，以一个 `FLEN` 位 NaN 值的低 `n` 位表示；这个过程称为 NaN-boxing。有效 NaN-boxed 值的高位必须全为 1。因此，当把一个有效的 NaN-boxed `n` 位值当作任意更宽的 `m` 位值查看时，其中 `n < m <= FLEN`，它会表现为一个负 quiet NaN，即负 qNaN。任何把较窄结果写入 `f` 寄存器的操作，都必须把最高的 `FLEN - n` 位写为全 1，从而生成合法的 NaN-boxed 值。

软件可能不知道浮点寄存器中当前保存的数据类型，但仍必须能够保存并恢复寄存器值。因此，使用较宽操作传送较窄值时的结果必须被定义。常见场景包括 callee-saved registers；同时，varargs、用户级线程库、虚拟机迁移和调试等功能也需要一套标准约定。

浮点 `n` 位传送操作把以 IEEE 标准格式保存的外部值移入或移出 `f` 寄存器。这些操作包括浮点 load/store，即 `FLn`/`FSn`，以及浮点 move 指令，即 `FMV.n.X`/`FMV.X.n`。一个写入 `f` 寄存器的较窄 `n` 位传送，其中 `n < FLEN`，会创建一个有效的 NaN-boxed 值。一个从浮点寄存器读出的较窄 `n` 位传送，会传送寄存器低 `n` 位，并忽略高 `FLEN - n` 位。

除前一段描述的传送操作外，所有其他作用于较窄 `n` 位操作数的浮点操作，其中 `n < FLEN`，都会检查输入操作数是否被正确 NaN-boxed，也就是高 `FLEN - n` 位是否全为 1。如果检查通过，输入的最低 `n` 位作为输入值使用；否则，输入值被视为一个 `n` 位规范 NaN。

本文档的早期版本没有定义把较窄或较宽操作数的结果送入某个操作时的行为，只要求较宽的保存和恢复能够保留较窄操作数的值。新的定义消除了这种实现相关行为，同时仍能适应非重编码和重编码两类浮点单元实现。新的定义也有助于捕获软件错误，因为错误使用值时会传播 NaN。

> Commentary
>
> 非重编码实现会在每个浮点操作的输入和输出处，把操作数解包和打包为 IEEE 标准格式。对非重编码实现来说，NaN-boxing 的成本主要在于检查较窄操作的高位是否表示合法的 NaN-boxed 值，以及在结果高位写入全 1。

> Commentary
>
> 重编码实现使用更方便的内部格式表示浮点值，并增加一个指数位，使所有值都可以按规格化形式保存。对重编码实现来说，主要成本是额外的标记，用来跟踪内部类型和符号位；不过这可以通过在内部对 NaN 的指数域重新编码来完成，而不必增加新的状态位。在数值移入和移出重编码格式的流水线上需要做一些小修改，但数据通路和延迟成本很小。无论如何，重编码过程都必须处理宽操作数中输入 subnormal 值的移位；提取 NaN-boxed 值与规格化过程类似，只是跳过前导 1 而不是跳过前导 0，因此可以共享数据通路复用逻辑。

## 12.3 Double-Precision Load and Store Instructions

`FLD` 指令从内存加载一个双精度浮点值，并写入浮点寄存器 `rd`。`FSD` 将浮点寄存器中的双精度值存入内存。这个双精度值也可以是一个 NaN-boxed 单精度值。

`FLD` 使用 `LOAD-FP` 主操作码空间，采用基址加偏移地址计算方式。有效地址由整数寄存器 `rs1` 与符号扩展的 12 位字节偏移相加得到，`width` 字段为 `D`。

| 指令类别 | 编码字段 | 含义 |
|---|---|---|
| `LOAD-FP` | `imm[11:0] rs1 width rd opcode` | 使用 `rs1` 加 12 位偏移形成地址，将宽度为 `D` 的双精度值加载到目的浮点寄存器 |
| 字段说明 | `offset[11:0] base D dest LOAD-FP` | `offset` 是字节偏移，`base` 是基址整数寄存器，`dest` 是目的浮点寄存器 |

`FSD` 使用 `STORE-FP` 主操作码空间，同样采用基址加偏移地址计算方式，`width` 字段为 `D`。

| 指令类别 | 编码字段 | 含义 |
|---|---|---|
| `STORE-FP` | `imm[11:5] rs2 rs1 width imm[4:0] opcode` | 使用 `rs1` 加 12 位偏移形成地址，将源浮点寄存器中的双精度值存储到内存 |
| 字段说明 | `offset[11:5] src base D offset[4:0] STORE-FP` | `src` 是源浮点寄存器，`base` 是基址整数寄存器，`offset` 是字节偏移 |

`FLD` 和 `FSD` 只有在有效地址自然对齐且 `XLEN >= 64` 时才保证原子执行。双精度自然对齐要求地址按 8 字节对齐。

`FLD` 和 `FSD` 不会修改被传送的位；特别是，非规范 NaN 的 payload 会被保留。

## 12.4 Double-Precision Floating-Point Computational Instructions

双精度浮点计算指令与对应的单精度指令按类似方式定义，但它们作用于双精度操作数，并产生双精度结果。

这些指令使用 `OP-FP` 主操作码空间，`fmt` 字段为 `D`。`rm` 字段指定舍入模式，含义与 `F` 扩展中相同。

| 指令族 | 编码概要 | 语义 |
|---|---|---|
| `FADD.D`/`FSUB.D` | `FADD/FSUB D src2 src1 RM dest OP-FP` | 对双精度操作数执行加法或减法，并按 `RM` 舍入 |
| `FMUL.D`/`FDIV.D` | `FMUL/FDIV D src2 src1 RM dest OP-FP` | 对双精度操作数执行乘法或除法，并按 `RM` 舍入 |
| `FMIN.D`/`FMAX.D` | `FMIN-MAX D src2 src1 MIN/MAX dest OP-FP` | 选择两个双精度操作数中的最小值或最大值 |
| `FSQRT.D` | `FSQRT D 0 src RM dest OP-FP` | 对双精度操作数求平方根，并按 `RM` 舍入 |

双精度融合乘加指令也与单精度对应指令类似定义，但 `fmt` 字段为 `D`，源和目的均为双精度浮点值。

| 指令族 | 编码概要 | 语义 |
|---|---|---|
| `FMADD.D`/`FMSUB.D`/`FNMADD.D`/`FNMSUB.D` | `src3 D src2 src1 RM dest F[N]MADD/F[N]MSUB` | 对双精度操作数执行融合乘加或融合乘减，只进行一次最终舍入 |

## 12.5 Double-Precision Floating-Point Conversion and Move Instructions

浮点到整数转换和整数到浮点转换指令编码在 `OP-FP` 主操作码空间中。`FCVT.W.D` 或 `FCVT.L.D` 分别把浮点寄存器 `rs1` 中的双精度浮点数转换为有符号 32 位或 64 位整数，并写入整数寄存器 `rd`。`FCVT.D.W` 或 `FCVT.D.L` 分别把整数寄存器 `rs1` 中的有符号 32 位或 64 位整数转换为双精度浮点数，并写入浮点寄存器 `rd`。

`FCVT.WU.D`、`FCVT.LU.D`、`FCVT.D.WU` 和 `FCVT.D.LU` 变体在无符号整数值和双精度浮点值之间转换。对于 RV64，`FCVT.W[U].D` 会把 32 位结果符号扩展到 `XLEN`。`FCVT.L[U].D` 和 `FCVT.D.L[U]` 是仅 RV64 定义的指令。`FCVT.int.D` 的有效输入范围以及无效输入行为与 `FCVT.int.S` 相同。

所有浮点到整数转换和整数到浮点转换指令都按照 `rm` 字段舍入。注意，`FCVT.D.W[U]` 总是产生精确结果，因此不受舍入模式影响。

| 指令类别 | 编码概要 | 语义 |
|---|---|---|
| `FCVT.int.D` | `FCVT.int.D D W[U]/L[U] src RM dest OP-FP` | 将双精度浮点源转换为整数目的寄存器 |
| `FCVT.D.int` | `FCVT.D.int D W[U]/L[U] src RM dest OP-FP` | 将整数源寄存器转换为双精度浮点目的寄存器 |

双精度到单精度以及单精度到双精度转换指令 `FCVT.S.D` 和 `FCVT.D.S` 编码在 `OP-FP` 主操作码空间中，并且源和目的都是浮点寄存器。`rs2` 字段编码源数据类型，`fmt` 字段编码目的数据类型。`FCVT.S.D` 按照 `RM` 字段舍入；`FCVT.D.S` 永远不需要舍入。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FCVT.S.D` | `FCVT.S.D S D src RM dest OP-FP` | 将双精度源转换为单精度目的，按 `RM` 舍入 |
| `FCVT.D.S` | `FCVT.D.S D S src RM dest OP-FP` | 将单精度源转换为双精度目的，不发生舍入 |

浮点到浮点符号注入指令 `FSGNJ.D`、`FSGNJN.D` 和 `FSGNJX.D` 与单精度符号注入指令按类似方式定义。

| 指令族 | 编码概要 | 语义 |
|---|---|---|
| `FSGNJ.D`/`FSGNJN.D`/`FSGNJX.D` | `FSGNJ D src2 src1 J[N]/JX dest OP-FP` | 复制双精度源的数值位，并按 `J`、`JN` 或 `JX` 规则生成符号位 |

仅当 `XLEN >= 64` 时，ISA 提供在浮点寄存器和整数寄存器之间移动位模式的指令。`FMV.X.D` 将浮点寄存器 `rs1` 中的双精度值，以 IEEE 754-2008 标准编码表示形式移动到整数寄存器 `rd`。`FMV.D.X` 将整数寄存器 `rs1` 中按 IEEE 754-2008 标准编码的双精度值移动到浮点寄存器 `rd`。

`FMV.X.D` 和 `FMV.D.X` 不会修改被传送的位；特别是，非规范 NaN 的 payload 会被保留。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FMV.X.D` | `FMV.X.D D 0 src 000 dest OP-FP` | 将浮点寄存器中的 64 位双精度位模式移到整数寄存器 |
| `FMV.D.X` | `FMV.D.X D 0 src 000 dest OP-FP` | 将整数寄存器中的 64 位位模式移到浮点寄存器 |

> Commentary
>
> RISC-V ISA 的早期版本曾包含额外指令，允许 RV32 系统在 64 位浮点寄存器的高半部分、低半部分与整数寄存器之间传送数据。然而，这些会是 ISA 中仅有的部分寄存器写指令，并会给采用重编码浮点或寄存器重命名的实现增加复杂度，因为流水线需要执行读-改-写序列。如果按同一模式扩展到四精度，RV32 和 RV64 也需要更多额外指令。ISA 的定义有意减少显式整数-浮点寄存器移动的数量，让转换和比较把结果写入适当的寄存器组；因此，这些额外指令的收益预计低于其他 ISA 中类似指令的收益。

> Commentary
>
> 对于实现了 64 位浮点单元的系统，如果该浮点单元包括融合乘加支持以及 64 位浮点 load/store，那么从 32 位整数数据通路转向 64 位整数数据通路的边际硬件成本较低。软件 ABI 仍可以使用 32 位宽地址空间和指针，以避免静态数据规模和动态内存流量增长。

## 12.6 Double-Precision Floating-Point Compare Instructions

双精度浮点比较指令与对应的单精度指令按类似方式定义，但它们作用于双精度操作数。

| 指令族 | 编码概要 | 语义 |
|---|---|---|
| `FEQ.D`/`FLT.D`/`FLE.D` | `FCMP D src2 src1 EQ/LT/LE dest OP-FP` | 比较两个双精度操作数，并将布尔结果写入整数目的寄存器 |

比较语义沿用单精度比较：`FEQ.D` 测试相等，`FLT.D` 测试小于，`FLE.D` 测试小于或等于。若比较结果为真，整数目的寄存器写入 1；否则写入 0。NaN 与 signaling NaN 的异常标志行为与单精度对应指令相同。

## 12.7 Double-Precision Floating-Point Classify Instruction

双精度浮点分类指令 `FCLASS.D` 与对应的单精度指令按类似方式定义，但它作用于双精度操作数。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FCLASS.D` | `FCLASS D 0 src 001 dest OP-FP` | 检查双精度源操作数的类别，并将分类掩码写入整数目的寄存器 |

`FCLASS.D` 的结果位含义与 `FCLASS.S` 相同，只是分类对象为双精度值：结果中恰好有一个位被置 1，用以表示负无穷、负正规数、负 subnormal、`-0`、`+0`、正 subnormal、正正规数、正无穷、signaling NaN 或 quiet NaN。
