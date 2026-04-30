# RISC-V Vector 扩展中文全文译文

源文档：`RISC-V_Vector_ISA-extensions_V1.0.pdf`

本文是 RISC-V Vector 扩展 1.0 的中文译文稿，用于离线阅读、设计讨论和实现对齐。源 PDF 不属于本项目原创内容，版权、商标和许可归原发布方及贡献者所有。译文保留指令名、寄存器名、CSR 名、字段名、扩展名和必要英文术语；若译文与源 PDF 存在差异，以源 PDF 为准。

## 1. 引言

Vector 扩展定义一套可变向量长度的数据并行指令。它让软件用同一套二进制在不同 VLEN 的实现上运行：程序不把向量寄存器长度写死，而是通过配置指令请求当前循环迭代可处理的元素数量，硬件返回实际 `vl`。这种模型适合数组、矩阵、信号处理、密码、机器学习和多媒体等吞吐型代码，也便于实现从小型嵌入式到高性能应用处理器的范围化设计。

Vector 1.0 被视为公开评审冻结版本，包含当前冻结的向量指令集合。规范把标准 Vector 能力拆成 `Zve*` 嵌入式子集、`Zvl*` 最小向量长度扩展和完整 `V` 应用处理器扩展，便于软件按能力发现和编译目标选择。

## 2. 实现定义常量参数

每个支持 Vector 扩展的 hart 至少定义两个常量：

| 参数 | 含义 | 约束 |
|---|---|---|
| `ELEN` | 任一向量操作可产生或消费的最大元素位宽 | `ELEN >= 8`，且为 2 的幂 |
| `VLEN` | 单个向量寄存器的位数 | `VLEN >= ELEN`，为 2 的幂，且不超过规范给定上限 |

标准扩展和架构 profile 可以进一步约束 `ELEN` 与 `VLEN`。当前 Vector 1.0 不支持一个元素跨多个向量寄存器保存，因此 `ELEN` 不大于 `VLEN`。同一线程若含有活跃向量状态，通常不能在 `VLEN` 或 `ELEN` 不同的 hart 之间透明迁移，除非执行环境保存、转换或重新建立状态。

## 3. Vector 程序员模型

Vector 扩展在基础标量 ISA 之外增加 32 个架构向量寄存器 `v0`-`v31`，以及若干非特权 CSR。每个向量寄存器有固定 `VLEN` 位状态。程序通过 `vtype` 设置元素宽度和寄存器组倍率，通过 `vl` 得知当前活动元素数，通过 mask 和 tail 策略控制未生效元素的写回行为。

### 3.1 Vector CSR

| 地址 | 权限 | 名称 | 含义 |
|---|---|---|---|
| `0x008` | `URW` | `vstart` | 向量指令重启起始元素索引 |
| `0x009` | `URW` | `vxsat` | 定点饱和标志 |
| `0x00A` | `URW` | `vxrm` | 定点舍入模式 |
| `0x00F` | `URW` | `vcsr` | 向量控制与状态寄存器 |
| `0xC20` | `URO` | `vl` | 当前向量长度 |
| `0xC21` | `URO` | `vtype` | 当前向量数据类型与策略 |
| `0xC22` | `URO` | `vlenb` | `VLEN/8`，向量寄存器字节数 |

`vcsr` 汇总 `vxrm` 和 `vxsat` 等状态。`vlenb` 让软件不用编码实现常量即可得知向量寄存器字节长度。

### 3.2 向量上下文状态

特权状态中增加向量上下文字段 `VS`，位于 `mstatus`，并在存在 Supervisor 或虚拟化相关状态时映射到 `sstatus`/`vsstatus`。`VS` 类似浮点 `FS`，可取 Off、Initial、Clean、Dirty。若 `VS=Off`，执行向量指令或访问向量 CSR 会产生 illegal-instruction exception。执行会改变向量状态的指令后，实现应把 `VS` 置为 Dirty；实现也可保守地提前置 Dirty。操作系统用该字段减少上下文切换时不必要的向量状态保存。

### 3.3 `vtype`

`vtype` 是 XLEN 位只读 CSR，只能由 `vsetvli`、`vsetivli` 或 `vsetvl` 更新。它描述当前向量寄存器文件如何解释，以及结果中 mask-off 元素和 tail 元素如何处理。

