# Chapter 2. Instructions (in alphabetical order)

## 2.1. add.uw

Synopsis：Add unsigned word

Mnemonic：`add.uw rd, rs1, rs2`

Pseudoinstructions：`zext.w rd, rs1 -> add.uw rd, rs1, zero`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 1 1 1 0 rd 0 0 0 rs1 rs2 0 0 1 0 0 0 0
OP-32 ADD.UW ADD.UW
```

Description：本指令在 `rs2` 与 `rs1` 的零扩展最低有效字之间执行一次 `XLEN` 宽加法。

Operation：

```text
let base = X(rs2);
let index = EXTZ(X(rs1)[31..0]);
X(rd) = base + index;
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zba (Address generation instructions) | 0.93 | Frozen |

## 2.2. andn

Synopsis：AND with inverted operand

Mnemonic：`andn rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 1 1 1 rs1 rs2 0 0 0 0 0 1 0
OP ANDN ANDN
```

Description：本指令在 `rs1` 与 `rs2` 的按位取反之间执行按位逻辑 AND 操作。

Operation：

```text
X(rd) = X(rs1) & ~X(rs2);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.3. bclr

Synopsis：Single-Bit Clear (Register)

Mnemonic：`bclr rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 1 0 0 rs1 rs2 0 0 1 0 0 1 0
OP BCLR BCLR/BEXT
```

Description：本指令返回 `rs1`，但清除由 `rs2` 指定索引处的单个比特。索引从 `rs2` 的低 `log2(XLEN)` 位读取。

Operation：

```text
let index = X(rs2) & (XLEN - 1);
X(rd) = X(rs1) & ~(1 << index)
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbs (Single-bit instructions) | 0.93 | Frozen |

## 2.4. bclri

Synopsis：Single-Bit Clear (Immediate)

Mnemonic：`bclri rd, rs1, shamt`

Encoding (RV32)：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 0 0 rd 1 0 0 rs1 shamt 0 0 1 0 0 1 0
OP-IMM BCLRI BCLRI
```

Encoding (RV64)：

```text
0 6 7 11 12 14 15 19 20 25 26 31
1 1 0 0 1 0 0 rd 1 0 0 rs1 shamt 0 1 0 0 1 0
OP-IMM BCLRI BCLRI
```

Description：本指令返回 `rs1`，但清除由 `shamt` 指定索引处的单个比特。索引从 `shamt` 的低 `log2(XLEN)` 位读取。对于 RV32，对应 `shamt[5]=1` 的编码保留。

Operation：

```text
let index = shamt & (XLEN - 1);
X(rd) = X(rs1) & ~(1 << index)
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbs (Single-bit instructions) | 0.93 | Frozen |

## 2.5. bext

Synopsis：Single-Bit Extract (Register)

Mnemonic：`bext rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 1 0 1 rs1 rs2 0 0 1 0 0 1 0
OP BEXT BCLR/BEXT
```

Description：本指令返回从 `rs1` 中提取的单个比特，该比特位于 `rs2` 指定的索引处。索引从 `rs2` 的低 `log2(XLEN)` 位读取。

Operation：

```text
let index = X(rs2) & (XLEN - 1);
X(rd) = (X(rs1) >> index) & 1;
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbs (Single-bit instructions) | 0.93 | Frozen |

## 2.6. bexti

Synopsis：Single-Bit Extract (Immediate)

Mnemonic：`bexti rd, rs1, shamt`

Encoding (RV32)：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 0 0 rd 1 0 1 rs1 shamt 0 0 1 0 0 1 0
OP-IMM BEXTI BEXTI/BCLRI
```

Encoding (RV64)：

```text
0 6 7 11 12 14 15 19 20 25 26 31
1 1 0 0 1 0 0 rd 1 0 1 rs1 shamt 0 1 0 0 1 0
OP-IMM BEXTI BEXTI/BCLRI
```

Description：本指令返回从 `rs1` 中提取的单个比特，该比特位于 `shamt` 指定的索引处。索引从 `shamt` 的低 `log2(XLEN)` 位读取。对于 RV32，对应 `shamt[5]=1` 的编码保留。

Operation：

