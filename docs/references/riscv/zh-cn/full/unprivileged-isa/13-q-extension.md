# Chapter 13 `Q` Standard Extension for Quad-Precision Floating-Point, Version 2.2

本章描述 `Q` 标准扩展。`Q` 扩展提供 128 位四精度二进制浮点指令，符合 IEEE 754-2008 算术标准。四精度二进制浮点指令集扩展命名为 `Q`；它依赖双精度浮点扩展 `D`。

支持 `Q` 后，浮点寄存器被扩展为能够保存单精度、双精度或四精度浮点值，此时 `FLEN=128`。12.2 节描述的 NaN-boxing 方案现在递归扩展：一个单精度值可以先 NaN-boxed 到双精度值中，而这个双精度值本身又可以 NaN-boxed 到四精度值中。

## 13.1 Quad-Precision Load and Store Instructions

ISA 增加新的 128 位 `LOAD-FP` 和 `STORE-FP` 指令变体，并通过 `funct3` 的 `width` 字段使用新的编码值来表示四精度宽度。

`FLQ` 从内存加载一个四精度浮点值到浮点寄存器 `rd`。有效地址由整数寄存器 `rs1` 和符号扩展的 12 位字节偏移相加得到，`width` 字段为 `Q`。

| 指令类别 | 编码字段 | 含义 |
|---|---|---|
| `LOAD-FP` | `imm[11:0] rs1 width rd opcode` | 使用 `rs1` 加 12 位偏移形成地址，将宽度为 `Q` 的四精度值加载到目的浮点寄存器 |
| 字段说明 | `offset[11:0] base Q dest LOAD-FP` | `offset` 是字节偏移，`base` 是基址整数寄存器，`dest` 是目的浮点寄存器 |

`FSQ` 将浮点寄存器中的四精度值存入内存。有效地址同样由整数寄存器 `rs1` 和符号扩展的 12 位字节偏移相加得到，`width` 字段为 `Q`。

| 指令类别 | 编码字段 | 含义 |
|---|---|---|
| `STORE-FP` | `imm[11:5] rs2 rs1 width imm[4:0] opcode` | 使用 `rs1` 加 12 位偏移形成地址，将源浮点寄存器中的四精度值存储到内存 |
| 字段说明 | `offset[11:5] src base Q offset[4:0] STORE-FP` | `src` 是源浮点寄存器，`base` 是基址整数寄存器，`offset` 是字节偏移 |

`FLQ` 和 `FSQ` 只有在有效地址自然对齐且 `XLEN=128` 时才保证原子执行。四精度自然对齐要求地址按 16 字节对齐。

`FLQ` 和 `FSQ` 不会修改被传送的位；特别是，非规范 NaN 的 payload 会被保留。

## 13.2 Quad-Precision Computational Instructions

大多数浮点指令的 `fmt` 字段增加一个新的受支持格式，如表 13.1 所示。

表 13.1：`fmt` 字段编码。

| `fmt` 字段 | 助记名 | 含义 |
|---|---|---|
| `00` | `S` | 32 位单精度 |
| `01` | `D` | 64 位双精度 |
| `10` | `H` | 16 位半精度 |
| `11` | `Q` | 128 位四精度 |

四精度浮点计算指令与对应的双精度指令按类似方式定义，但它们作用于四精度操作数，并产生四精度结果。

这些指令使用 `OP-FP` 主操作码空间，`fmt` 字段为 `Q`。`rm` 字段指定舍入模式，含义与 `F` 和 `D` 扩展中的舍入模式相同。

| 指令族 | 编码概要 | 语义 |
|---|---|---|
| `FADD.Q`/`FSUB.Q` | `FADD/FSUB Q src2 src1 RM dest OP-FP` | 对四精度操作数执行加法或减法，并按 `RM` 舍入 |
| `FMUL.Q`/`FDIV.Q` | `FMUL/FDIV Q src2 src1 RM dest OP-FP` | 对四精度操作数执行乘法或除法，并按 `RM` 舍入 |
| `FMIN.Q`/`FMAX.Q` | `FMIN-MAX Q src2 src1 MIN/MAX dest OP-FP` | 选择两个四精度操作数中的最小值或最大值 |
| `FSQRT.Q` | `FSQRT Q 0 src RM dest OP-FP` | 对四精度操作数求平方根，并按 `RM` 舍入 |

四精度融合乘加指令与双精度对应指令按类似方式定义，但 `fmt` 字段为 `Q`，源和目的均为四精度浮点值。

| 指令族 | 编码概要 | 语义 |
|---|---|---|
| `FMADD.Q`/`FMSUB.Q`/`FNMADD.Q`/`FNMSUB.Q` | `src3 Q src2 src1 RM dest F[N]MADD/F[N]MSUB` | 对四精度操作数执行融合乘加或融合乘减，只进行一次最终舍入 |

