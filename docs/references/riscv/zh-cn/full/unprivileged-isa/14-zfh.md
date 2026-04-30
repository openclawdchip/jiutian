# Chapter 14 `Zfh` and `Zfhmin` Standard Extensions for Half-Precision Floating-Point, Version 1.0

本章描述 `Zfh` 标准扩展。`Zfh` 扩展提供符合 IEEE 754-2008 算术标准的 16 位半精度二进制浮点指令。`Zfh` 扩展依赖单精度浮点扩展 `F`。

12.2 节描述的 NaN-boxing 方案扩展为允许半精度值 NaN-boxed 到单精度值中；当存在 `D` 或 `Q` 扩展时，这个单精度值还可以递归地 NaN-boxed 到双精度或四精度值中。

本扩展主要提供消费半精度操作数并产生半精度结果的指令。不过，使用更高的中间精度对半精度数据进行计算也很常见。

虽然本扩展提供的显式转换指令已经足以实现这种模式，但未来扩展可能通过额外指令进一步加速此类计算，例如隐式加宽操作数的 `half * half + single -> single`，或隐式缩窄结果的 `half + single -> half`。

## 14.1 Half-Precision Load and Store Instructions

ISA 增加新的 16 位 `LOAD-FP` 和 `STORE-FP` 指令变体，并通过 `funct3` 的 `width` 字段使用新的编码值来表示半精度宽度。

`FLH` 从内存加载一个半精度浮点值到浮点寄存器 `rd`。有效地址由整数寄存器 `rs1` 和符号扩展的 12 位字节偏移相加得到，`width` 字段为 `H`。

| 指令类别 | 编码字段 | 含义 |
|---|---|---|
| `LOAD-FP` | `imm[11:0] rs1 width rd opcode` | 使用 `rs1` 加 12 位偏移形成地址，将宽度为 `H` 的半精度值加载到目的浮点寄存器 |
| 字段说明 | `offset[11:0] base H dest LOAD-FP` | `offset` 是字节偏移，`base` 是基址整数寄存器，`dest` 是目的浮点寄存器 |

`FSH` 将浮点寄存器中的半精度值存入内存。有效地址同样由整数寄存器 `rs1` 和符号扩展的 12 位字节偏移相加得到，`width` 字段为 `H`。

| 指令类别 | 编码字段 | 含义 |
|---|---|---|
| `STORE-FP` | `imm[11:5] rs2 rs1 width imm[4:0] opcode` | 使用 `rs1` 加 12 位偏移形成地址，将源浮点寄存器中的半精度值存储到内存 |
| 字段说明 | `offset[11:5] src base H offset[4:0] STORE-FP` | `src` 是源浮点寄存器，`base` 是基址整数寄存器，`offset` 是字节偏移 |

`FLH` 和 `FSH` 只有在有效地址自然对齐时才保证原子执行。半精度自然对齐要求地址按 2 字节对齐。

`FLH` 和 `FSH` 不会修改被传送的位；特别是，非规范 NaN 的 payload 会被保留。`FLH` 会对写入 `rd` 的结果进行 NaN-boxing，而 `FSH` 会忽略 `rs2` 中除低 16 位以外的所有位。

## 14.2 Half-Precision Computational Instructions

大多数浮点指令的 `fmt` 字段增加一个新的受支持格式，如表 14.1 所示。

表 14.1：`fmt` 字段编码。

| `fmt` 字段 | 助记名 | 含义 |
|---|---|---|
| `00` | `S` | 32 位单精度 |
| `01` | `D` | 64 位双精度 |
| `10` | `H` | 16 位半精度 |
| `11` | `Q` | 128 位四精度 |

半精度浮点计算指令与对应的单精度指令按类似方式定义，但它们作用于半精度操作数，并产生半精度结果。

这些指令使用 `OP-FP` 主操作码空间，`fmt` 字段为 `H`。`rm` 字段指定舍入模式，含义与 `F`、`D` 和 `Q` 扩展中的舍入模式相同。

