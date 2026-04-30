# Chapter 24 RV32/64G Instruction Set Listings

RISC-V 项目的目标之一，是让 RISC-V 可以作为稳定的软件开发目标使用。为此，本规范把一个基础 ISA（RV32I 或 RV64I）加上选定标准扩展（IMAFD、`Zicsr`、`Zifencei`）定义为 “general-purpose” ISA，并使用缩写 `G` 表示 `IMAFDZicsr_Zifencei` 这一指令集扩展组合。本章给出 RV32G 和 RV64G 的 opcode maps 与 instruction-set listings。

表 24.1：RISC-V base opcode map，`inst[1:0]=11`。列为 `inst[4:2]`，行为 `inst[6:5]`。

| `inst[6:5]` / `inst[4:2]` | `000` | `001` | `010` | `011` | `100` | `101` | `110` | `111` | `>32b` |
|---|---|---|---|---|---|---|---|---|---|
| `00` | `LOAD` | `LOAD-FP` | `custom-0` | `MISC-MEM` | `OP-IMM` | `AUIPC` | `OP-IMM-32` |  | `48b` |
| `01` | `STORE` | `STORE-FP` | `custom-1` | `AMO` | `OP` | `LUI` | `OP-32` |  | `64b` |
| `10` | `MADD` | `MSUB` | `NMSUB` | `NMADD` | `OP-FP` | `reserved` | `custom-2/rv128` |  | `48b` |
| `11` | `BRANCH` | `JALR` | `reserved` | `JAL` | `SYSTEM` | `reserved` | `custom-3/rv128` |  | `>=80b` |

表 24.1 给出 RVG 的 major opcodes 映射。低位中有 3 个或更多位被置 1 的 major opcodes 保留给长度大于 32 位的指令。标记为 `reserved` 的 opcodes 应避免用于 custom instruction-set extensions，因为它们可能被未来标准扩展使用。标记为 `custom-0` 和 `custom-1` 的 major opcodes 将被未来标准扩展避开，建议在基础 32 位指令格式内用于 custom instruction-set extensions。标记为 `custom-2/rv128` 和 `custom-3/rv128` 的 opcodes 保留给 RV128 未来使用；除此之外它们也会被标准扩展避开，因此在 RV32 和 RV64 中也可用于 custom instruction-set extensions。

我们认为 RV32G 和 RV64G 为广泛的 general-purpose computing 提供了简单但完整的指令集。第 16 章描述的可选 compressed instruction set 可以加入其中，形成 RV32GC 和 RV64GC，以提高性能、代码大小和能效，但会带来一些额外硬件复杂度。

当从 IMAFDC 继续扩展到更多 instruction-set extensions 时，新增指令往往更偏领域专用，只对受限类别的应用有益，例如 multimedia 或 security。与大多数商业 ISA 不同，RISC-V ISA 设计清楚地区分基础 ISA、广泛适用的标准扩展，以及这些更专门化的附加内容。第 26 章更详细讨论了向 RISC-V ISA 添加扩展的方式。

下面的清单使用源文档中的字段名和指令名。字段行给出对应指令格式中从位 31 到位 0 的编码字段；随后的条目给出各指令的编码字段取值和助记名。

## Instruction Format Fields

```text
31      27 26 25 24   20 19   15 14   12 11    7 6      0
funct7      rs2        rs1     funct3  rd       opcode   R-type
imm[11:0]              rs1     funct3  rd       opcode   I-type
imm[11:5]  rs2        rs1     funct3  imm[4:0] opcode   S-type
imm[12|10:5] rs2      rs1     funct3  imm[4:1|11] opcode B-type
imm[31:12]                       rd    opcode            U-type
imm[20|10:1|11|19:12]            rd    opcode            J-type
```

## RV32I Base Instruction Set

