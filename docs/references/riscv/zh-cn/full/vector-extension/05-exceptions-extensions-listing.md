# 17. Exception Handling

vector 指令可能在某个元素处产生同步异常，也可能被异步中断打断。`vstart` CSR 用于记录可恢复 trap 后应继续执行的元素索引。

## 17.1. Precise vector traps

precise vector trap 满足：

1. trapping vector instruction 之前的所有指令已经提交结果。
2. trapping vector instruction 之后的任何指令都没有改变架构状态。
3. trapping vector instruction 内部，影响 `vstart` CSR 中索引之前结果元素的操作已经提交结果。
4. trapping vector instruction 内部，影响 `vstart` CSR 中索引及其之后元素的操作没有改变架构状态。

在 precise trap 中，trap handler 可处理异常原因，然后从相同 PC 重新执行 vector 指令；由于 `vstart` 指向出错或被中断的元素，已经完成的较早元素不会重复执行。正常完成后，指令把 `vstart` 清零。

## 17.2. Imprecise vector traps

imprecise vector trap 不保证以上全部精确属性。它可用于某些高性能实现，特别是长 vector 或 memory 操作。imprecise trap 可能要求软件或执行环境终止进程、回滚更大范围状态，或使用平台特定机制恢复。

## 17.3. Selectable precise/imprecise traps

某些系统可以提供可选择的 precise 或 imprecise trap 模式。高可靠或调试场景可选择 precise trap；高性能计算场景可能接受 imprecise trap 以减少硬件代价。

## 17.4. Swappable traps

swappable trap 模式用于支持在 trap 发生时将线程迁移、换出或重新调度。因为不同 hart 可能支持不同 `vstart` 位置，运行时必须确保迁移后的 hart 能从该 `vstart` 继续，或者仿真直到受支持位置。

# 18. Standard Vector Extensions

标准 vector extension 被组织为最小 vector length 扩展 `Zvl*`、嵌入式 processor vector 扩展 `Zve*`，以及应用 processor 的完整 `V` 扩展。这种分解允许软件表达对向量长度、元素宽度、整数和浮点能力的需求。

## 18.1. `Zvl*`: Minimum Vector Length Standard Extensions

`Zvl*b` 扩展指定实现支持的最小 `VLEN`。例如 `Zvl32b` 表示至少 32 bit vector register，`Zvl64b` 至少 64 bit，依此类推。更大的 `Zvl*` 隐含较小的最小长度扩展。软件可用这些扩展约束编译目标所需的最小 vector length。

## 18.2. `Zve*`: Vector Extensions for Embedded Processors

`Zve*` 子集面向嵌入式 processor，按支持的最大元素宽度和浮点能力划分。整数子集包括如 `Zve32x`、`Zve64x`；带浮点能力的子集包括如 `Zve32f`、`Zve64f`、`Zve64d`。这些子集支持 vector 配置、load/store、整数算术、mask 和 permutation 的相应部分，并按名称约束 `ELEN`、`SEW` 与浮点元素支持。

## 18.3. `V`: Vector Extension for Application Processors

完整 `V` extension 面向 application processor，包含标准 vector 指令集合，并要求配合足够的 `Zvl*` 最小向量长度能力。它提供整数、定点、浮点、reduction、mask、permutation、segment load/store、fault-only-first 等完整能力，是通用软件和编译器主要目标。

# 19. Vector Instruction Listing

本章列出 `OP-V` 编码空间中的 vector 指令。下表按类别保留源规范中的指令名和主要编码分组。

## Integer `OPIVV`/`OPIVX`/`OPIVI`

