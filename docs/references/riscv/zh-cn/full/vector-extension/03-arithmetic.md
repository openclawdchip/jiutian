# 10. Vector Arithmetic Instruction Formats

vector arithmetic 指令使用 `OP-V` 主 opcode，并通过 `funct6`、`funct3`、`vm`、`vs2`、`vs1/rs1/imm`、`vd` 等字段编码。`funct3` 区分 vector-vector (`OPIVV`/`OPMVV`/`OPFVV`)、vector-scalar (`OPIVX`/`OPMVX`/`OPFVF`) 与 vector-immediate (`OPIVI`) 等形式。

## 10.1. Vector Arithmetic Instruction encoding

整数操作的标量可以是 `rs1` 字段中编码的 5 bit immediate `imm[4:0]`，该值按指令要求符号扩展或零扩展；也可以来自 `rs1` 指定的标量 `x` register。浮点操作的标量来自标量 `f` register。vector-vector 操作读取 `vs2` 与 `vs1`，vector-scalar 操作读取 `vs2` 与标量，vector-immediate 操作读取 `vs2` 与 immediate。

所有算术指令均受 `vl`、`vstart` 和 mask 控制。active 元素执行语义；prestart 元素保持不变；inactive 与 tail 元素按 `vma/vta` 处理。指令完成后 `vstart` 复位为 0。

## 10.2. Widening Vector Arithmetic Instructions

widening 指令产生比输入宽 2 倍的结果。结果的 `EEW` 为 `2*SEW`，目的 `EMUL` 为 `2*LMUL`。若该 `EMUL` 超出合法范围或目的寄存器组不满足约束，编码保留或指令非法。widening 指令用于加减、乘法、MAC、reduction 和浮点转换等。

## 10.3. Narrowing Vector Arithmetic Instructions

narrowing 指令从较宽输入产生较窄结果。通常源操作数 `EEW` 为 `2*SEW`，目的元素宽度为当前 `SEW`，源 `EMUL` 大于目的 `LMUL`。缩窄右移、clip 和浮点窄化转换属于此类。它们通常结合 `vxrm` 指定的舍入模式，并可能设置 `vxsat`。

# 11. Vector Integer Arithmetic Instructions

整数算术指令覆盖单宽加减、拓宽加减、扩展、带进位/借位、逻辑、移位、比较、min/max、乘除、拓宽乘法、乘加、merge 和 move。

## 11.1. Vector Single-Width Integer Add and Subtract

```asm
vadd.vv  vd, vs2, vs1, vm
vadd.vx  vd, vs2, rs1, vm
vadd.vi  vd, vs2, imm, vm
vsub.vv  vd, vs2, vs1, vm
vsub.vx  vd, vs2, rs1, vm
vrsub.vx vd, vs2, rs1, vm
vrsub.vi vd, vs2, imm, vm
```

`vadd` 对 active 元素执行 modulo `2^SEW` 加法。`vsub` 计算 `vs2 - vs1/rs1`。`vrsub` 反向相减，计算 `rs1/imm - vs2`。溢出按二进制补码截断，不设置 `vxsat`。

## 11.2. Vector Widening Integer Add/Subtract

```asm
vwaddu.vv  vd, vs2, vs1, vm
vwaddu.vx  vd, vs2, rs1, vm
vwadd.vv   vd, vs2, vs1, vm
vwadd.vx   vd, vs2, rs1, vm
vwsubu.vv  vd, vs2, vs1, vm
vwsubu.vx  vd, vs2, rs1, vm
vwsub.vv   vd, vs2, vs1, vm
vwsub.vx   vd, vs2, rs1, vm
vwaddu.wv  vd, vs2, vs1, vm
vwaddu.wx  vd, vs2, rs1, vm
vwadd.wv   vd, vs2, vs1, vm
vwadd.wx   vd, vs2, rs1, vm
vwsubu.wv  vd, vs2, vs1, vm
vwsubu.wx  vd, vs2, rs1, vm
vwsub.wv   vd, vs2, vs1, vm
vwsub.wx   vd, vs2, rs1, vm
```

无符号形式零扩展输入，有符号形式符号扩展输入。`.w` 形式将一个 double-width `vs2` 与一个 single-width 源相加或相减，产生 double-width 结果。

## 11.3. Vector Integer Extension

```asm
vzext.vf2  vd, vs2, vm
vsext.vf2  vd, vs2, vm
vzext.vf4  vd, vs2, vm
vsext.vf4  vd, vs2, vm
vzext.vf8  vd, vs2, vm
vsext.vf8  vd, vs2, vm
```