```text
imm[31:12] rd 0110111 LUI
imm[31:12] rd 0010111 AUIPC
imm[20|10:1|11|19:12] rd 1101111 JAL
imm[11:0] rs1 000 rd 1100111 JALR
imm[12|10:5] rs2 rs1 000 imm[4:1|11] 1100011 BEQ
imm[12|10:5] rs2 rs1 001 imm[4:1|11] 1100011 BNE
imm[12|10:5] rs2 rs1 100 imm[4:1|11] 1100011 BLT
imm[12|10:5] rs2 rs1 101 imm[4:1|11] 1100011 BGE
imm[12|10:5] rs2 rs1 110 imm[4:1|11] 1100011 BLTU
imm[12|10:5] rs2 rs1 111 imm[4:1|11] 1100011 BGEU
imm[11:0] rs1 000 rd 0000011 LB
imm[11:0] rs1 001 rd 0000011 LH
imm[11:0] rs1 010 rd 0000011 LW
imm[11:0] rs1 100 rd 0000011 LBU
imm[11:0] rs1 101 rd 0000011 LHU
imm[11:5] rs2 rs1 000 imm[4:0] 0100011 SB
imm[11:5] rs2 rs1 001 imm[4:0] 0100011 SH
imm[11:5] rs2 rs1 010 imm[4:0] 0100011 SW
imm[11:0] rs1 000 rd 0010011 ADDI
imm[11:0] rs1 010 rd 0010011 SLTI
imm[11:0] rs1 011 rd 0010011 SLTIU
imm[11:0] rs1 100 rd 0010011 XORI
imm[11:0] rs1 110 rd 0010011 ORI
imm[11:0] rs1 111 rd 0010011 ANDI
0000000 shamt rs1 001 rd 0010011 SLLI
0000000 shamt rs1 101 rd 0010011 SRLI
0100000 shamt rs1 101 rd 0010011 SRAI
0000000 rs2 rs1 000 rd 0110011 ADD
0100000 rs2 rs1 000 rd 0110011 SUB
0000000 rs2 rs1 001 rd 0110011 SLL
0000000 rs2 rs1 010 rd 0110011 SLT
0000000 rs2 rs1 011 rd 0110011 SLTU
0000000 rs2 rs1 100 rd 0110011 XOR
0000000 rs2 rs1 101 rd 0110011 SRL
0100000 rs2 rs1 101 rd 0110011 SRA
0000000 rs2 rs1 110 rd 0110011 OR
0000000 rs2 rs1 111 rd 0110011 AND
fm pred succ rs1 000 rd 0001111 FENCE
000000000000 00000 000 00000 1110011 ECALL
000000000001 00000 000 00000 1110011 EBREAK
```

## RV64I Base Instruction Set

以下指令是在 RV32I 之外由 RV64I 增加的指令。

```text
imm[11:0] rs1 110 rd 0000011 LWU
imm[11:0] rs1 011 rd 0000011 LD
imm[11:5] rs2 rs1 011 imm[4:0] 0100011 SD
000000 shamt rs1 001 rd 0010011 SLLI
000000 shamt rs1 101 rd 0010011 SRLI
010000 shamt rs1 101 rd 0010011 SRAI
imm[11:0] rs1 000 rd 0011011 ADDIW
0000000 shamt rs1 001 rd 0011011 SLLIW
0000000 shamt rs1 101 rd 0011011 SRLIW
0100000 shamt rs1 101 rd 0011011 SRAIW
0000000 rs2 rs1 000 rd 0111011 ADDW
0100000 rs2 rs1 000 rd 0111011 SUBW
0000000 rs2 rs1 001 rd 0111011 SLLW
0000000 rs2 rs1 101 rd 0111011 SRLW
0100000 rs2 rs1 101 rd 0111011 SRAW
```

## RV32/RV64 `Zifencei` Standard Extension

```text
imm[11:0] rs1 001 rd 0001111 FENCE.I
```

## RV32/RV64 `Zicsr` Standard Extension

```text
csr rs1 001 rd 1110011 CSRRW
csr rs1 010 rd 1110011 CSRRS
csr rs1 011 rd 1110011 CSRRC
csr uimm 101 rd 1110011 CSRRWI
csr uimm 110 rd 1110011 CSRRSI
csr uimm 111 rd 1110011 CSRRCI
```

## RV32M Standard Extension

