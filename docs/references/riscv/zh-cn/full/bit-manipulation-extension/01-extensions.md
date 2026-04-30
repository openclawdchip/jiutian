# Chapter 1. Extensions

第一组发布用于公开审阅的 bitmanip 扩展是：

- 地址生成指令
- 基本位操作
- 无进位乘法
- 单比特指令

下面列出了这些扩展中包含的所有指令（以及伪指令）及其具体映射：

| RV32 | RV64 | Mnemonic | Instruction | Zba | Zbb | Zbc | Zbs |
|---|---|---|---|---|---|---|---|
|  | ✓ | `add.uw rd, rs1, rs2` | Add unsigned word | ✓ |  |  |  |
| ✓ | ✓ | `andn rd, rs1, rs2` | AND with inverted operand |  | ✓ |  |  |
| ✓ | ✓ | `clmul rd, rs1, rs2` | Carry-less multiply (low-part) |  |  | ✓ |  |
| ✓ | ✓ | `clmulh rd, rs1, rs2` | Carry-less multiply (high-part) |  |  | ✓ |  |
| ✓ | ✓ | `clmulr rd, rs1, rs2` | Carry-less multiply (reversed) |  |  | ✓ |  |
| ✓ | ✓ | `clz rd, rs` | Count leading zero bits |  | ✓ |  |  |
|  | ✓ | `clzw rd, rs` | Count leading zero bits in word |  | ✓ |  |  |
| ✓ | ✓ | `cpop rd, rs` | Count set bits |  | ✓ |  |  |
|  | ✓ | `cpopw rd, rs` | Count set bits in word |  | ✓ |  |  |
| ✓ | ✓ | `ctz rd, rs` | Count trailing zero bits |  | ✓ |  |  |
|  | ✓ | `ctzw rd, rs` | Count trailing zero bits in word |  | ✓ |  |  |
| ✓ | ✓ | `max rd, rs1, rs2` | Maximum |  | ✓ |  |  |
| ✓ | ✓ | `maxu rd, rs1, rs2` | Unsigned maximum |  | ✓ |  |  |
| ✓ | ✓ | `min rd, rs1, rs2` | Minimum |  | ✓ |  |  |
| ✓ | ✓ | `minu rd, rs1, rs2` | Unsigned minimum |  | ✓ |  |  |
| ✓ | ✓ | `orc.b rd, rs` | Bitwise OR-Combine, byte granule |  | ✓ |  |  |
| ✓ | ✓ | `orn rd, rs1, rs2` | OR with inverted operand |  | ✓ |  |  |
| ✓ | ✓ | `rev8 rd, rs` | Byte-reverse register |  | ✓ |  |  |
| ✓ | ✓ | `rol rd, rs1, rs2` | Rotate left (Register) |  | ✓ |  |  |
|  | ✓ | `rolw rd, rs1, rs2` | Rotate Left Word (Register) |  | ✓ |  |  |
| ✓ | ✓ | `ror rd, rs1, rs2` | Rotate right (Register) |  | ✓ |  |  |
| ✓ | ✓ | `rori rd, rs1, shamt` | Rotate right (Immediate) |  | ✓ |  |  |
|  | ✓ | `roriw rd, rs1, shamt` | Rotate right Word (Immediate) |  | ✓ |  |  |
|  | ✓ | `rorw rd, rs1, rs2` | Rotate right Word (Register) |  | ✓ |  |  |
| ✓ | ✓ | `bclr rd, rs1, rs2` | Single-Bit Clear (Register) |  |  |  | ✓ |
| ✓ | ✓ | `bclri rd, rs1, imm` | Single-Bit Clear (Immediate) |  |  |  | ✓ |
| ✓ | ✓ | `bext rd, rs1, rs2` | Single-Bit Extract (Register) |  |  |  | ✓ |
| ✓ | ✓ | `bexti rd, rs1, imm` | Single-Bit Extract (Immediate) |  |  |  | ✓ |
| ✓ | ✓ | `binv rd, rs1, rs2` | Single-Bit Invert (Register) |  |  |  | ✓ |
| ✓ | ✓ | `binvi rd, rs1, imm` | Single-Bit Invert (Immediate) |  |  |  | ✓ |
| ✓ | ✓ | `bset rd, rs1, rs2` | Single-Bit Set (Register) |  |  |  | ✓ |
| ✓ | ✓ | `bseti rd, rs1, imm` | Single-Bit Set (Immediate) |  |  |  | ✓ |
| ✓ | ✓ | `sext.b rd, rs` | Sign-extend byte |  | ✓ |  |  |
| ✓ | ✓ | `sext.h rd, rs` | Sign-extend halfword |  | ✓ |  |  |
| ✓ | ✓ | `sh1add rd, rs1, rs2` | Shift left by 1 and add | ✓ |  |  |  |
|  | ✓ | `sh1add.uw rd, rs1, rs2` | Shift unsigned word left by 1 and add | ✓ |  |  |  |
| ✓ | ✓ | `sh2add rd, rs1, rs2` | Shift left by 2 and add | ✓ |  |  |  |
|  | ✓ | `sh2add.uw rd, rs1, rs2` | Shift unsigned word left by 2 and add | ✓ |  |  |  |
| ✓ | ✓ | `sh3add rd, rs2, rs2` | Shift left by 3 and add | ✓ |  |  |  |
|  | ✓ | `sh3add.uw rd, rs1, rs2` | Shift unsigned word left by 3 and add | ✓ |  |  |  |
|  | ✓ | `slli.uw rd, rs1, imm` | Shift-left unsigned word (Immediate) | ✓ |  |  |  |
| ✓ | ✓ | `xnor rd, rs1, rs2` | Exclusive NOR |  | ✓ |  |  |
| ✓ | ✓ | `zext.h rd, rs` | Zero-extend halfword |  | ✓ |  |  |

