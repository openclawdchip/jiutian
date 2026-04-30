# Chapter 25 RISC-V Assembly Programmer's Handbook

本章是 assembly programmer's manual 的占位章。

表 25.1 列出 `x` 和 `f` 寄存器的 assembler mnemonics，以及它们在第一个标准 calling convention 中的角色。

表 25.1：RISC-V integer 和 floating-point registers 的 assembler mnemonics，以及它们在第一个标准 calling convention 中的角色。

| Register | ABI Name | Description | Saver |
|---|---|---|---|
| `x0` | `zero` | 硬连线为零 | - |
| `x1` | `ra` | Return address | Caller |
| `x2` | `sp` | Stack pointer | Callee |
| `x3` | `gp` | Global pointer | - |
| `x4` | `tp` | Thread pointer | - |
| `x5` | `t0` | Temporary/alternate link register | Caller |
| `x6-x7` | `t1-t2` | Temporaries | Caller |
| `x8` | `s0/fp` | Saved register/frame pointer | Callee |
| `x9` | `s1` | Saved register | Callee |
| `x10-x11` | `a0-a1` | Function arguments/return values | Caller |
| `x12-x17` | `a2-a7` | Function arguments | Caller |
| `x18-x27` | `s2-s11` | Saved registers | Callee |
| `x28-x31` | `t3-t6` | Temporaries | Caller |
| `f0-f7` | `ft0-ft7` | FP temporaries | Caller |
| `f8-f9` | `fs0-fs1` | FP saved registers | Callee |
| `f10-f11` | `fa0-fa1` | FP arguments/return values | Caller |
| `f12-f17` | `fa2-fa7` | FP arguments | Caller |
| `f18-f27` | `fs2-fs11` | FP saved registers | Callee |
| `f28-f31` | `ft8-ft11` | FP temporaries | Caller |

未来可能会有不同的 calling conventions，但要注意，寄存器 `x1`、`x2` 和 `x5` 在标准 ISA 和/或 compressed extension 中编码了特殊含义。

表 25.2 和表 25.3 包含标准 RISC-V pseudoinstructions 的清单。

表 25.2：RISC-V pseudoinstructions。

| Pseudoinstruction | Base Instruction(s) | Meaning |
|---|---|---|
| `la rd, symbol`（non-PIC） | `auipc rd, delta[31:12] + delta[11]`；`addi rd, rd, delta[11:0]` | 加载 absolute address，其中 `delta = symbol - pc` |
| `la rd, symbol`（PIC） | `auipc rd, delta[31:12] + delta[11]`；`l{w|d} rd, rd, delta[11:0]` | 加载 absolute address，其中 `delta = GOT[symbol] - pc` |
| `lla rd, symbol` | `auipc rd, delta[31:12] + delta[11]`；`addi rd, rd, delta[11:0]` | 加载 local address，其中 `delta = symbol - pc` |
| `l{b|h|w|d} rd, symbol` | `auipc rd, delta[31:12] + delta[11]`；`l{b|h|w|d} rd, delta[11:0](rd)` | Load global |
| `s{b|h|w|d} rd, symbol, rt` | `auipc rt, delta[31:12] + delta[11]`；`s{b|h|w|d} rd, delta[11:0](rt)` | Store global |
| `fl{w|d} rd, symbol, rt` | `auipc rt, delta[31:12] + delta[11]`；`fl{w|d} rd, delta[11:0](rt)` | Floating-point load global |
| `fs{w|d} rd, symbol, rt` | `auipc rt, delta[31:12] + delta[11]`；`fs{w|d} rd, delta[11:0](rt)` | Floating-point store global |

基础指令使用 pc-relative addressing，因此 linker 从 `symbol` 中减去 `pc` 得到 `delta`。linker 把 `delta[11]` 加到 20 位高半部分，以抵消 12 位低半部分的符号扩展。