```text
let index = shamt & (XLEN - 1);
X(rd) = (X(rs1) >> index) & 1;
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbs (Single-bit instructions) | 0.93 | Frozen |

## 2.7. binv

Synopsis：Single-Bit Invert (Register)

Mnemonic：`binv rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 1 0 0 rs1 rs2 0 0 1 0 1 1 0
OP BINV BINV
```

Description：本指令返回 `rs1`，但反转由 `rs2` 指定索引处的单个比特。索引从 `rs2` 的低 `log2(XLEN)` 位读取。

Operation：

```text
let index = X(rs2) & (XLEN - 1);
X(rd) = X(rs1) ^ (1 << index)
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbs (Single-bit instructions) | 0.93 | Frozen |

## 2.8. binvi

Synopsis：Single-Bit Invert (Immediate)

Mnemonic：`binvi rd, rs1, shamt`

Encoding (RV32)：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 0 0 rd 1 0 0 rs1 shamt 0 0 1 0 1 1 0
OP-IMM BINV BINVI
```

Encoding (RV64)：

```text
0 6 7 11 12 14 15 19 20 25 26 31
1 1 0 0 1 0 0 rd 1 0 0 rs1 shamt 0 1 0 1 1 0
OP-IMM BINV BINVI
```

Description：本指令返回 `rs1`，但反转由 `shamt` 指定索引处的单个比特。索引从 `shamt` 的低 `log2(XLEN)` 位读取。对于 RV32，对应 `shamt[5]=1` 的编码保留。

Operation：

```text
let index = shamt & (XLEN - 1);
X(rd) = X(rs1) ^ (1 << index)
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbs (Single-bit instructions) | 0.93 | Frozen |

## 2.9. bset

Synopsis：Single-Bit Set (Register)

Mnemonic：`bset rd, rs1,rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 1 0 0 rs1 rs2 0 0 1 0 1 0 0
OP BSET BSET
```

Description：本指令返回 `rs1`，但设置由 `rs2` 指定索引处的单个比特。索引从 `rs2` 的低 `log2(XLEN)` 位读取。

Operation：

```text
let index = X(rs2) & (XLEN - 1);
X(rd) = X(rs1) | (1 << index)
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbs (Single-bit instructions) | 0.93 | Frozen |

## 2.10. bseti

Synopsis：Single-Bit Set (Immediate)

Mnemonic：`bseti rd, rs1,shamt`

Encoding (RV32)：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 0 0 rd 1 0 0 rs1 shamt 0 0 1 0 1 0 0
OP-IMM BSETI BSETI
```

Encoding (RV64)：

```text
0 6 7 11 12 14 15 19 20 25 26 31
1 1 0 0 1 0 0 rd 1 0 0 rs1 shamt 0 1 0 1 0 0
OP-IMM BSETI BSETI
```

Description：本指令返回 `rs1`，但设置由 `shamt` 指定索引处的单个比特。索引从 `shamt` 的低 `log2(XLEN)` 位读取。对于 RV32，对应 `shamt[5]=1` 的编码保留。

Operation：

```text
let index = shamt & (XLEN - 1);
X(rd) = X(rs1) | (1 << index)
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbs (Single-bit instructions) | 0.93 | Frozen |

## 2.11. clmul

Synopsis：Carry-less multiply (low-part)

Mnemonic：`clmul rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 1 0 0 rs1 rs2 1 0 1 0 0 0 0
OP CLMUL MINMAX/CLMUL
```

Description：`clmul` 产生 `2*XLEN` 无进位乘积的低半部分。

Operation：

```text
let rs1_val = X(rs1);
let rs2_val = X(rs2);
let output : xlenbits = 0;
foreach (i from 0 to xlen by 1) {
  output = if   ((rs2_val >> i) & 1)
           then output ^ (rs1_val << i);
       else output;
}
X[rd] = output
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbc (Carry-less multiplication) | 0.93 | Frozen |

## 2.12. clmulh

Synopsis：Carry-less multiply (high-part)

Mnemonic：`clmulh rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 1 1 0 rs1 rs2 1 0 1 0 0 0 0
OP CLMULH MINMAX/CLMUL
```

Description：`clmulh` 产生 `2*XLEN` 无进位乘积的高半部分。

Operation：