这些指令把窄整数元素零扩展或符号扩展到当前 `SEW`。`vf2/vf4/vf8` 表示源元素宽度为目的元素宽度的 1/2、1/4、1/8。

## 11.4. Vector Integer Add-with-Carry / Subtract-with-Borrow Instructions

```asm
vadc.vvm   vd, vs2, vs1, v0
vadc.vxm   vd, vs2, rs1, v0
vadc.vim   vd, vs2, imm, v0
vmadc.vvm  vd, vs2, vs1, v0
vmadc.vx   vd, vs2, rs1, vm
vmadc.vi   vd, vs2, imm, vm
vsbc.vvm   vd, vs2, vs1, v0
vsbc.vxm   vd, vs2, rs1, v0
vmsbc.vvm  vd, vs2, vs1, v0
vmsbc.vx   vd, vs2, rs1, vm
```

`vadc` 把 mask 位作为 carry-in 加入；`vmadc` 产生 carry-out mask。`vsbc` 使用 borrow-in 执行减法；`vmsbc` 产生 borrow-out mask。carry/borrow 链用于多精度整数算术。产生 mask 的指令把结果写为一 bit-per-element mask。

## 11.5. Vector Bitwise Logical Instructions

```asm
vand.vv/vx/vi
vor.vv/vx/vi
vxor.vv/vx/vi
```

这些指令对 active 元素执行按位 AND、OR、XOR。immediate 形式使用 sign-extended 5 bit immediate。

## 11.6. Vector Single-Width Shift Instructions

```asm
vsll.vv/vx/vi
vsrl.vv/vx/vi
vsra.vv/vx/vi
```

`vsll` 逻辑左移，`vsrl` 逻辑右移，`vsra` 算术右移。移位量取低 `log2(SEW)` bit。

## 11.7. Vector Narrowing Integer Right Shift Instructions

```asm
vnsrl.wv/wx/wi
vnsra.wv/wx/wi
```

这些指令把 double-width 源右移并缩窄为 single-width 结果。`vnsrl` 为逻辑右移，`vnsra` 为算术右移。结果按低 `SEW` bit 写入目的。

## 11.8. Vector Integer Compare Instructions

```asm
vmseq.vv/vx/vi
vmsne.vv/vx/vi
vmsltu.vv/vx
vmslt.vv/vx
vmsleu.vv/vx/vi
vmsle.vv/vx/vi
vmsgtu.vx/vi
vmsgt.vx/vi
```

比较指令写入 mask destination，每个 active 元素产生 1 bit 结果。无符号形式带 `u`，有符号形式不带 `u`。一些大于比较由小于/小于等于形式的操作数交换或 immediate 形式提供。

## 11.9. Vector Integer Min/Max Instructions

```asm
vminu.vv/vx
vmin.vv/vx
vmaxu.vv/vx
vmax.vv/vx
```

`vminu/vmaxu` 使用无符号比较；`vmin/vmax` 使用有符号比较。

## 11.10. Vector Single-Width Integer Multiply Instructions

```asm
vmul.vv/vx
vmulh.vv/vx
vmulhu.vv/vx
vmulhsu.vv/vx
```

`vmul` 返回乘积低 `SEW` bit。`vmulh` 返回有符号乘积高半部分，`vmulhu` 返回无符号乘积高半部分，`vmulhsu` 返回有符号乘无符号乘积高半部分。

## 11.11. Vector Integer Divide Instructions

```asm
vdivu.vv/vx
vdiv.vv/vx
vremu.vv/vx
vrem.vv/vx
```

`vdivu/vremu` 为无符号除法和余数；`vdiv/vrem` 为有符号除法和余数。除零和有符号溢出遵循 RISC-V 标量整数除法约定，以便不引发 arithmetic trap。

## 11.12. Vector Widening Integer Multiply Instructions

```asm
vwmul.vv/vx
vwmulu.vv/vx
vwmulsu.vv/vx
```

这些指令将 single-width 输入相乘，产生 double-width 结果。有符号、无符号、signed-by-unsigned 形式分别由指令名区分。

## 11.13. Vector Single-Width Integer Multiply-Add Instructions

```asm
vmacc.vv/vx
vnmsac.vv/vx
vmadd.vv/vx
vnmsub.vv/vx
```

这些指令执行 single-width 乘加或乘减，结果截断到 `SEW`。`vmacc` 把乘积加到 accumulator，`vnmsac` 从 accumulator 减去乘积，`vmadd` 和 `vnmsub` 使用不同操作数作为加数/被加数以匹配常见代码生成模式。

## 11.14. Vector Widening Integer Multiply-Add Instructions