| 指令族 | 编码概要 | 语义 |
|---|---|---|
| `FADD.H`/`FSUB.H` | `FADD/FSUB H src2 src1 RM dest OP-FP` | 对半精度操作数执行加法或减法，并按 `RM` 舍入 |
| `FMUL.H`/`FDIV.H` | `FMUL/FDIV H src2 src1 RM dest OP-FP` | 对半精度操作数执行乘法或除法，并按 `RM` 舍入 |
| `FMIN.H`/`FMAX.H` | `FMIN-MAX H src2 src1 MIN/MAX dest OP-FP` | 选择两个半精度操作数中的最小值或最大值 |
| `FSQRT.H` | `FSQRT H 0 src RM dest OP-FP` | 对半精度操作数求平方根，并按 `RM` 舍入 |

半精度融合乘加指令与单精度对应指令按类似方式定义，但 `fmt` 字段为 `H`，源和目的均为半精度浮点值。

| 指令族 | 编码概要 | 语义 |
|---|---|---|
| `FMADD.H`/`FMSUB.H`/`FNMADD.H`/`FNMSUB.H` | `src3 H src2 src1 RM dest F[N]MADD/F[N]MSUB` | 对半精度操作数执行融合乘加或融合乘减，只进行一次最终舍入 |

## 14.3 Half-Precision Conversion and Move Instructions

ISA 增加新的浮点到整数转换指令和整数到浮点转换指令。这些指令与单精度到整数、整数到单精度转换指令按类似方式定义。

`FCVT.W.H` 或 `FCVT.L.H` 分别把半精度浮点数转换为有符号 32 位或 64 位整数。`FCVT.H.W` 或 `FCVT.H.L` 分别把 32 位或 64 位有符号整数转换为半精度浮点数。

`FCVT.WU.H`、`FCVT.LU.H`、`FCVT.H.WU` 和 `FCVT.H.LU` 变体在无符号整数值和半精度浮点值之间转换。`FCVT.L[U].H` 和 `FCVT.H.L[U]` 是仅 RV64 定义的指令。

| 指令类别 | 编码概要 | 语义 |
|---|---|---|
| `FCVT.int.H` | `FCVT.int.H H W[U]/L[U] src RM dest OP-FP` | 将半精度浮点源转换为整数目的寄存器 |
| `FCVT.H.int` | `FCVT.H.int H W[U]/L[U] src RM dest OP-FP` | 将整数源寄存器转换为半精度浮点目的寄存器 |

ISA 还增加新的浮点到浮点转换指令。这些指令与双精度浮点到浮点转换指令按类似方式定义。`FCVT.S.H` 或 `FCVT.H.S` 分别把半精度浮点数转换为单精度浮点数，或把单精度浮点数转换为半精度浮点数。

如果存在 `D` 扩展，`FCVT.D.H` 或 `FCVT.H.D` 分别把半精度浮点数转换为双精度浮点数，或把双精度浮点数转换为半精度浮点数。如果存在 `Q` 扩展，`FCVT.Q.H` 或 `FCVT.H.Q` 分别把半精度浮点数转换为四精度浮点数，或把四精度浮点数转换为半精度浮点数。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FCVT.S.H` | `FCVT.S.H S H src RM dest OP-FP` | 将半精度源转换为单精度目的 |
| `FCVT.H.S` | `FCVT.H.S H S src RM dest OP-FP` | 将单精度源转换为半精度目的，并按 `RM` 舍入 |
| `FCVT.D.H` | `FCVT.D.H D H src RM dest OP-FP` | 将半精度源转换为双精度目的 |
| `FCVT.H.D` | `FCVT.H.D H D src RM dest OP-FP` | 将双精度源转换为半精度目的，并按 `RM` 舍入 |
| `FCVT.Q.H` | `FCVT.Q.H Q H src RM dest OP-FP` | 将半精度源转换为四精度目的 |
| `FCVT.H.Q` | `FCVT.H.Q H Q src RM dest OP-FP` | 将四精度源转换为半精度目的，并按 `RM` 舍入 |

浮点到浮点符号注入指令 `FSGNJ.H`、`FSGNJN.H` 和 `FSGNJX.H` 与单精度符号注入指令按类似方式定义。

| 指令族 | 编码概要 | 语义 |
|---|---|---|
| `FSGNJ.H`/`FSGNJN.H`/`FSGNJX.H` | `FSGNJ H src2 src1 J[N]/JX dest OP-FP` | 复制半精度源的数值位，并按 `J`、`JN` 或 `JX` 规则生成符号位 |

ISA 提供在浮点寄存器和整数寄存器之间移动位模式的指令。`FMV.X.H` 将浮点寄存器 `rs1` 中的半精度值，以 IEEE 754-2008 标准编码表示形式移动到整数寄存器 `rd`，并用该浮点数符号位的副本填充高 `XLEN - 16` 位。

`FMV.H.X` 将整数寄存器 `rs1` 低 16 位中按 IEEE 754-2008 标准编码的半精度值移动到浮点寄存器 `rd`，并对结果进行 NaN-boxing。

`FMV.X.H` 和 `FMV.H.X` 不会修改被传送的位；特别是，非规范 NaN 的 payload 会被保留。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FMV.X.H` | `FMV.X.H H 0 src 000 dest OP-FP` | 将浮点寄存器中的 16 位半精度位模式移到整数寄存器，并用符号位填充高位 |
| `FMV.H.X` | `FMV.H.X H 0 src 000 dest OP-FP` | 将整数寄存器低 16 位位模式移到浮点寄存器，并进行 NaN-boxing |