| Pseudoinstruction | Base Instruction(s) | Meaning |
|---|---|---|
| `nop` | `addi x0, x0, 0` | No operation |
| `li rd, immediate` | Myriad sequences | Load immediate |
| `mv rd, rs` | `addi rd, rs, 0` | Copy register |
| `not rd, rs` | `xori rd, rs, -1` | One's complement |
| `neg rd, rs` | `sub rd, x0, rs` | Two's complement |
| `negw rd, rs` | `subw rd, x0, rs` | Two's complement word |
| `sext.w rd, rs` | `addiw rd, rs, 0` | Sign extend word |
| `seqz rd, rs` | `sltiu rd, rs, 1` | Set if `= zero` |
| `snez rd, rs` | `sltu rd, x0, rs` | Set if `!= zero` |
| `sltz rd, rs` | `slt rd, rs, x0` | Set if `< zero` |
| `sgtz rd, rs` | `slt rd, x0, rs` | Set if `> zero` |
| `fmv.s rd, rs` | `fsgnj.s rd, rs, rs` | Copy single-precision register |
| `fabs.s rd, rs` | `fsgnjx.s rd, rs, rs` | Single-precision absolute value |
| `fneg.s rd, rs` | `fsgnjn.s rd, rs, rs` | Single-precision negate |
| `fmv.d rd, rs` | `fsgnj.d rd, rs, rs` | Copy double-precision register |
| `fabs.d rd, rs` | `fsgnjx.d rd, rs, rs` | Double-precision absolute value |
| `fneg.d rd, rs` | `fsgnjn.d rd, rs, rs` | Double-precision negate |
| `beqz rs, offset` | `beq rs, x0, offset` | Branch if `= zero` |
| `bnez rs, offset` | `bne rs, x0, offset` | Branch if `!= zero` |
| `blez rs, offset` | `bge x0, rs, offset` | Branch if `<= zero` |
| `bgez rs, offset` | `bge rs, x0, offset` | Branch if `>= zero` |
| `bltz rs, offset` | `blt rs, x0, offset` | Branch if `< zero` |
| `bgtz rs, offset` | `blt x0, rs, offset` | Branch if `> zero` |
| `bgt rs, rt, offset` | `blt rt, rs, offset` | Branch if `>` |
| `ble rs, rt, offset` | `bge rt, rs, offset` | Branch if `<=` |
| `bgtu rs, rt, offset` | `bltu rt, rs, offset` | Branch if `>`, unsigned |
| `bleu rs, rt, offset` | `bgeu rt, rs, offset` | Branch if `<=`, unsigned |

表 25.3：RISC-V pseudoinstructions。

| Pseudoinstruction | Base Instruction | Meaning |
|---|---|---|
| `j offset` | `jal x0, offset` | Jump |
| `jal offset` | `jal x1, offset` | Jump and link |
| `jr rs` | `jalr x0, 0(rs)` | Jump register |
| `jalr rs` | `jalr x1, 0(rs)` | Jump and link register |
| `ret` | `jalr x0, 0(x1)` | Return from subroutine |
| `call offset` | `auipc x1, offset[31:12] + offset[11]`；`jalr x1, offset[11:0](x1)` | Call far-away subroutine |
| `tail offset` | `auipc x6, offset[31:12] + offset[11]`；`jalr x0, offset[11:0](x6)` | Tail call far-away subroutine |
| `fence` | `fence iorw, iorw` | Fence on all memory and I/O |
| `rdinstret[h] rd` | `csrrs rd, instret[h], x0` | Read instructions-retired counter |
| `rdcycle[h] rd` | `csrrs rd, cycle[h], x0` | Read cycle counter |
| `rdtime[h] rd` | `csrrs rd, time[h], x0` | Read real-time clock |
| `csrr rd, csr` | `csrrs rd, csr, x0` | Read CSR |
| `csrw csr, rs` | `csrrw x0, csr, rs` | Write CSR |
| `csrs csr, rs` | `csrrs x0, csr, rs` | Set bits in CSR |
| `csrc csr, rs` | `csrrc x0, csr, rs` | Clear bits in CSR |
| `csrwi csr, imm` | `csrrwi x0, csr, imm` | Write CSR, immediate |
| `csrsi csr, imm` | `csrrsi x0, csr, imm` | Set bits in CSR, immediate |
| `csrci csr, imm` | `csrrci x0, csr, imm` | Clear bits in CSR, immediate |
| `frcsr rd` | `csrrs rd, fcsr, x0` | Read FP control/status register |
| `fscsr rd, rs` | `csrrw rd, fcsr, rs` | Swap FP control/status register |
| `fscsr rs` | `csrrw x0, fcsr, rs` | Write FP control/status register |
| `frrm rd` | `csrrs rd, frm, x0` | Read FP rounding mode |
| `fsrm rd, rs` | `csrrw rd, frm, rs` | Swap FP rounding mode |
| `fsrm rs` | `csrrw x0, frm, rs` | Write FP rounding mode |
| `frflags rd` | `csrrs rd, fflags, x0` | Read FP exception flags |
| `fsflags rd, rs` | `csrrw rd, fflags, rs` | Swap FP exception flags |
| `fsflags rs` | `csrrw x0, fflags, rs` | Write FP exception flags |