```asm
vwmaccu.vv/vx
vwmacc.vv/vx
vwmaccsu.vv/vx
vwmaccus.vx
```

widening multiply-add 将 single-width 输入相乘并累加到 double-width destination。`u` 与 `su/us` 后缀标明乘法输入的符号解释。

## 11.15. Vector Integer Merge Instructions

```asm
vmerge.vvm
vmerge.vxm
vmerge.vim
```

`vmerge` 根据 mask 从两个源选择元素。mask 位为 1 时选择第二源，mask 位为 0 时选择第一源。该指令总是使用 mask 形式。

## 11.16. Vector Integer Move Instructions

```asm
vmv.v.v
vmv.v.x
vmv.v.i
```

`vmv` 是 unmasked move/splat。`vmv.v.v` 从 vector 复制，`vmv.v.x` 将标量 `x` register 广播到 active 元素，`vmv.v.i` 将 immediate 广播到 active 元素。

# 12. Vector Fixed-Point Arithmetic Instructions

fixed-point 指令使用 `vxrm` 指定的 rounding mode，并在饱和发生时设置 `vxsat`。它们支持 DSP 常见的 saturating add/sub、averaging add/sub、fractional multiply、scaling shift 与 clip。

## 12.1. Vector Single-Width Saturating Add and Subtract

```asm
vsaddu.vv/vx/vi
vsadd.vv/vx/vi
vssubu.vv/vx
vssub.vv/vx
```

无符号形式饱和到 `[0, 2^SEW-1]`，有符号形式饱和到 `[-2^(SEW-1), 2^(SEW-1)-1]`。若结果饱和，设置 `vxsat`。

## 12.2. Vector Single-Width Averaging Add and Subtract

```asm
vaaddu.vv/vx
vaadd.vv/vx
vasubu.vv/vx
vasub.vv/vx
```

averaging add/sub 计算加法或减法后右移 1 bit，并按 `vxrm` 舍入。无符号和有符号形式分别解释输入。

## 12.3. Vector Single-Width Fractional Multiply with Rounding and Saturation

```asm
vsmul.vv/vx
```

`vsmul` 执行 signed fractional multiply，产生按 `vxrm` 舍入并饱和的 single-width 结果。若发生饱和则设置 `vxsat`。

## 12.4. Vector Single-Width Scaling Shift Instructions

```asm
vssrl.vv/vx/vi
vssra.vv/vx/vi
```

scaling shift right 在右移时使用 `vxrm` 舍入。`vssrl` 为逻辑右移，`vssra` 为算术右移。

## 12.5. Vector Narrowing Fixed-Point Clip Instructions

```asm
vnclipu.wv/wx/wi
vnclip.wv/wx/wi
```

`vnclipu` 和 `vnclip` 将 double-width 源右移、按 `vxrm` 舍入，并饱和缩窄到 single-width destination。无符号形式饱和到无符号范围，有符号形式饱和到有符号范围。饱和时设置 `vxsat`。

# 13. Vector Floating-Point Instructions

vector floating-point 指令依赖相应标量 floating-point 扩展提供的格式、舍入模式和异常标志。active 元素按 IEEE 754 与 RISC-V 浮点语义执行。mask-off 与 tail 元素按 vector 策略处理。

## 13.1. Vector Floating-Point Exception Flags

vector floating-point 指令产生的异常标志累计到标量 floating-point accrued exception flags 中。任何 active 元素产生的 invalid、divide-by-zero、overflow、underflow、inexact 等标志都会被记录。inactive 与 tail 元素不应产生浮点异常。

## 13.2. Vector Single-Width Floating-Point Add/Subtract Instructions

```asm
vfadd.vv/vf
vfsub.vv/vf
vfrsub.vf
```

这些指令执行 single-width 浮点加减。`vfrsub.vf` 计算 scalar 减 vector 元素。

## 13.3. Vector Widening Floating-Point Add/Subtract Instructions

```asm
vfwadd.vv/vf
vfwsub.vv/vf
vfwadd.wv/wf
vfwsub.wv/wf
```

widening 形式把较窄输入扩展并产生双倍宽度结果。`.w` 形式将 double-width accumulator 与 single-width 输入相加或相减。

## 13.4. Vector Single-Width Floating-Point Multiply/Divide Instructions

```asm
vfmul.vv/vf
vfdiv.vv/vf
vfrdiv.vf
```

`vfmul` 执行乘法，`vfdiv` 计算 vector 除以 vector/scalar，`vfrdiv.vf` 计算 scalar 除以 vector 元素。