| 字段 | 含义 |
|---|---|
| `vill` | 非法 `vtype` 标志；置位表示当前配置不被支持 |
| `vma` | vector mask agnostic 策略位 |
| `vta` | vector tail agnostic 策略位 |
| `vsew[2:0]` | selected element width，当前元素宽度 |
| `vlmul[2:0]` | vector register group multiplier，寄存器组倍率 |

`SEW = 8 << vsew`。`LMUL` 可为 1、2、4、8，也可为分数值 `mf2`、`mf4`、`mf8`，具体取决于编码和实现支持。若请求了不支持的 `SEW`、`LMUL` 或组合，硬件设置 `vill=1`，并通常把 `vl` 置 0。软件应检查 `vill` 或根据标准扩展约束避免非法组合。

### 3.4 `vl`、AVL 和 VLMAX

`vl` 是当前向量指令活动元素数量。`VLMAX = LMUL * VLEN / SEW`，表示当前 `vtype` 下最多可处理的元素数。配置指令根据应用向量长度 AVL 和硬件能力设置 `vl`。典型 stripmining 循环把剩余元素数传给 `vsetvli`，每次处理返回的 `vl` 个元素，然后减少剩余计数。

规范允许实现对 `vl` 选择有一定自由，但必须满足可移植循环所需约束：当 AVL 小于等于 VLMAX 时，`vl` 应不超过 AVL；当 AVL 大于 VLMAX 时，`vl` 可选择一个不超过 VLMAX 的正值，通常为 VLMAX。这样软件无需知道实际 VLEN。

### 3.5 `vstart`

`vstart` 保存下一条向量指令应从哪个元素索引开始执行。正常执行前通常为 0。若向量指令中途产生可重启异常，trap 处理程序可通过 `vstart` 得知已完成元素数量，修复原因后从该元素重新执行。大多数软件不直接写 `vstart`；异常返回路径和精确 trap 支持需要正确维护它。

### 3.6 `vxrm`、`vxsat` 和 `vcsr`

`vxrm` 控制定点舍入，常见模式包括向最近偶数舍入、向零舍入、向下取整形式的舍入增量等。`vxsat` 是定点饱和标志，饱和算术发生截断/饱和时置位。`vcsr` 将 `vxrm` 和 `vxsat` 放在一个 CSR 中，便于保存和恢复。

### 3.7 复位状态

复位后向量状态可处于实现定义状态，软件在使用 Vector 前必须显式配置 `vtype` 和 `vl`，并根据特权状态启用向量上下文。不能假设复位后向量寄存器、`vstart`、`vxrm` 或 `vxsat` 为某个特定应用值。

## 4. 元素到寄存器的映射

向量寄存器按元素宽度 `SEW` 切分为元素槽。`LMUL=1` 时，一个向量寄存器组就是单个 `v` 寄存器。`LMUL>1` 时，多个连续向量寄存器组成一个寄存器组，例如 `LMUL=4` 时 `v8`、`v9`、`v10`、`v11` 组成一组。寄存器组起始编号必须满足对齐要求，否则指令编码保留或非法。

`LMUL<1` 时，一个物理向量寄存器可容纳多个较小逻辑向量组，便于窄元素计算减少寄存器压力。分数 LMUL 的合法性受 `SEW`、`ELEN` 和实现支持限制。

混合宽度操作通过有效元素倍率 `EMUL` 描述源/目的寄存器组大小。拓宽操作的目的 `EMUL` 通常大于源 `LMUL`，缩窄操作相反。实现和汇编器必须检查寄存器组是否重叠、是否对齐、是否超过 `v31`。

mask 寄存器固定使用 `v0`，每个元素使用 1 bit mask。mask 元素布局与 `SEW` 无关，即元素 i 的 mask 位控制元素 i。

## 5. 向量指令格式和元素状态

向量指令有向量-向量、向量-标量、向量-立即数、mask 形式等。操作数包括目的向量寄存器组 `vd`、源向量寄存器组 `vs1`/`vs2`、标量寄存器 `rs1`、立即数和 mask 控制位 `vm`。当 `vm=0` 时，使用 `v0` 作为 mask；当 `vm=1` 时，指令不受 mask 屏蔽。

元素可分为：

| 区域 | 定义 |
|---|---|
| prestart | 索引小于 `vstart` 的元素，本次执行不改动 |
| active | `vstart <= i < vl` 且 mask 使能的元素 |
| inactive | `vstart <= i < vl` 但 mask 关闭的元素 |
| body | `vstart <= i < vl` 的执行范围 |
| tail | `i >= vl` 且小于 VLMAX 的元素 |