```text
let rs1_val = X(rs1);
let rs2_val = X(rs2);
let output : xlenbits = 0;
foreach (i from 1 to xlen by 1) {
  output = if   ((rs2_val >> i) & 1)
           then output ^ (rs1_val >> (xlen - i));
       else output;
}
X[rd] = output
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbc (Carry-less multiplication) | 0.93 | Frozen |

## 2.13. clmulr

Synopsis：Carry-less multiply (reversed)

Mnemonic：`clmulr rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 0 1 0 rs1 rs2 1 0 1 0 0 0 0
OP CLMULR MINMAX/CLMUL
```

Description：`clmulr` 产生 `2*XLEN` 无进位乘积的 `2*XLEN-2:XLEN-1` 位。

Operation：

```text
let rs1_val = X(rs1);
let rs2_val = X(rs2);
let output : xlenbits = 0;
foreach (i from 0 to (xlen - 1) by 1) {
  output = if   ((rs2_val >> i) & 1)
           then output ^ (rs1_val >> (xlen - i - 1));
       else output;
}
X[rd] = output
```

Note：`clmulr` 指令用于加速 CRC 计算。指令助记符中的 `r` 表示 reversed，因为该指令等价于对输入进行比特反转、执行 `clmul`、然后对输出进行比特反转。

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbc (Carry-less multiplication) | 0.93 | Frozen |

## 2.14. clz

Synopsis：Count leading zero bits

Mnemonic：`clz rd, rs`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 0 0 rd 1 0 0 rs1 0 0 0 0 0 0 0 0 0 1 1 0
OP-IMM CLZ CLZ CLZ
```

Description：本指令从最高有效位（即 `XLEN-1`）开始并向 bit 0 前进，计算第一个 1 之前的 0 的数量。因此，如果输入为 0，输出为 `XLEN`；如果输入的最高有效位为 1，输出为 0。

Operation：

```text
val HighestSetBit : forall ('N : Int), 'N >= 0. bits('N) -> int
function HighestSetBit x = {
  foreach (i from (xlen - 1) to 0 by 1 in dec)
    if [x[i]] == 0b1 then return(i) else ();
  return -1;
}
let rs = X(rs);
X[rd] = (xlen - 1) - HighestSetBit(rs);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.15. clzw

Synopsis：Count leading zero bits in word

Mnemonic：`clzw rd, rs`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 1 1 0 0 rd 1 0 0 rs1 0 0 0 0 0 0 0 0 0 1 1 0
OP-IMM-32 CLZW CLZW CLZW
```

Description：本指令从 bit 31 开始并向 bit 0 前进，计算第一个 1 之前的 0 的数量。因此，如果最低有效字为 0，输出为 32；如果该字的最高有效位（即 bit 31）为 1，输出为 0。

Operation：

```text
val HighestSetBit32 : forall ('N : Int), 'N >= 0. bits('N) -> int
function HighestSetBit32 x = {
  foreach (i from 31 to 0 by 1 in dec)
    if [x[i]] == 0b1 then return(i) else ();
  return -1;
}
let rs = X(rs);
X[rd] = 31 - HighestSetBit(rs);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.16. cpop

Synopsis：Count set bits

Mnemonic：`cpop rd, rs`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 0 0 rd 1 0 0 rs1 0 1 0 0 0 0 0 0 0 1 1 0
OP-IMM CPOP CPOP CPOP
```

Description：本指令计算源寄存器中 1（即置位比特）的数量。

Operation：

```text
let bitcount = 0;
let rs = X(rs);
foreach (i from 0 to (xlen - 1) in inc)
  if rs[i] == 0b1 then bitcount = bitcount + 1 else ();
X[rd] = bitcount
```

Software Hint：此操作称为 population count、popcount、sideways sum、bit summation 或 Hamming weight。

GCC 内建函数 `__builtin_popcount(unsigned int x)` 在 RV32 上由 `cpop` 实现，在 RV64 上由 `cpopw` 实现。面向 LP64 的 GCC 内建函数 `__builtin_popcountl(unsigned long x)` 在 RV64 上由 `cpop` 实现。

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.17. cpopw

Synopsis：Count set bits in word

Mnemonic：`cpopw rd, rs`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 1 1 0 0 rd 1 0 0 rs 0 1 0 0 0 0 0 0 0 1 1 0
OP-IMM-32 CPOPW CPOPW CPOPW
```

Description：本指令计算源寄存器最低有效字中 1（即置位比特）的数量。

Operation：

```text
let bitcount = 0;
let val = X(rs);
foreach (i from 0 to 31 in inc)
  if val[i] == 0b1 then bitcount = bitcount + 1 else ();