| `funct6` | 指令 |
|---|---|
| `000000` | `vadd` |
| `000010` | `vsub` |
| `000011` | `vrsub` |
| `000100` | `vminu` |
| `000101` | `vmin` |
| `000110` | `vmaxu` |
| `000111` | `vmax` |
| `001001` | `vand` |
| `001010` | `vor` |
| `001011` | `vxor` |
| `001100` | `vrgather` |
| `001110` | `vslideup` |
| `001111` | `vslidedown` |
| `010000` | `vadc` |
| `010001` | `vmadc` |
| `010010` | `vsbc` |
| `010011` | `vmsbc` |
| `010111` | `vmerge`/`vmv` |
| `011000` | `vmseq` |
| `011001` | `vmsne` |
| `011010` | `vmsltu` |
| `011011` | `vmslt` |
| `011100` | `vmsleu` |
| `011101` | `vmsle` |
| `011110` | `vmsgtu` |
| `011111` | `vmsgt` |
| `100000` | `vsaddu` |
| `100001` | `vsadd` |
| `100010` | `vssubu` |
| `100011` | `vssub` |
| `100101` | `vsll` |
| `100111` | `vsmul`/`vmv<nr>r` |
| `101000` | `vsrl` |
| `101001` | `vsra` |
| `101010` | `vssrl` |
| `101011` | `vssra` |
| `101100` | `vnsrl` |
| `101101` | `vnsra` |
| `101110` | `vnclipu` |
| `101111` | `vnclip` |

## Integer/Mask `OPMVV`/`OPMVX`

| `funct6` | 指令 |
|---|---|
| `000000` | `vredsum` |
| `000001` | `vredand` |
| `000010` | `vredor` |
| `000011` | `vredxor` |
| `000100` | `vredminu` |
| `000101` | `vredmin` |
| `000110` | `vredmaxu` |
| `000111` | `vredmax` |
| `001000` | `vaaddu` |
| `001001` | `vaadd` |
| `001010` | `vasubu` |
| `001011` | `vasub` |
| `001110` | `vslide1up` |
| `001111` | `vslide1down` |
| `010000` | `VWXUNARY0`/`VRXUNARY0` |
| `010010` | `VXUNARY0` |
| `010100` | `VMUNARY0` |
| `010111` | `vcompress` |
| `011000` | `vmandnot` |
| `011001` | `vmand` |
| `011010` | `vmor` |
| `011011` | `vmxor` |
| `011100` | `vmornot` |
| `011101` | `vmnand` |
| `011110` | `vmnor` |
| `011111` | `vmxnor` |
| `100000` | `vdivu` |
| `100001` | `vdiv` |
| `100010` | `vremu` |
| `100011` | `vrem` |
| `100100` | `vmulhu` |
| `100101` | `vmul` |
| `100110` | `vmulhsu` |
| `100111` | `vmulh` |
| `101001` | `vmadd` |
| `101011` | `vnmsub` |
| `101101` | `vmacc` |
| `101111` | `vnmsac` |
| `110000` | `vwredsumu`/`vwaddu` |
| `110001` | `vwredsum`/`vwadd` |
| `110010` | `vwsubu` |
| `110011` | `vwsub` |
| `110100` | `vwaddu.w` |
| `110101` | `vwadd.w` |
| `110110` | `vwsubu.w` |
| `110111` | `vwsub.w` |
| `111000` | `vwmulu` |
| `111010` | `vwmulsu` |
| `111011` | `vwmul` |
| `111100` | `vwmaccu` |
| `111101` | `vwmacc` |
| `111110` | `vwmaccus` |
| `111111` | `vwmaccsu` |

## Floating-Point `OPFVV`/`OPFVF`