```text
0000001 rs2 rs1 000 rd 0110011 MUL
0000001 rs2 rs1 001 rd 0110011 MULH
0000001 rs2 rs1 010 rd 0110011 MULHSU
0000001 rs2 rs1 011 rd 0110011 MULHU
0000001 rs2 rs1 100 rd 0110011 DIV
0000001 rs2 rs1 101 rd 0110011 DIVU
0000001 rs2 rs1 110 rd 0110011 REM
0000001 rs2 rs1 111 rd 0110011 REMU
```

## RV64M Standard Extension

以下指令是在 RV32M 之外由 RV64M 增加的指令。

```text
0000001 rs2 rs1 000 rd 0111011 MULW
0000001 rs2 rs1 100 rd 0111011 DIVW
0000001 rs2 rs1 101 rd 0111011 DIVUW
0000001 rs2 rs1 110 rd 0111011 REMW
0000001 rs2 rs1 111 rd 0111011 REMUW
```

## RV32A Standard Extension

```text
00010 aq rl 00000 rs1 010 rd 0101111 LR.W
00011 aq rl rs2 rs1 010 rd 0101111 SC.W
00001 aq rl rs2 rs1 010 rd 0101111 AMOSWAP.W
00000 aq rl rs2 rs1 010 rd 0101111 AMOADD.W
00100 aq rl rs2 rs1 010 rd 0101111 AMOXOR.W
01100 aq rl rs2 rs1 010 rd 0101111 AMOAND.W
01000 aq rl rs2 rs1 010 rd 0101111 AMOOR.W
10000 aq rl rs2 rs1 010 rd 0101111 AMOMIN.W
10100 aq rl rs2 rs1 010 rd 0101111 AMOMAX.W
11000 aq rl rs2 rs1 010 rd 0101111 AMOMINU.W
11100 aq rl rs2 rs1 010 rd 0101111 AMOMAXU.W
```

## RV64A Standard Extension

以下指令是在 RV32A 之外由 RV64A 增加的指令。

```text
00010 aq rl 00000 rs1 011 rd 0101111 LR.D
00011 aq rl rs2 rs1 011 rd 0101111 SC.D
00001 aq rl rs2 rs1 011 rd 0101111 AMOSWAP.D
00000 aq rl rs2 rs1 011 rd 0101111 AMOADD.D
00100 aq rl rs2 rs1 011 rd 0101111 AMOXOR.D
01100 aq rl rs2 rs1 011 rd 0101111 AMOAND.D
01000 aq rl rs2 rs1 011 rd 0101111 AMOOR.D
10000 aq rl rs2 rs1 011 rd 0101111 AMOMIN.D
10100 aq rl rs2 rs1 011 rd 0101111 AMOMAX.D
11000 aq rl rs2 rs1 011 rd 0101111 AMOMINU.D
11100 aq rl rs2 rs1 011 rd 0101111 AMOMAXU.D
```

## Floating-Point Instruction Format Fields

```text
31      27 26 25 24   20 19   15 14   12 11    7 6      0
funct7      rs2        rs1     funct3  rd       opcode   R-type
rs3     funct2 rs2     rs1     funct3  rd       opcode   R4-type
imm[11:0]              rs1     funct3  rd       opcode   I-type
imm[11:5]  rs2        rs1     funct3  imm[4:0] opcode   S-type
```

## RV32F Standard Extension