X[rd] = bitcount
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.18. ctz

Synopsis：Count trailing zeros

Mnemonic：`ctz rd, rs`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 0 0 rd 1 0 0 rs1 1 0 0 0 0 0 0 0 0 1 1 0
OP-IMM CTZ/CTZW CTZ/CTZW CTZ/CTZW
```

Description：本指令从最低有效位（即 0）开始并向最高有效位（即 `XLEN-1`）前进，计算第一个 1 之前的 0 的数量。因此，如果输入为 0，输出为 `XLEN`；如果输入的最低有效位为 1，输出为 0。

Operation：

```text
val LowestSetBit : forall ('N : Int), 'N >= 0. bits('N) -> int
function LowestSetBit x = {
  foreach (i from 0 to (xlen - 1) by 1 in dec)
    if [x[i]] == 0b1 then return(i) else ();
  return xlen;
}
let rs = X(rs);
X[rd] = LowestSetBit(rs);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.19. ctzw

Synopsis：Count trailing zero bits in word

Mnemonic：`ctzw rd, rs`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 1 1 0 0 rd 1 0 0 rs1 1 0 0 0 0 0 0 0 0 1 1 0
OP-IMM-32 CTZ/CTZW CTZ/CTZW CTZ/CTZW
```

Description：本指令从最低有效位（即 0）开始并向最低有效字的最高有效位（即 31）前进，计算第一个 1 之前的 0 的数量。因此，如果最低有效字为 0，输出为 32；如果输入的最低有效位为 1，输出为 0。

Operation：

```text
val LowestSetBit32 : forall ('N : Int), 'N >= 0. bits('N) -> int
function LowestSetBit32 x = {
  foreach (i from 0 to 31 by 1 in dec)
    if [x[i]] == 0b1 then return(i) else ();
  return 32;
}
let rs = X(rs);
X[rd] = LowestSetBit32(rs);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.20. max

Synopsis：Maximum

Mnemonic：`max rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 0 1 1 rs1 rs2 1 0 1 0 0 0 0
OP MAX MINMAX/CLMUL
```

Description：本指令返回两个有符号整数中较大的一个。

Operation：

```text
let rs1_val = X(rs1);
let rs2_val = X(rs2);
let result = if   rs1_val <_s rs2_val
             then rs2_val
         else rs1_val;
X(rd) = result;
```

Software Hint：计算有符号整数绝对值可使用如下序列执行：`neg rD,rS` 后接 `max rD,rS,rD`。在使用这一常见序列时，建议二者之间不要调度其他指令，使经过相应优化的实现能够将它们融合在一起。

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.21. maxu

Synopsis：Unsigned maximum

Mnemonic：`maxu rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 1 1 1 rs1 rs2 1 0 1 0 0 0 0
OP MAXU MINMAX/CLMUL
```

Description：本指令返回两个无符号整数中较大的一个。

Operation：

```text
let rs1_val = X(rs1);
let rs2_val = X(rs2);
let result = if   rs1_val <_u rs2_val
             then rs2_val
         else rs1_val;
X(rd) = result;
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.22. min

Synopsis：Minimum

Mnemonic：`min rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 0 0 1 rs1 rs2 1 0 1 0 0 0 0
OP MIN MINMAX/CLMUL
```

Description：本指令返回两个有符号整数中较小的一个。

Operation：

```text
let rs1_val = X(rs1);
let rs2_val = X(rs2);
let result = if   rs1_val <_s rs2_val
             then rs1_val
         else rs2_val;
X(rd) = result;
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.23. minu

Synopsis：Unsigned minimum

Mnemonic：`minu rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 1 0 1 rs1 rs2 1 0 1 0 0 0 0
OP MINU MINMAX/CLMUL
```

Description：本指令返回两个无符号整数中较小的一个。

Operation：

```text
let rs1_val = X(rs1);
let rs2_val = X(rs2);
let result = if   rs1_val <_u rs2_val
             then rs1_val
         else rs2_val;
X(rd) = result;
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.24. orc.b

Synopsis：Bitwise OR-Combine, byte granule

Mnemonic：`orc.b rd, rs`

Encoding：

```text
0 6 7 11 12 14 15 19 20 31
1 1 0 0 1 0 0 rd 1 0 1 rs 1 1 1 0 0 0 0 1 0 1 0 0
OP-IMM
```

Description：使用按位逻辑 OR 组合每个字节内的比特。如果 `rs` 对应字节中没有任何比特被置位，则将结果 `rd` 中该字节的比特设为全零；如果 `rs` 对应字节中任意比特被置位，则设为全一。

Operation：

```text
let input = X(rs);
let output : xlenbits = 0;
foreach (i from 0 to (xlen - 8) by 8) {
  output[(i + 7)..i] = if   input[(i + 7)..i] == 0
                       then 0b00000000
                       else 0b11111111;
}
X[rd] = output;
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.25. orn

Synopsis：OR with inverted operand

Mnemonic：`orn rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 0 1 1 rs1 rs2 0 0 0 0 0 1 0
OP ORN ORN
```

Description：本指令在 `rs1` 与 `rs2` 的按位取反之间执行按位逻辑 OR 操作。

Operation：

```text
X(rd) = X(rs1) | ~X(rs2);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.26. rev8

Synopsis：Byte-reverse register

Mnemonic：`rev8 rd, rs`

Encoding (RV32)：

```text
0 6 7 11 12 14 15 19 20 31
1 1 0 0 1 0 0 rd 1 0 1 rs 0 0 0 1 1 0 0 1 0 1 1 0
OP-IMM
```

Encoding (RV64)：

```text
0 6 7 11 12 14 15 19 20 31
1 1 0 0 1 0 0 rd 1 0 1 rs 0 0 0 1 1 1 0 1 0 1 1 0
OP-IMM
```

Description：本指令反转 `rs` 中字节的顺序。

Operation：

```text
let input = X(rs);
let output : xlenbits = 0;
let j = xlen - 1;
foreach (i from 0 to (xlen - 8) by 8) {
  output[i..(i + 7)] = input[(j - 7)..j];
  j = j - 8;
}
X[rd] = output
```

Note：`rev8` 助记符在 RV32 和 RV64 中对应不同的指令编码。

Software Hint：字节反转操作只可用于完整寄存器宽度。要仿真字大小和半字大小的字节反转，先执行 `rev8 rd,rs`，再执行 `srai rd,rd`。

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.27. rol

Synopsis：Rotate Left (Register)

Mnemonic：`rol rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 1 0 0 rs1 rs2 0 0 0 0 1 1 0
OP ROL ROL
```

Description：本指令将 `rs1` 左循环移位，移位量来自 `rs2` 的最低有效 `log2(XLEN)` 位。

Operation：

```text
let shamt = if   xlen == 32
            then X(rs2)[4..0]
        else X(rs2)[5..0];
let result = (X(rs1) << shamt) | (X(rs1) >> (xlen - shamt));
X(rd) = result;
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.28. rolw

Synopsis：Rotate Left Word (Register)

Mnemonic：`rolw rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 1 1 1 0 rd 1 0 0 rs1 rs2 0 0 0 0 1 1 0
OP-32 ROLW ROLW
```

Description：本指令将 `rs1` 的最低有效字左循环移位，移位量来自 `rs2` 的最低有效 5 位。所得字值通过将 bit 31 复制到所有更高有效位来符号扩展。

Operation：

```text
let rs1 = EXTZ(X(rs1)[31..0])
let shamt = X(rs2)[4..0];
let result = (rs1 << shamt) | (rs1 >> (32 - shamt));
X(rd) = EXTS(result);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.29. ror

Synopsis：Rotate Right

Mnemonic：`ror rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 1 0 1 rs1 rs2 0 0 0 0 1 1 0
OP ROR ROR
```

Description：本指令将 `rs1` 右循环移位，移位量来自 `rs2` 的最低有效 `log2(XLEN)` 位。

Operation：

```text
let shamt = if   xlen == 32
            then X(rs2)[4..0]
        else X(rs2)[5..0];
let result = (X(rs1) >> shamt) | (X(rs1) << (xlen - shamt));
X(rd) = result;
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.30. rori

Synopsis：Rotate Right (Immediate)

Mnemonic：`rori rd, rs1, shamt`

Encoding (RV32)：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 0 0 rd 1 0 1 rs1 shamt 0 0 0 0 1 1 0
OP-IMM RORI RORI
```

Encoding (RV64)：

```text
0 6 7 11 12 14 15 19 20 25 26 31
1 1 0 0 1 0 0 rd 1 0 1 rs1 shamt 0 0 0 1 1 0
OP-IMM RORI RORI
```

Description：本指令将 `rs1` 右循环移位，移位量来自 `shamt` 的最低有效 `log2(XLEN)` 位。对于 RV32，对应 `shamt[5]=1` 的编码保留。

Operation：

```text
let shamt = if   xlen == 32
            then shamt[4..0]
        else shamt[5..0];
let result = (X(rs1) >> shamt) | (X(rs1) << (xlen - shamt));
X(rd) = result;
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.31. roriw

Synopsis：Rotate Right Word by Immediate

Mnemonic：`roriw rd, rs1, shamt`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 1 1 0 0 rd 1 0 1 rs1 shamt 0 0 0 0 1 1 0
OP-IMM-32 RORIW RORIW
```

Description：本指令将 `rs1` 的最低有效字右循环移位，移位量来自 `shamt` 的最低有效 `log2(XLEN)` 位。所得字值通过将 bit 31 复制到所有更高有效位来符号扩展。

Operation：

```text
let rs1_data = EXTZ(X(rs1)[31..0];
let result = (rs1_data >> shamt[4..0]) | (rs1_data << (32 - shamt[4..0]));
X(rd) = EXTS(result[31..0]);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.32. rorw

Synopsis：Rotate Right Word (Register)

Mnemonic：`rorw rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 1 1 1 0 rd 1 0 1 rs1 rs2 0 0 0 0 1 1 0
OP-32 RORW RORW
```

Description：本指令将 `rs1` 的最低有效字右循环移位，移位量来自 `rs2` 的最低有效 5 位。所得字通过将 bit 31 复制到所有更高有效位来符号扩展。

Operation：

```text
let rs1 = EXTZ(X(rs1)[31..0])
let shamt = X(rs2)[4..0];
let result = (rs1 >> shamt) | (rs1 << (32 - shamt));
X(rd) = EXTS(result);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.33. sext.b

Synopsis：Sign-extend byte

Mnemonic：`sext.b rd, rs`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 0 0 rd 1 0 0 rs1 0 0 1 0 0 0 0 0 0 1 1 0
OP-IMM SEXT .B/SEXT .H SEXT .B
```

Description：本指令将源中的最低有效字节符号扩展到 `XLEN`，方法是把该字节的最高有效位（即 bit 7）复制到所有更高有效位。

Operation：

```text
X(rd) = EXTS(X(rs)[7..0]);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.34. sext.h

Synopsis：Sign-extend halfword

Mnemonic：`sext.h rd, rs`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 0 0 rd 1 0 0 rs1 1 0 1 0 0 0 0 0 0 1 1 0
OP-IMM SEXT .B/SEXT .H SEXT .H
```

Description：本指令将 `rs` 中的最低有效半字符号扩展到 `XLEN`，方法是把该半字的最高有效位（即 bit 15）复制到所有更高有效位。

Operation：

```text
X(rd) = EXTS(X(rs)[15..0]);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.35. sh1add

Synopsis：Shift left by 1 and add

Mnemonic：`sh1add rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 0 1 0 rs1 rs2 0 0 0 0 1 0 0
OP SH1ADD SH1ADD
```

Description：本指令将 `rs1` 左移 1 位并加到 `rs2`。

Operation：

```text
X(rd) = X(rs2) + (X(rs1) << 1);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zba (Address generation instructions) | 0.93 | Frozen |

## 2.36. sh1add.uw

Synopsis：Shift unsigned word left by 1 and add

Mnemonic：`sh1add.uw rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 1 1 1 0 rd 0 1 0 rs1 rs2 0 0 0 0 1 0 0
OP-32 SH1ADD.UW SH1ADD.UW
```

Description：本指令执行两个加数的 `XLEN` 宽加法。第一个加数是 `rs2`。第二个加数是从 `rs1` 中提取最低有效字并将其左移 1 位而形成的无符号值。

Operation：

```text
let base = X(rs2);
let index = EXTZ(X(rs1)[31..0]);
X(rd) = base + (index << 1);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zba (Address generation instructions) | 0.93 | Frozen |

## 2.37. sh2add

Synopsis：Shift left by 2 and add

Mnemonic：`sh2add rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 0 0 1 rs1 rs2 0 0 0 0 1 0 0
OP SH2ADD SH2ADD
```

Description：本指令将 `rs1` 左移 2 位并加到 `rs2`。

Operation：

```text
X(rd) = X(rs2) + (X(rs1) << 2);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zba (Address generation instructions) | 0.93 | Frozen |

## 2.38. sh2add.uw

Synopsis：Shift unsigned word left by 2 and add

Mnemonic：`sh2add.uw rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 1 1 1 0 rd 0 0 1 rs1 rs2 0 0 0 0 1 0 0
OP-32 SH2ADD.UW SH2ADD.UW
```

Description：本指令执行两个加数的 `XLEN` 宽加法。第一个加数是 `rs2`。第二个加数是从 `rs1` 中提取最低有效字并将其左移 2 位而形成的无符号值。

Operation：

```text
let base = X(rs2);
let index = EXTZ(X(rs1)[31..0]);
X(rd) = base + (index << 2);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zba (Address generation instructions) | 0.93 | Frozen |

## 2.39. sh3add

Synopsis：Shift left by 3 and add

Mnemonic：`sh3add rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 0 1 1 rs1 rs2 0 0 0 0 1 0 0
OP SH3ADD SH3ADD
```

Description：本指令将 `rs1` 左移 3 位并加到 `rs2`。

Operation：

```text
X(rd) = X(rs2) + (X(rs1) << 3);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zba (Address generation instructions) | 0.93 | Frozen |

## 2.40. sh3add.uw

Synopsis：Shift unsigned word left by 3 and add

Mnemonic：`sh3add.uw rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 1 1 1 0 rd 0 1 1 rs1 rs2 0 0 0 0 1 0 0
OP-32 SH3ADD.UW SH3ADD.UW
```

Description：本指令执行两个加数的 `XLEN` 宽加法。第一个加数是 `rs2`。第二个加数是从 `rs1` 中提取最低有效字并将其左移 3 位而形成的无符号值。

Operation：

```text
let base = X(rs2);
let index = EXTZ(X(rs1)[31..0]);
X(rd) = base + (index << 3);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zba (Address generation instructions) | 0.93 | Frozen |

## 2.41. slli.uw

Synopsis：Shift-left unsigned word (Immediate)

Mnemonic：`slli.uw rd, rs1, shamt`

Encoding：

```text
0 6 7 11 12 14 15 19 20 25 26 31
1 1 0 1 1 0 0 rd 1 0 0 rs1 shamt 0 1 0 0 0 0
OP-IMM-32 SLLI.UW SLLI.UW
```

Description：本指令取得 `rs1` 的最低有效字，将其零扩展，然后按立即数左移。

Operation：

```text
X(rd) = (EXTZ(X(rs)[31..0]) << shamt);
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zba (Address generation instructions) | 0.93 | Frozen |

Architecture Explanation：本指令等同于在移位前对 `rs1` 执行 `zext.w` 的 `slli`。

## 2.42. xnor

Synopsis：Exclusive NOR

Mnemonic：`xnor rd, rs1, rs2`

Encoding：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 0 0 1 rs1 rs2 0 0 0 0 0 1 0
OP XNOR XNOR
```

Description：本指令对 `rs1` 和 `rs2` 执行按位 exclusive-NOR 操作。

Operation：

```text
X(rd) = ~(X(rs1) ^ X(rs2));
```

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

## 2.43. zext.h

Synopsis：Zero-extend halfword

Mnemonic：`zext.h rd, rs`

Encoding (RV32)：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 0 1 1 0 rd 0 0 1 rs 0 0 0 0 0 0 0 1 0 0 0 0
OP ZEXT .H
```

Encoding (RV64)：

```text
0 6 7 11 12 14 15 19 20 24 25 31
1 1 0 1 1 1 0 rd 0 0 1 rs 0 0 0 0 0 0 0 1 0 0 0 0
OP-32 ZEXT .H
```

Description：本指令将源的最低有效半字零扩展到 `XLEN`，方法是在所有比 15 更高有效的比特中插入 0。

Operation：

```text
X(rd) = EXTZ(X(rs)[15..0]);
```

Note：`zext.h` 助记符在 RV32 和 RV64 中对应不同的指令编码。

Included in：

| Extension | Minimum version | Lifecycle state |
|---|---|---|
| Zbb (Basic bit-manipulation) | 0.93 | Frozen |