| `funct6` | 指令 |
|---|---|
| `000000` | `vfadd` |
| `000001` | `vfredusum` |
| `000010` | `vfsub` |
| `000011` | `vfredosum` |
| `000100` | `vfmin` |
| `000101` | `vfredmin` |
| `000110` | `vfmax` |
| `000111` | `vfredmax` |
| `001000` | `vfsgnj` |
| `001001` | `vfsgnjn` |
| `001010` | `vfsgnjx` |
| `001110` | `vfslide1up` |
| `001111` | `vfslide1down` |
| `010000` | `VWFUNARY0`/`VRFUNARY0` |
| `010010` | `VFUNARY0` |
| `010011` | `VFUNARY1` |
| `010111` | `vfmerge`/`vfmv` |
| `011000` | `vmfeq` |
| `011001` | `vmfle` |
| `011011` | `vmflt` |
| `011100` | `vmfne` |
| `011101` | `vmfgt` |
| `011111` | `vmfge` |
| `100000` | `vfdiv` |
| `100001` | `vfrdiv` |
| `100100` | `vfmul` |
| `100111` | `vfrsub` |
| `101000` | `vfmadd` |
| `101001` | `vfnmadd` |
| `101010` | `vfmsub` |
| `101011` | `vfnmsub` |
| `101100` | `vfmacc` |
| `101101` | `vfnmacc` |
| `101110` | `vfmsac` |
| `101111` | `vfnmsac` |
| `110000` | `vfwadd` |
| `110001` | `vfwredusum` |
| `110010` | `vfwsub` |
| `110011` | `vfwredosum` |
| `110100` | `vfwadd.w` |
| `110110` | `vfwsub.w` |
| `111000` | `vfwmul` |
| `111100` | `vfwmacc` |
| `111101` | `vfwnmacc` |
| `111110` | `vfwmsac` |
| `111111` | `vfwnmsac` |

## Unary encoding spaces

表 20. `VRXUNARY0` encoding space

| `vs2` | name |
|---|---|
| `00000` | `vmv.s.x` |

表 21. `VWXUNARY0` encoding space

| `vs1` | name |
|---|---|
| `00000` | `vmv.x.s` |
| `10000` | `vpopc` |
| `10001` | `vfirst` |

表 22. `VXUNARY0` encoding space

| `vs1` | name |
|---|---|
| `00010` | `vzext.vf8` |
| `00011` | `vsext.vf8` |
| `00100` | `vzext.vf4` |
| `00101` | `vsext.vf4` |
| `00110` | `vzext.vf2` |
| `00111` | `vsext.vf2` |

表 23. `VRFUNARY0` encoding space

| `vs2` | name |
|---|---|
| `00000` | `vfmv.s.f` |

表 24. `VWFUNARY0` encoding space

| `vs1` | name |
|---|---|
| `00000` | `vfmv.f.s` |

表 25. `VFUNARY0` encoding space

| `vs1` | name |
|---|---|
| `00000` | `vfcvt.xu.f.v` |
| `00001` | `vfcvt.x.f.v` |
| `00010` | `vfcvt.f.xu.v` |
| `00011` | `vfcvt.f.x.v` |
| `00110` | `vfcvt.rtz.xu.f.v` |
| `00111` | `vfcvt.rtz.x.f.v` |
| `01000` | `vfwcvt.xu.f.v` |
| `01001` | `vfwcvt.x.f.v` |
| `01010` | `vfwcvt.f.xu.v` |
| `01011` | `vfwcvt.f.x.v` |
| `01100` | `vfwcvt.f.f.v` |
| `01110` | `vfwcvt.rtz.xu.f.v` |
| `01111` | `vfwcvt.rtz.x.f.v` |
| `10000` | `vfncvt.xu.f.w` |
| `10001` | `vfncvt.x.f.w` |
| `10010` | `vfncvt.f.xu.w` |
| `10011` | `vfncvt.f.x.w` |
| `10100` | `vfncvt.f.f.w` |
| `10101` | `vfncvt.rod.f.f.w` |
| `10110` | `vfncvt.rtz.xu.f.w` |
| `10111` | `vfncvt.rtz.x.f.w` |

表 26. `VFUNARY1` encoding space

| `vs1` | name |
|---|---|
| `00000` | `vfsqrt.v` |
| `00100` | `vfrsqrt7.v` |
| `00101` | `vfrec7.v` |
| `10000` | `vfclass.v` |

表 27. `VMUNARY0` encoding space

| `vs1` | name |
|---|---|
| `00001` | `vmsbf` |
| `00010` | `vmsof` |
| `00011` | `vmsif` |
| `10000` | `viota` |
| `10001` | `vid` |