active 元素按指令语义写结果。inactive 和 tail 元素如何处理由 `vma` 和 `vta` 控制。

## 6. Tail 和 mask 策略

Vector 1.0 要求汇编中显式写出 tail 和 mask 策略，避免旧默认值造成可移植性问题。

| 策略 | 含义 |
|---|---|
| tail undisturbed (`tu`) | tail 元素保持原目的寄存器值 |
| tail agnostic (`ta`) | tail 元素可保持原值，也可写为全 1，软件不得依赖 |
| mask undisturbed (`mu`) | inactive 元素保持原目的寄存器值 |
| mask agnostic (`ma`) | inactive 元素可保持原值，也可写为全 1，软件不得依赖 |

agnostic 策略允许乱序或重命名实现避免读取旧目的寄存器，减少硬件代价。undisturbed 策略适合需要保留未处理元素的代码。mask 结果自身通常有特殊 tail 处理规则，软件不应读取超出 `vl` 的 mask tail 值作为语义数据。

## 7. 配置指令

`vsetvli`、`vsetivli` 和 `vsetvl` 设置 `vtype` 与 `vl`。

| 指令 | 输入 | 用途 |
|---|---|---|
| `vsetvli rd, rs1, vtypei` | AVL 来自 `rs1`，`vtype` 来自立即数 | 常见动态 stripmining |
| `vsetivli rd, uimm, vtypei` | AVL 为小立即数 | 短固定长度配置 |
| `vsetvl rd, rs1, rs2` | AVL 来自 `rs1`，`vtype` 来自 `rs2` | 恢复先前保存的 `vtype` |

执行后，`vl` 写入 CSR，并把新 `vl` 写入 `rd`。若 `rd=x0` 可忽略返回值。AVL 有几种特殊编码：普通寄存器值表示剩余元素数；某些 `rd/rs1` 组合可请求保持已有 `vl` 或设置为最大值，供上下文恢复和固定 VLMAX 代码使用。

`vtypei` 包含 `SEW`、`LMUL`、`ta/tu`、`ma/mu`。汇编常写成：

```asm
vsetvli t0, a0, e32, m4, ta, ma
```

它请求 32 位元素、`LMUL=4`、tail agnostic、mask agnostic，并把实际 `vl` 写入 `t0`。

## 8. 向量加载与存储

向量访存按元素生成地址并执行加载/存储。所有访存受当前 `vl`、`vstart` 和 mask 控制。异常时，已完成元素、`vstart` 和目标寄存器状态必须满足可重启规则。

### 8.1 寻址模式

| 模式 | 地址计算 | 用途 |
|---|---|---|
| unit-stride | `base + i * element_width` | 连续数组 |
| strided | `base + i * stride` | 固定步长访问 |
| indexed unordered | `base + index[i]`，元素顺序可重排 | gather/scatter，顺序不重要 |
| indexed ordered | `base + index[i]`，按元素顺序约束 | 需要可观察顺序的 I/O 或重叠访问 |
| segment | 每个元素位置加载/存储多个字段 | AoS 结构体数组 |
| whole register | 按寄存器整体搬运 | 上下文保存、快速复制 |

unit-stride 包括普通向量加载/存储、mask 加载/存储、fault-only-first 加载和 whole-register 形式。strided 通过标量寄存器给出 stride；若 stride 为 0，多个元素可访问同一地址，具体顺序按模式定义。indexed 通过向量寄存器提供偏移，偏移宽度由指令编码指定。

### 8.2 宽度和扩展

向量加载/存储可指定元素内存宽度 EEW。加载可进行符号扩展或零扩展，也可按相同宽度直接载入。存储写出源元素低 EEW 位。若 EEW 与当前 `SEW` 不同，需要通过编码和 `EMUL` 调整寄存器组使用。

### 8.3 Fault-only-first

fault-only-first unit-stride 加载用于字符串或探测式循环。若第一个元素发生异常，正常报告异常；若后续元素发生异常，指令可缩短 `vl`，只报告已成功加载的前缀而不陷入。这样软件可以安全处理未知长度数据，同时避免越界页故障中断循环。

### 8.4 Segment 访存