## 1.1. Zba extension

说明：`Zba` 扩展已冻结。

`Zba` 指令可用于加速地址生成，这些地址使用无符号字大小索引和 `XLEN` 大小索引，对基本类型（半字、字、双字）数组进行索引：左移后的索引被加到基地址上。

移位加法指令执行左移 1、2 或 3 位，因为这些形式在真实代码中很常见，并且除简单加法器之外，只需要最少量的额外硬件即可实现。这避免了在实现中拉长关键路径。

虽然移位加法指令的最大左移量限制为 3，但基础 ISA 中的 `slli` 指令可用于对更宽元素数组的索引执行类似移位。本扩展新增的 `slli.uw` 可在索引应被解释为无符号字时使用。

以下指令构成 `Zba` 扩展：

| RV32 | RV64 | Mnemonic | Instruction |
|---|---|---|---|
|  | ✓ | `add.uw rd, rs1, rs2` | Add unsigned word |
| ✓ | ✓ | `sh1add rd, rs1, rs2` | Shift left by 1 and add |
|  | ✓ | `sh1add.uw rd, rs1, rs2` | Shift unsigned word left by 1 and add |
| ✓ | ✓ | `sh2add rd, rs1, rs2` | Shift left by 2 and add |
|  | ✓ | `sh2add.uw rd, rs1, rs2` | Shift unsigned word left by 2 and add |
| ✓ | ✓ | `sh3add rd, rs2, rs2` | Shift left by 3 and add |
|  | ✓ | `sh3add.uw rd, rs1, rs2` | Shift unsigned word left by 3 and add |
|  | ✓ | `slli.uw rd, rs1, imm` | Shift-left unsigned word (Immediate) |

## 1.2. Zbb: Basic bit-manipulation

说明：`Zbb` 扩展已冻结。

### 1.2.1. Logical with negate

| RV32 | RV64 | Mnemonic | Instruction |
|---|---|---|---|
| ✓ | ✓ | `andn rd, rs1, rs2` | AND with inverted operand |
| ✓ | ✓ | `orn rd, rs1, rs2` | OR with inverted operand |
| ✓ | ✓ | `xnor rd, rs1, rs2` | Exclusive NOR |

实现提示：`Logical with Negate` 指令可通过对基础要求的 `AND`、`OR` 和 `XOR` 逻辑指令的 `rs2` 输入取反来实现。在某些实现中，可复用用于减法的 `rs2` 反相器来完成此用途。

### 1.2.2. Count leading/trailing zero bits

| RV32 | RV64 | Mnemonic | Instruction |
|---|---|---|---|
| ✓ | ✓ | `clz rd, rs` | Count leading zero bits |
|  | ✓ | `clzw rd, rs` | Count leading zero bits in word |
| ✓ | ✓ | `ctz rd, rs` | Count trailing zero bits |
|  | ✓ | `ctzw rd, rs` | Count trailing zero bits in word |

### 1.2.3. Count population

这些指令计算置位比特（1 比特）的数量。这通常也称为 population count。

| RV32 | RV64 | Mnemonic | Instruction |
|---|---|---|---|
| ✓ | ✓ | `cpop rd, rs` | Count set bits |
|  | ✓ | `cpopw rd, rs` | Count set bits in word |

### 1.2.4. Integer minimum/maximum

整数最小值/最大值指令是算术 R-type 指令，返回两个操作数中较小或较大的一个。

| RV32 | RV64 | Mnemonic | Instruction |
|---|---|---|---|
| ✓ | ✓ | `max rd, rs1, rs2` | Maximum |
| ✓ | ✓ | `maxu rd, rs1, rs2` | Unsigned maximum |
| ✓ | ✓ | `min rd, rs1, rs2` | Minimum |
| ✓ | ✓ | `minu rd, rs1, rs2` | Unsigned minimum |