## 14.4 Half-Precision Floating-Point Compare Instructions

半精度浮点比较指令与对应的单精度指令按类似方式定义，但它们作用于半精度操作数。

| 指令族 | 编码概要 | 语义 |
|---|---|---|
| `FEQ.H`/`FLT.H`/`FLE.H` | `FCMP H src2 src1 EQ/LT/LE dest OP-FP` | 比较两个半精度操作数，并将布尔结果写入整数目的寄存器 |

比较语义沿用单精度比较：`FEQ.H` 测试相等，`FLT.H` 测试小于，`FLE.H` 测试小于或等于。若比较结果为真，整数目的寄存器写入 1；否则写入 0。NaN 与 signaling NaN 的异常标志行为与单精度对应指令相同。

## 14.5 Half-Precision Floating-Point Classify Instruction

半精度浮点分类指令 `FCLASS.H` 与对应的单精度指令按类似方式定义，但它作用于半精度操作数。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FCLASS.H` | `FCLASS H 0 src 001 dest OP-FP` | 检查半精度源操作数的类别，并将分类掩码写入整数目的寄存器 |

`FCLASS.H` 的结果位含义与 `FCLASS.S` 相同，只是分类对象为半精度值：结果中恰好有一个位被置 1，用以表示负无穷、负正规数、负 subnormal、`-0`、`+0`、正 subnormal、正正规数、正无穷、signaling NaN 或 quiet NaN。

## 14.6 `Zfhmin` Standard Extension for Minimal Half-Precision Floating-Point

本节描述 `Zfhmin` 标准扩展。`Zfhmin` 为 16 位半精度二进制浮点指令提供最小支持。`Zfhmin` 扩展是 `Zfh` 扩展的子集，只包含数据传送和转换指令。与 `Zfh` 一样，`Zfhmin` 扩展依赖单精度浮点扩展 `F`。预期 `Zfhmin` 软件主要把半精度格式用于存储，而大多数计算在更高精度中执行。

`Zfhmin` 扩展包含 `Zfh` 扩展中的以下指令：`FLH`、`FSH`、`FMV.X.H`、`FMV.H.X`、`FCVT.S.H` 和 `FCVT.H.S`。如果存在 `D` 扩展，也包含 `FCVT.D.H` 和 `FCVT.H.D` 指令。如果存在 `Q` 扩展，还额外包含 `FCVT.Q.H` 和 `FCVT.H.Q` 指令。

`Zfhmin` 不包含 `FSGNJ.H` 指令，因为可以改用 `FSGNJ.S` 在浮点寄存器之间移动半精度值。

半精度加法、减法、乘法、除法和平方根操作可以通过以下方式精确仿真：先把半精度操作数转换为单精度，使用单精度算术执行操作，然后再转换回半精度。使用这种方法执行半精度 fused multiply-addition 时，在 `RNE` 和 `RMM` 舍入模式下，某些输入会产生 1-ulp 误差。

从 8 位或 16 位整数到半精度的转换可以通过先转换为单精度、再转换为半精度来仿真。从 32 位整数开始的转换可以通过先转换为双精度来仿真。如果不存在 `D` 扩展，并且在 `RNE` 或 `RMM` 下可以容忍 1-ulp 误差，则 32 位整数也可以先转换为单精度。没有 `Q` 扩展时，从 64 位整数开始的转换也适用同样说明。