segment 指令每个元素位置加载或存储多个字段，例如结构体数组中的 `(x,y,z)`。`nf` 字段指定字段数量。目的或源寄存器组按字段分布，元素 i 的各字段来自连续内存位置。segment 指令可与 unit-stride、strided 或 indexed 模式结合。

### 8.5 对齐和一致性

向量访存的对齐要求由元素宽度、平台内存属性和执行环境决定。自然对齐通常最高效；非对齐访问可能被硬件支持，也可能产生异常。向量内存一致性遵循 RISC-V 内存模型：单条向量指令内部的元素访问在普通内存中不一定表现为逐元素程序顺序，除非使用 ordered indexed 或其他同步约束。访问设备或有副作用区域时，软件应使用有序形式和 `FENCE`。

## 9. 向量算术指令格式

向量算术指令按操作数形态分为：

| 形态 | 示例含义 |
|---|---|
| `vv` | 向量与向量逐元素 |
| `vx` | 向量与标量整数寄存器 |
| `vi` | 向量与立即数 |
| `vf` | 向量与标量浮点寄存器 |
| mask-producing | 产生 mask 结果 |
| widening | 源较窄，目的较宽 |
| narrowing | 源较宽，目的较窄 |

大多数算术指令只处理 active 元素。inactive 和 tail 按策略处理。拓宽指令的目的 `SEW` 是源的两倍，缩窄指令把较宽源裁剪到较窄目的。

## 10. 向量整数算术

整数指令覆盖加减、反向减、位逻辑、移位、比较、最小/最大、乘除、乘加、合并和移动。

| 类别 | 代表指令 | 语义 |
|---|---|---|
| 单宽加减 | `vadd`、`vsub`、`vrsub` | 逐元素加减，结果按 `SEW` 截断 |
| 拓宽加减 | `vwaddu`、`vwadd`、`vwsubu`、`vwsub` | 源扩展后产生 2*SEW 结果 |
| 整数扩展 | `vzext`、`vsext` | 零扩展或符号扩展较窄元素 |
| 带进位/借位 | `vadc`、`vmadc`、`vsbc`、`vmsbc` | 与 mask 位配合实现多精度算术 |
| 位逻辑 | `vand`、`vor`、`vxor` | 逐元素按位逻辑 |
| 移位 | `vsll`、`vsrl`、`vsra`、`vnsrl`、`vnsra` | 左移、逻辑右移、算术右移、缩窄右移 |
| 比较 | `vmseq`、`vmsne`、`vmslt`、`vmsle`、`vmsgt` | 产生 mask |
| min/max | `vminu`、`vmin`、`vmaxu`、`vmax` | 无符号/有符号最小最大 |
| 乘除 | `vmul`、`vmulh*`、`vdiv*`、`vrem*` | 逐元素乘法高低位、除法和余数 |
| 乘加 | `vmacc`、`vnmsac`、`vmadd`、`vnmsub` | 单宽乘加变体 |
| 拓宽乘加 | `vwmacc*` | 窄源乘法累加到宽目的 |
| 合并/移动 | `vmerge`、`vmv` | 按 mask 合并或复制值 |

除法和余数沿用标量整数除法边界规则：除以零和有符号溢出不触发异常，而产生规定结果。比较指令写入 mask 寄存器，结果元素为单 bit。

## 11. 向量定点算术

定点指令面向 DSP 风格整数运算。它们使用 `vxrm` 控制舍入，用 `vxsat` 记录饱和。

| 类别 | 代表指令 | 语义 |
|---|---|---|
| 饱和加减 | `vsaddu`、`vsadd`、`vssubu`、`vssub` | 溢出时钳位到目标范围 |
| 平均加减 | `vaaddu`、`vaadd`、`vasubu`、`vasub` | 加/减后按舍入模式缩放 |
| 小数乘 | `vsmul` | 高位小数乘法，带舍入和饱和 |
| 缩放移位 | `vssrl`、`vssra` | 右移并按 `vxrm` 舍入 |
| 缩窄裁剪 | `vnclipu`、`vnclip` | 宽源缩窄到窄目的，带舍入/饱和 |

发生饱和时，`vxsat` 置位并保持，直到软件清除。定点代码在一段计算后可检查 `vxsat` 判断是否发生过饱和。

## 12. 向量浮点指令