## 13.3 Quad-Precision Convert and Move Instructions

ISA 增加新的浮点到整数转换指令和整数到浮点转换指令。这些指令与双精度到整数、整数到双精度转换指令按类似方式定义。

`FCVT.W.Q` 或 `FCVT.L.Q` 分别把四精度浮点数转换为有符号 32 位或 64 位整数。`FCVT.Q.W` 或 `FCVT.Q.L` 分别把 32 位或 64 位有符号整数转换为四精度浮点数。`FCVT.WU.Q`、`FCVT.LU.Q`、`FCVT.Q.WU` 和 `FCVT.Q.LU` 变体在无符号整数值和四精度浮点值之间转换。`FCVT.L[U].Q` 和 `FCVT.Q.L[U]` 是仅 RV64 定义的指令。

| 指令类别 | 编码概要 | 语义 |
|---|---|---|
| `FCVT.int.Q` | `FCVT.int.Q Q W[U]/L[U] src RM dest OP-FP` | 将四精度浮点源转换为整数目的寄存器 |
| `FCVT.Q.int` | `FCVT.Q.int Q W[U]/L[U] src RM dest OP-FP` | 将整数源寄存器转换为四精度浮点目的寄存器 |

ISA 还增加新的浮点到浮点转换指令。这些指令与双精度浮点到浮点转换指令按类似方式定义。

`FCVT.S.Q` 或 `FCVT.Q.S` 分别把四精度浮点数转换为单精度浮点数，或把单精度浮点数转换为四精度浮点数。`FCVT.D.Q` 或 `FCVT.Q.D` 分别把四精度浮点数转换为双精度浮点数，或把双精度浮点数转换为四精度浮点数。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FCVT.S.Q` | `FCVT.S.Q S Q src RM dest OP-FP` | 将四精度源转换为单精度目的，并按 `RM` 舍入 |
| `FCVT.Q.S` | `FCVT.Q.S Q S src RM dest OP-FP` | 将单精度源转换为四精度目的 |
| `FCVT.D.Q` | `FCVT.D.Q D Q src RM dest OP-FP` | 将四精度源转换为双精度目的，并按 `RM` 舍入 |
| `FCVT.Q.D` | `FCVT.Q.D Q D src RM dest OP-FP` | 将双精度源转换为四精度目的 |

浮点到浮点符号注入指令 `FSGNJ.Q`、`FSGNJN.Q` 和 `FSGNJX.Q` 与双精度符号注入指令按类似方式定义。

| 指令族 | 编码概要 | 语义 |
|---|---|---|
| `FSGNJ.Q`/`FSGNJN.Q`/`FSGNJX.Q` | `FSGNJ Q src2 src1 J[N]/JX dest OP-FP` | 复制四精度源的数值位，并按 `J`、`JN` 或 `JX` 规则生成符号位 |

RV32 或 RV64 中不提供 `FMV.X.Q` 和 `FMV.Q.X` 指令，因此四精度位模式必须通过内存在浮点寄存器和整数寄存器之间移动。

RV128 会在 `Q` 扩展中支持 `FMV.X.Q` 和 `FMV.Q.X`。

## 13.4 Quad-Precision Floating-Point Compare Instructions

四精度浮点比较指令与对应的双精度指令按类似方式定义，但它们作用于四精度操作数。

| 指令族 | 编码概要 | 语义 |
|---|---|---|
| `FEQ.Q`/`FLT.Q`/`FLE.Q` | `FCMP Q src2 src1 EQ/LT/LE dest OP-FP` | 比较两个四精度操作数，并将布尔结果写入整数目的寄存器 |

比较语义沿用双精度和单精度比较：`FEQ.Q` 测试相等，`FLT.Q` 测试小于，`FLE.Q` 测试小于或等于。若比较结果为真，整数目的寄存器写入 1；否则写入 0。NaN 与 signaling NaN 的异常标志行为与相应较低精度指令相同。

## 13.5 Quad-Precision Floating-Point Classify Instruction

四精度浮点分类指令 `FCLASS.Q` 与对应的双精度指令按类似方式定义，但它作用于四精度操作数。

| 指令 | 编码概要 | 语义 |
|---|---|---|
| `FCLASS.Q` | `FCLASS Q 0 src 001 dest OP-FP` | 检查四精度源操作数的类别，并将分类掩码写入整数目的寄存器 |

`FCLASS.Q` 的结果位含义与 `FCLASS.D` 和 `FCLASS.S` 相同，只是分类对象为四精度值：结果中恰好有一个位被置 1，用以表示负无穷、负正规数、负 subnormal、`-0`、`+0`、正 subnormal、正正规数、正无穷、signaling NaN 或 quiet NaN。