```text
imm[11:0] rs1 010 rd 0000111 FLW
imm[11:5] rs2 rs1 010 imm[4:0] 0100111 FSW
rs3 00 rs2 rs1 rm rd 1000011 FMADD.S
rs3 00 rs2 rs1 rm rd 1000111 FMSUB.S
rs3 00 rs2 rs1 rm rd 1001011 FNMSUB.S
rs3 00 rs2 rs1 rm rd 1001111 FNMADD.S
0000000 rs2 rs1 rm rd 1010011 FADD.S
0000100 rs2 rs1 rm rd 1010011 FSUB.S
0001000 rs2 rs1 rm rd 1010011 FMUL.S
0001100 rs2 rs1 rm rd 1010011 FDIV.S
0101100 00000 rs1 rm rd 1010011 FSQRT.S
0010000 rs2 rs1 000 rd 1010011 FSGNJ.S
0010000 rs2 rs1 001 rd 1010011 FSGNJN.S
0010000 rs2 rs1 010 rd 1010011 FSGNJX.S
0010100 rs2 rs1 000 rd 1010011 FMIN.S
0010100 rs2 rs1 001 rd 1010011 FMAX.S
1100000 00000 rs1 rm rd 1010011 FCVT.W.S
1100000 00001 rs1 rm rd 1010011 FCVT.WU.S
1110000 00000 rs1 000 rd 1010011 FMV.X.W
1010000 rs2 rs1 010 rd 1010011 FEQ.S
1010000 rs2 rs1 001 rd 1010011 FLT.S
1010000 rs2 rs1 000 rd 1010011 FLE.S
1110000 00000 rs1 001 rd 1010011 FCLASS.S
1101000 00000 rs1 rm rd 1010011 FCVT.S.W
1101000 00001 rs1 rm rd 1010011 FCVT.S.WU
1111000 00000 rs1 000 rd 1010011 FMV.W.X
```

## RV64F Standard Extension

以下指令是在 RV32F 之外由 RV64F 增加的指令。

```text
1100000 00010 rs1 rm rd 1010011 FCVT.L.S
1100000 00011 rs1 rm rd 1010011 FCVT.LU.S
1101000 00010 rs1 rm rd 1010011 FCVT.S.L
1101000 00011 rs1 rm rd 1010011 FCVT.S.LU
```

## RV32D Standard Extension

```text
imm[11:0] rs1 011 rd 0000111 FLD
imm[11:5] rs2 rs1 011 imm[4:0] 0100111 FSD
rs3 01 rs2 rs1 rm rd 1000011 FMADD.D
rs3 01 rs2 rs1 rm rd 1000111 FMSUB.D
rs3 01 rs2 rs1 rm rd 1001011 FNMSUB.D
rs3 01 rs2 rs1 rm rd 1001111 FNMADD.D
0000001 rs2 rs1 rm rd 1010011 FADD.D
0000101 rs2 rs1 rm rd 1010011 FSUB.D
0001001 rs2 rs1 rm rd 1010011 FMUL.D
0001101 rs2 rs1 rm rd 1010011 FDIV.D
0101101 00000 rs1 rm rd 1010011 FSQRT.D
0010001 rs2 rs1 000 rd 1010011 FSGNJ.D
0010001 rs2 rs1 001 rd 1010011 FSGNJN.D
0010001 rs2 rs1 010 rd 1010011 FSGNJX.D
0010101 rs2 rs1 000 rd 1010011 FMIN.D
0010101 rs2 rs1 001 rd 1010011 FMAX.D
0100000 00001 rs1 rm rd 1010011 FCVT.S.D
0100001 00000 rs1 rm rd 1010011 FCVT.D.S
1010001 rs2 rs1 010 rd 1010011 FEQ.D
1010001 rs2 rs1 001 rd 1010011 FLT.D
1010001 rs2 rs1 000 rd 1010011 FLE.D
1110001 00000 rs1 001 rd 1010011 FCLASS.D
1100001 00000 rs1 rm rd 1010011 FCVT.W.D
1100001 00001 rs1 rm rd 1010011 FCVT.WU.D
1101001 00000 rs1 rm rd 1010011 FCVT.D.W
1101001 00001 rs1 rm rd 1010011 FCVT.D.WU
```

## RV64D Standard Extension

以下指令是在 RV32D 之外由 RV64D 增加的指令。

```text
1100001 00010 rs1 rm rd 1010011 FCVT.L.D
1100001 00011 rs1 rm rd 1010011 FCVT.LU.D
1110001 00000 rs1 000 rd 1010011 FMV.X.D
1101001 00010 rs1 rm rd 1010011 FCVT.D.L
1101001 00011 rs1 rm rd 1010011 FCVT.D.LU
1111001 00000 rs1 000 rd 1010011 FMV.D.X
```