浮点向量指令依赖相应标量浮点扩展和浮点寄存器状态。它们按元素执行 IEEE 754 风格运算，并把异常标志累计到浮点状态中。

| 类别 | 代表指令 |
|---|---|
| 加减 | `vfadd`、`vfsub`、`vfrsub` |
| 拓宽加减 | `vfwadd`、`vfwsub` |
| 乘除 | `vfmul`、`vfdiv`、`vfrdiv` |
| 拓宽乘 | `vfwmul` |
| 融合乘加 | `vfmacc`、`vfnmacc`、`vfmsac`、`vfnmsac`、`vfmadd`、`vfnmadd`、`vfmsub`、`vfnmsub` |
| 拓宽融合乘加 | `vfwmacc`、`vfwnmacc`、`vfwmsac`、`vfwnmsac` |
| 平方根/估计 | `vfsqrt`、`vfrsqrt7`、`vfrec7` |
| min/max | `vfmin`、`vfmax` |
| 符号注入 | `vfsgnj`、`vfsgnjn`、`vfsgnjx` |
| 比较 | `vmfeq`、`vmfne`、`vmflt`、`vmfle`、`vmfgt`、`vmfge` |
| 分类 | `vfclass` |
| 合并/移动 | `vfmerge`、`vfmv` |
| 类型转换 | `vfcvt`、`vfwcvt`、`vfncvt` |

浮点比较产生 mask。类型转换覆盖有符号/无符号整数与浮点之间的单宽、拓宽和缩窄转换。缩窄转换可使用当前舍入模式，并按浮点规范设置异常标志。

## 13. 归约操作

归约把向量多个元素合并为一个结果，初始值通常来自目的寄存器的元素 0 或指定源。整数归约包括求和、与、或、异或、最小/最大；拓宽整数归约把窄元素累加到宽结果。浮点归约包括有序和无序求和、最小/最大，拓宽浮点归约把窄浮点源累加到宽浮点结果。

| 类别 | 指令 |
|---|---|
| 整数单宽归约 | `vredsum`、`vredand`、`vredor`、`vredxor`、`vredminu`、`vredmin`、`vredmaxu`、`vredmax` |
| 整数拓宽归约 | `vwredsumu`、`vwredsum` |
| 浮点归约 | `vfredosum`、`vfredusum`、`vfredmin`、`vfredmax` |
| 浮点拓宽归约 | `vfwredosum`、`vfwredusum` |

有序浮点求和按元素顺序定义舍入路径，便于可重复结果；无序求和允许实现重排，性能更高但舍入结果可能不同。

## 14. Mask 指令

mask 指令操作 `v0` 或其他 mask 目的，按 bit 表示元素选择。

| 指令 | 作用 |
|---|---|
| `vmand`、`vmnand`、`vmandn` | mask 与及其取反组合 |
| `vmxor`、`vmxnor` | mask 异或/同或 |
| `vmor`、`vmnor`、`vmorn` | mask 或及其取反组合 |
| `vcpop.m` | 统计 active mask 中为 1 的 bit 数 |
| `vfirst.m` | 返回第一个置位 mask 元素索引，未找到返回 -1 |
| `vmsbf.m` | first 之前置位 |
| `vmsif.m` | first 之前并包含 first 置位 |
| `vmsof.m` | 仅 first 置位 |
| `viota.m` | 为每个元素生成此前置位 mask 数量 |
| `vid.v` | 生成元素索引 |

这些指令常用于压缩、条件执行、前缀计数、字符串扫描和 gather/scatter 前的索引构造。mask 指令自身也受 `vl` 约束，tail 区域不应被软件依赖。

## 15. 排列、slide、gather 和 compress

排列类指令在寄存器内部或寄存器之间重排元素。

| 类别 | 指令 | 语义 |
|---|---|---|
| 标量移动 | `vmv.x.s`、`vmv.s.x`、`vfmv.f.s`、`vfmv.s.f` | 向量元素 0 与标量寄存器之间移动 |
| slide | `vslideup`、`vslidedown`、`vslide1up`、`vslide1down` | 元素按偏移上移/下移，或插入一个标量 |
| gather | `vrgather`、`vrgatherei16` | 用索引选择源向量元素 |
| compress | `vcompress.vm` | 按 mask 把选中元素紧凑写入目的 |
| whole register move | `vmv<nr>r.v` | 移动一个或多个完整向量寄存器 |