## 13.5. Vector Widening Floating-Point Multiply

```asm
vfwmul.vv/vf
```

输入按 single-width 读取，结果为 double-width 浮点乘积。

## 13.6. Vector Single-Width Floating-Point Fused Multiply-Add Instructions

```asm
vfmacc.vv/vf
vfnmacc.vv/vf
vfmsac.vv/vf
vfnmsac.vv/vf
vfmadd.vv/vf
vfnmadd.vv/vf
vfmsub.vv/vf
vfnmsub.vv/vf
```

这些指令执行 fused multiply-add/subtract，只有一次最终舍入。`n` 后缀表示取负组合，`acc/add/sub` 形式决定 accumulator 与乘积的排列。

## 13.7. Vector Widening Floating-Point Fused Multiply-Add Instructions

```asm
vfwmacc.vv/vf
vfwnmacc.vv/vf
vfwmsac.vv/vf
vfwnmsac.vv/vf
```

这些指令把 single-width 输入相乘，并把 double-width 乘积累加到 double-width destination。

## 13.8. Vector Floating-Point Square-Root Instruction

```asm
vfsqrt.v
```

`vfsqrt.v` 对 active 元素计算平方根，并按当前 floating-point rounding mode 舍入。

## 13.9. Vector Floating-Point Reciprocal Square-Root Estimate Instruction

```asm
vfrsqrt7.v
```

`vfrsqrt7.v` 产生 `1/sqrt(x)` 的近似估计，精度约为 7 bit，用于后续 Newton-Raphson 迭代。

## 13.10. Vector Floating-Point Reciprocal Estimate Instruction

```asm
vfrec7.v
```

`vfrec7.v` 产生 `1/x` 的近似估计，精度约为 7 bit。

## 13.11. Vector Floating-Point MIN/MAX Instructions

```asm
vfmin.vv/vf
vfmax.vv/vf
```

这些指令按 RISC-V 浮点 min/max 语义处理 NaN、零符号和异常标志。

## 13.12. Vector Floating-Point Sign-Injection Instructions

```asm
vfsgnj.vv/vf
vfsgnjn.vv/vf
vfsgnjx.vv/vf
```

这些指令把一个源的数值部分与另一个源的符号、反符号或异或符号组合。

## 13.13. Vector Floating-Point Compare Instructions

```asm
vmfeq.vv/vf
vmfne.vv/vf
vmflt.vv/vf
vmfle.vv/vf
vmfgt.vf
vmfge.vf
```

比较结果写入 mask。ordered/unordered NaN 行为和 invalid exception 遵循 RISC-V 浮点比较语义。

## 13.14. Vector Floating-Point Classify Instruction

```asm
vfclass.v
```

`vfclass.v` 对每个 active 浮点元素生成与标量 `fclass` 相同类别 bitmask。

## 13.15. Vector Floating-Point Merge Instruction

```asm
vfmerge.vfm
```

`vfmerge` 根据 mask 在 vector 源和 floating-point scalar 源之间选择元素。

## 13.16. Vector Floating-Point Move Instruction

```asm
vfmv.v.f
```

`vfmv.v.f` 将 floating-point scalar 广播到 active vector 元素。

## 13.17. Single-Width Floating-Point/Integer Type-Convert Instructions

```asm
vfcvt.xu.f.v
vfcvt.x.f.v
vfcvt.f.xu.v
vfcvt.f.x.v
vfcvt.rtz.xu.f.v
vfcvt.rtz.x.f.v
```

这些指令在 single-width 浮点和整数之间转换。`xu` 为无符号整数，`x` 为有符号整数，`rtz` 使用 round-towards-zero。

## 13.18. Widening Floating-Point/Integer Type-Convert Instructions

```asm
vfwcvt.xu.f.v
vfwcvt.x.f.v
vfwcvt.f.xu.v
vfwcvt.f.x.v
vfwcvt.f.f.v
vfwcvt.rtz.xu.f.v
vfwcvt.rtz.x.f.v
```

widening convert 产生 double-width destination，包括浮点-整数转换和窄浮点到宽浮点转换。

## 13.19. Narrowing Floating-Point/Integer Type-Convert Instructions

```asm
vfncvt.xu.f.w
vfncvt.x.f.w
vfncvt.f.xu.w
vfncvt.f.x.w
vfncvt.f.f.w
vfncvt.rod.f.f.w
vfncvt.rtz.xu.f.w
vfncvt.rtz.x.f.w
```

narrowing convert 从 double-width 源产生 single-width destination。`rod` 表示 round-to-odd，用于多步精度缩窄时保留粘滞信息。