### 1.2.5. Sign- and zero-extension

这些指令对源寄存器的最低有效 8 位、16 位或 32 位执行符号扩展或零扩展。

这些指令替代通用惯用序列 `slli rD,rS,(XLEN-<size>) + srli`（用于零扩展）或 `slli + srai`（用于符号扩展），适用于 8 位和 16 位量的符号扩展，以及 16 位和 32 位量的零扩展。

| RV32 | RV64 | Mnemonic | Instruction |
|---|---|---|---|
| ✓ | ✓ | `sext.b rd, rs` | Sign-extend byte |
| ✓ | ✓ | `sext.h rd, rs` | Sign-extend halfword |
| ✓ | ✓ | `zext.h rd, rs` | Zero-extend halfword |

### 1.2.6. Bitwise rotation

按位循环移位指令类似于基础规范中的逻辑移位操作。不过，逻辑移位指令移入零，而循环移位指令会移入从值另一侧移出的比特。这类操作也称为“循环移位”。

| RV32 | RV64 | Mnemonic | Instruction |
|---|---|---|---|
| ✓ | ✓ | `rol rd, rs1, rs2` | Rotate left (Register) |
|  | ✓ | `rolw rd, rs1, rs2` | Rotate Left Word (Register) |
| ✓ | ✓ | `ror rd, rs1, rs2` | Rotate right (Register) |
| ✓ | ✓ | `rori rd, rs1, shamt` | Rotate right (Immediate) |
|  | ✓ | `roriw rd, rs1, shamt` | Rotate right Word (Immediate) |
|  | ✓ | `rorw rd, rs1, rs2` | Rotate right Word (Register) |

架构说明：包含循环移位指令是为了替代一种常见的四指令序列，以达到相同效果：`neg; sll/srl; srl/sll; or`。

### 1.2.7. OR Combine

如果 `rs` 对应字节中没有任何比特被置位，则 `orc.b` 将结果 `rd` 中该字节的所有比特设为全零；如果 `rs` 对应字节中任意比特被置位，则设为全一。

一个使用场景是字符串处理函数，例如 `strlen` 和 `strcpy`，它们可以使用 `orc.b` 测试终止零字节，方法是统计一个字中前导非零字节中的置位比特。

| RV32 | RV64 | Mnemonic | Instruction |
|---|---|---|---|
| ✓ | ✓ | `orc.b rd, rs` | Bitwise OR-Combine, byte granule |

### 1.2.8. Byte-reverse

`rev8` 反转 `rs` 的字节顺序。

| RV32 | RV64 | Mnemonic | Instruction |
|---|---|---|---|
| ✓ | ✓ | `rev8 rd, rs` | Byte-reverse register |

## 1.3. Zbc: Carry-less multiplication

说明：`Zbc` 扩展已冻结。

无进位乘法是在 GF(2) 上的多项式环中的乘法。

`clmul` 产生无进位乘积的低半部分，`clmulh` 产生 `2 * XLEN` 无进位乘积的高半部分。

`clmulr` 产生 `2 * XLEN` 无进位乘积的 `2*XLEN-2:XLEN-1` 位。

| RV32 | RV64 | Mnemonic | Instruction |
|---|---|---|---|
| ✓ | ✓ | `clmul rd, rs1, rs2` | Carry-less multiply (low-part) |
| ✓ | ✓ | `clmulh rd, rs1, rs2` | Carry-less multiply (high-part) |
| ✓ | ✓ | `clmulr rd, rs1, rs2` | Carry-less multiply (reversed) |

## 1.4. Zbs: Single-bit instructions

说明：`Zbs` 扩展已冻结。

单比特指令提供一种在寄存器中设置、清除、取反或提取单个比特的机制。该比特由其索引指定。

| RV32 | RV64 | Mnemonic | Instruction |
|---|---|---|---|
| ✓ | ✓ | `bclr rd, rs1, rs2` | Single-Bit Clear (Register) |
| ✓ | ✓ | `bclri rd, rs1, imm` | Single-Bit Clear (Immediate) |
| ✓ | ✓ | `bext rd, rs1, rs2` | Single-Bit Extract (Register) |
| ✓ | ✓ | `bexti rd, rs1, imm` | Single-Bit Extract (Immediate) |
| ✓ | ✓ | `binv rd, rs1, rs2` | Single-Bit Invert (Register) |
| ✓ | ✓ | `binvi rd, rs1, imm` | Single-Bit Invert (Immediate) |
| ✓ | ✓ | `bset rd, rs1, rs2` | Single-Bit Set (Register) |
| ✓ | ✓ | `bseti rd, rs1, imm` | Single-Bit Set (Immediate) |