## RV32Q Standard Extension

```text
imm[11:0] rs1 100 rd 0000111 FLQ
imm[11:5] rs2 rs1 100 imm[4:0] 0100111 FSQ
rs3 11 rs2 rs1 rm rd 1000011 FMADD.Q
rs3 11 rs2 rs1 rm rd 1000111 FMSUB.Q
rs3 11 rs2 rs1 rm rd 1001011 FNMSUB.Q
rs3 11 rs2 rs1 rm rd 1001111 FNMADD.Q
0000011 rs2 rs1 rm rd 1010011 FADD.Q
0000111 rs2 rs1 rm rd 1010011 FSUB.Q
0001011 rs2 rs1 rm rd 1010011 FMUL.Q
0001111 rs2 rs1 rm rd 1010011 FDIV.Q
0101111 00000 rs1 rm rd 1010011 FSQRT.Q
0010011 rs2 rs1 000 rd 1010011 FSGNJ.Q
0010011 rs2 rs1 001 rd 1010011 FSGNJN.Q
0010011 rs2 rs1 010 rd 1010011 FSGNJX.Q
0010111 rs2 rs1 000 rd 1010011 FMIN.Q
0010111 rs2 rs1 001 rd 1010011 FMAX.Q
0100000 00011 rs1 rm rd 1010011 FCVT.S.Q
0100011 00000 rs1 rm rd 1010011 FCVT.Q.S
0100001 00011 rs1 rm rd 1010011 FCVT.D.Q
0100011 00001 rs1 rm rd 1010011 FCVT.Q.D
1010011 rs2 rs1 010 rd 1010011 FEQ.Q
1010011 rs2 rs1 001 rd 1010011 FLT.Q
1010011 rs2 rs1 000 rd 1010011 FLE.Q
1110011 00000 rs1 001 rd 1010011 FCLASS.Q
1100011 00000 rs1 rm rd 1010011 FCVT.W.Q
1100011 00001 rs1 rm rd 1010011 FCVT.WU.Q
1101011 00000 rs1 rm rd 1010011 FCVT.Q.W
1101011 00001 rs1 rm rd 1010011 FCVT.Q.WU
```

## RV64Q Standard Extension

以下指令是在 RV32Q 之外由 RV64Q 增加的指令。

```text
1100011 00010 rs1 rm rd 1010011 FCVT.L.Q
1100011 00011 rs1 rm rd 1010011 FCVT.LU.Q
1101011 00010 rs1 rm rd 1010011 FCVT.Q.L
1101011 00011 rs1 rm rd 1010011 FCVT.Q.LU
```

表 24.2：RISC-V 指令清单。上面各节按源文档顺序列出 RV32I、RV64I、`Zifencei`、`Zicsr`、`M`、`A`、`F`、`D` 和 `Q` 相关编码。

表 24.3 列出当前已经分配 CSR 地址的 CSRs。timers、counters 和 floating-point CSRs 是本规范中定义的唯一 CSRs。

表 24.3：RISC-V control and status register（CSR）address map。

| Number | Privilege | Name | Description |
|---|---|---|---|
| `0x001` | Read/write | `fflags` | Floating-Point Accrued Exceptions. |
| `0x002` | Read/write | `frm` | Floating-Point Dynamic Rounding Mode. |
| `0x003` | Read/write | `fcsr` | Floating-Point Control and Status Register（`frm` + `fflags`）. |
| `0xC00` | Read-only | `cycle` | `RDCYCLE` instruction 的 cycle counter. |
| `0xC01` | Read-only | `time` | `RDTIME` instruction 的 timer. |
| `0xC02` | Read-only | `instret` | `RDINSTRET` instruction 的 instructions-retired counter. |
| `0xC80` | Read-only | `cycleh` | `cycle` 的高 32 位，仅 RV32I. |
| `0xC81` | Read-only | `timeh` | `time` 的高 32 位，仅 RV32I. |
| `0xC82` | Read-only | `instreth` | `instret` 的高 32 位，仅 RV32I. |