`vcompress.vm` 的目的寄存器不能与源或 mask 非法重叠。它常与 `vcpop.m` 一起用于过滤数组。`vrgather` 对越界索引返回 0。slide 指令可用于构造窗口、移位队列和跨向量边界的数据对齐。

## 16. 异常处理与 restart

Vector 异常可以是精确、非精确、可选择精确/非精确或可交换形式。精确向量 trap 要求异常被报告到明确元素，且 `vstart` 指向需要重启的元素。处理程序修复异常原因后，可重新执行同一向量指令，从 `vstart` 开始继续。

非精确 trap 允许实现只报告某个较粗粒度状态，适合某些高性能机器，但软件恢复更困难。规范通过 `vstart`、prestart 元素不改动、active 元素顺序约束和 fault-only-first 规则，为可重启实现提供统一模型。

向量指令正常完成后，`vstart` 通常清零。若软件显式写入非零 `vstart`，只应在实现支持并符合指令约束的情况下使用；并非所有指令都要求支持任意非零 `vstart`。

## 17. 向量内存一致性模型

向量访存是单条指令产生多个元素级内存操作。对普通内存，元素操作可以在不破坏依赖和异常语义的前提下由实现重排。对有序 indexed 访存，元素访问顺序受到更强约束。mask 关闭或 tail 元素不执行内存访问。

Vector 扩展不替代 `FENCE`、原子或语言内存模型。跨 hart 同步仍需使用 RISC-V 内存模型规定的 acquire/release、AMO、LR/SC 或 `FENCE`。访问 I/O 或副作用区域时，应选择 ordered 形式并配合平台所需栅栏。

## 18. 标准 Vector 扩展集合

`Zvl*` 扩展声明最小 VLEN。例如某实现可通过 `Zvl128b` 表示至少 128 bit 向量寄存器。`Zve*` 面向嵌入式处理器，按整数和浮点能力拆分子集，例如仅整数向量、支持 32 位浮点或支持 64 位浮点等。完整 `V` 扩展面向应用处理器，包含较完整的整数、定点、浮点、访存、mask、归约和排列能力。

软件应根据 ISA 字符串、平台 profile 或运行时探测确定可用最小向量长度、元素宽度和浮点能力。编译器生成代码时需要匹配目标 `Zve*`/`V` 能力，避免使用目标不支持的 EEW、SEW、LMUL 或指令类别。

## 19. ABI 与调用约定

Vector 1.0 文档中的调用约定附录是非权威占位说明。原则上，ABI 必须规定向量寄存器是否跨调用保存、`vtype`/`vl`/`vstart`/`vcsr` 的调用边界状态、栈上保存格式、信号/异常上下文如何保存向量状态，以及不同 VLEN hart 之间线程迁移的限制。

常见系统策略是把向量寄存器视为调用者保存或在特定 ABI 变体中划分参数/返回值寄存器；操作系统通过 `VS` Dirty 状态延迟保存。由于向量状态大小随 VLEN 变化，ABI 和内核上下文格式需要能描述实际 `vlenb`。若线程在不同 VLEN 的 hart 间迁移，执行环境必须禁止、重新初始化或转换向量状态。

## 20. 编程示例模式

典型 stripmining 循环如下：

```asm
loop:
    vsetvli t0, a0, e32, m1, ta, ma
    vle32.v v0, (a1)
    vle32.v v1, (a2)
    vadd.vv v2, v0, v1
    vse32.v v2, (a3)
    slli t1, t0, 2
    add a1, a1, t1
    add a2, a2, t1
    add a3, a3, t1
    sub a0, a0, t0
    bnez a0, loop
```

这段代码不假设 VLEN。每轮 `vsetvli` 根据剩余元素数设置 `vl`，指针按实际处理元素数前进，最后一轮自然处理尾部。

## 21. 翻译完成状态

本文件已从入口/摘要稿改为 Vector 扩展中文正文译文稿，覆盖 Vector 总体模型、`VLEN`/`ELEN`、向量寄存器、`vtype`/`vl`/`vlenb`、`SEW`/`LMUL`、`vill`、`vsetvli`/`vsetivli`/`vsetvl`、mask 与 tail 策略、unit-stride/strided/indexed/segment 访存、整数/定点/浮点算术、归约、mask 指令、permutation/slide/compress、异常与 restart、向量内存一致性、标准 Vector 子集和 ABI/calling convention 相关内容。
