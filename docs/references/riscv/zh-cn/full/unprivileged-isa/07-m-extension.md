# 第 7 章 `M` 整数乘法和除法标准扩展，版本 2.0

本章描述标准 integer multiplication and division instruction extension。该扩展命名为 `M`，包含对两个 integer register 中保存的值执行乘法或除法的指令。

> 我们把 integer multiply 和 divide 从 base 中分离出来，是为了简化 low-end implementation；或者用于 integer multiply 和 divide operation 不常见，或更适合由 attached accelerator 处理的应用。

## 7.1 乘法操作

```text
31      25 24 20 19 15 14 12 11 7 6 0
funct7     rs2   rs1   funct3 rd   opcode
7          5     5     3      5    7

MULDIV multiplier multiplicand MUL/MULH[[S]U] dest OP
MULDIV multiplier multiplicand MULW            dest OP-32
```

`MUL` 对 `rs1` 和 `rs2` 执行 `XLEN-bit × XLEN-bit` 乘法，并把低 XLEN bit 放入 destination register。

`MULH`、`MULHU` 和 `MULHSU` 执行同样的乘法，但返回完整 `2×XLEN-bit` 乘积的高 XLEN bit；它们分别对应 signed×signed、unsigned×unsigned，以及 signed `rs1` × unsigned `rs2` 乘法。

如果需要同一乘积的高位和低位，则推荐的代码序列是：

```asm
MULH[[S]U] rdh, rs1, rs2
MUL        rdl, rs1, rs2
```

其中 source register specifier 必须采用相同顺序，并且 `rdh` 不能与 `rs1` 或 `rs2` 相同。这样，microarchitecture 可以把这两条指令 fuse 成单个 multiply operation，而不是执行两次独立乘法。

`MULHSU` 用于 multi-word signed multiplication：它把 multiplicand 的 most-significant word（包含 sign bit）与 multiplier 的 less-significant word（无符号）相乘。

`MULW` 是 RV64 指令。它把 source register 的低 32 bit 相乘，并把结果低 32 bit 的 sign-extension 放入 destination register。

在 RV64 中，`MUL` 可用于取得 64-bit 乘积的高 32 bit，但 signed argument 必须是正确的 32-bit signed value，而 unsigned argument 必须清除其高 32 bit。如果不确定 argument 是否已经 sign-extended 或 zero-extended，另一种做法是把两个 argument 都左移 32 bit，然后使用 `MULH[[S]U]`。

## 7.2 除法操作

```text
31      25 24 20 19 15 14 12 11 7 6 0
funct7     rs2   rs1   funct3 rd   opcode
7          5     5     3      5    7

MULDIV divisor dividend DIV[U]/REM[U]        dest OP
MULDIV divisor dividend DIV[U]W/REM[U]W      dest OP-32
```

`DIV` 和 `DIVU` 对 `rs1` 除以 `rs2` 执行 XLEN bit by XLEN bit 的 signed 和 unsigned integer division，并向零舍入。`REM` 和 `REMU` 提供对应 division operation 的 remainder。对于 `REM`，结果的符号等于 dividend 的符号。

对于 signed 和 unsigned division，都满足：

```text
dividend = divisor × quotient + remainder
```

如果需要同一次除法的 quotient 和 remainder，则推荐的代码序列是：

```asm
DIV[U]  rdq, rs1, rs2
REM[U]  rdr, rs1, rs2
```

其中 `rdq` 不能与 `rs1` 或 `rs2` 相同。这样，microarchitecture 可以把这两条指令 fuse 成单个 divide operation，而不是执行两次独立除法。

`DIVW` 和 `DIVUW` 是 RV64 指令。它们分别把 `rs1` 的低 32 bit 除以 `rs2` 的低 32 bit，并分别把这些值视为 signed integer 和 unsigned integer；得到的 32-bit quotient 放入 `rd`，并 sign-extended 到 64 bit。

`REMW` 和 `REMUW` 是 RV64 指令，分别提供对应的 signed 和 unsigned remainder operation。`REMW` 和 `REMUW` 始终把 32-bit 结果 sign-extend 到 64 bit，包括 divide by zero 的情况。

division by zero 和 division overflow 的语义汇总在表 7.1 中。division by zero 的 quotient 为所有 bit 置位，division by zero 的 remainder 等于 dividend。Signed division overflow 只在 most-negative integer 除以 `-1` 时发生。发生 overflow 的 signed division，其 quotient 等于 dividend，remainder 为 0。Unsigned division overflow 不会发生。

| Condition | Dividend | Divisor | `DIVU[W]` | `REMU[W]` | `DIV[W]` | `REM[W]` |
|---|---:|---:|---:|---:|---:|---:|
| Division by zero | `x` | 0 | `2^L - 1` | `x` | `-1` | `x` |
| Overflow（仅 signed） | `-2^(L-1)` | `-1` | - | - | `-2^(L-1)` | 0 |

表 7.1：division by zero 和 division overflow 的语义。`L` 是 operation 的 bit 宽度：对 `DIV[U]` 和 `REM[U]` 为 XLEN，对 `DIV[U]W` 和 `REM[U]W` 为 32。

> 我们考虑过在 integer divide by zero 时引发 exception，并使这些 exception 在大多数 execution environment 中导致 trap。然而，这将成为 standard ISA 中唯一的 arithmetic trap（floating-point exception 会设置 flag 并写入 default value，但不会导致 trap），而且会要求 language implementor 在这种情况下与 execution environment 的 trap handler 交互。此外，如果 language standard 强制要求 divide-by-zero exception 必须导致立即 control flow change，那么只需要为每个 divide operation 增加一条 branch 指令即可；该 branch 指令可以插入在 divide 之后，并且通常会非常可预测地 not taken，因此只增加很少 runtime overhead。

> unsigned 和 signed divide by zero 都返回所有 bit 置位的值，以简化 divider circuitry。全 1 值既是 unsigned divide 的自然返回值，表示最大的 unsigned number，也是简单 unsigned divider 实现的自然结果。Signed division 通常使用 unsigned division circuit 实现，规定相同的 overflow result 可以简化硬件。
