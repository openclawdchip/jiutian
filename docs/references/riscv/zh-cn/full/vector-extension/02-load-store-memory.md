# 7. Vector Loads and Stores

vector load/store 指令在 vector register group 与内存之间移动元素。它们覆盖 unit-stride、strided、indexed、segment、fault-only-first 和 whole-register 形式。指令名中的元素宽度，如 `vle8.v`、`vse32.v`，表示内存元素的 encoded element width (`EEW`)；实际寄存器分组由 `EEW`、当前 `SEW/LMUL` 和 `EMUL` 关系确定。

## 7.1. Vector Load/Store Instruction Encoding

vector load/store 使用与标量 load/store 类似的基址寄存器 `rs1`，并使用 vector register 字段指定 `vd` 或 `vs3`。store 使用 `vs3` 作为待写 vector 数据。`mop`、`lumop`、`sumop`、`nf`、`width` 等字段共同区分寻址模式、segment 字段数、whole-register 形式和 fault-only-first 形式。

`vm` bit 控制 mask。`vm=1` 表示 unmasked；`vm=0` 表示使用 `v0.t`。masked-off 元素不进行内存访问，因此不会产生该元素的内存异常，也不会对内存顺序产生访问。

## 7.2. Vector Load/Store Addressing Modes

标准寻址模式包括：

| 模式 | 含义 |
|---|---|
| unit-stride | 元素地址连续，地址为 `base + i * EEW/8` |
| strided | 元素地址为 `base + i * stride`，stride 来自 `rs2` |
| indexed-unordered | 偏移量来自 vector index，元素访问顺序不保证 |
| indexed-ordered | 偏移量来自 vector index，元素访问按元素顺序观察 |

indexed load/store 的 index 元素宽度由指令名决定，例如 `vluxei8.v` 使用 8 bit unsigned index，`vloxei32.v` 使用 ordered 32 bit index。effective address 由基址加零扩展 index 形成。

## 7.3. Vector Load/Store Width Encoding

load/store 宽度编码指定内存中每个元素的 `EEW`，包括 8、16、32、64 bit。若 `EEW` 与当前 `SEW` 不同，则形成 mixed-width 访存，使用对应 `EMUL = (EEW/SEW) * LMUL`。`EMUL` 必须位于合法范围，寄存器组必须满足对齐与编号约束。

## 7.4. Vector Unit-Stride Instructions

unit-stride load/store 是最常用形式：

```asm
vle8.v   vd, (rs1), vm
vle16.v  vd, (rs1), vm
vle32.v  vd, (rs1), vm
vle64.v  vd, (rs1), vm
vse8.v   vs3, (rs1), vm
vse16.v  vs3, (rs1), vm
vse32.v  vs3, (rs1), vm
vse64.v  vs3, (rs1), vm
```

load 将 active 元素从连续内存地址读入 destination vector register group；store 将 active 元素写入连续内存地址。inactive 元素不访问内存。load 的 inactive 与 tail destination 元素按 `vma/vta` 策略处理；store 对 inactive 与 tail 元素不写内存。

unit-stride mask load/store 使用 `vlm.v` 与 `vsm.v`，按 byte 访问 mask 数据，但 mask 语义仍是一元素一 bit。

## 7.5. Vector Strided Instructions

strided load/store 使用标量 stride：

```asm
vlse8.v   vd, (rs1), rs2, vm
vsse8.v   vs3, (rs1), rs2, vm
```

第 `i` 个元素地址为 `rs1 + i * rs2`。stride 可以为 0 或负值。若多个 active 元素映射到同一地址，load 的读取值和 store 的最终内存值按内存模型与指令定义约束处理；可移植程序不应依赖未排序冲突 store 的特定写入顺序。

## 7.6. Vector Indexed Instructions

indexed-unordered 指令：

```asm
vluxei8.v   vd, (rs1), vs2, vm
vsuxei8.v   vs3, (rs1), vs2, vm
```

indexed-ordered 指令：

```asm
vloxei8.v   vd, (rs1), vs2, vm
vsoxei8.v   vs3, (rs1), vs2, vm
```

`vs2` 提供每个元素的 byte offset。unordered 形式允许实现重排元素访问，适合无依赖 gather/scatter；ordered 形式按元素顺序提供更强观察顺序，适合内存映射 I/O 或具有地址冲突语义的代码。

## 7.7. Unit-stride Fault-Only-First Loads

fault-only-first load 在第一个元素发生异常时 trap；若后续元素发生异常，实现可以不 trap，而是缩短 `vl`，使软件能处理已经成功加载的前缀。这类指令用于向量化字符串或搜索循环，例如扫描直到页边界或终止字节。

```asm
vle8ff.v   vd, (rs1), vm
vle16ff.v  vd, (rs1), vm
vle32ff.v  vd, (rs1), vm
vle64ff.v  vd, (rs1), vm
```

如果元素 0 fault，则正常报告异常且不更新为成功前缀。若某个大于 0 的元素 fault，可将 `vl` 设置为 fault 元素之前成功加载的元素数。fault-only-first load 不应被用作探测任意地址合法性的通用机制；它是为了循环前缀处理而提供。

## 7.8. Vector Load/Store Segment Instructions

segment load/store 一次处理结构体数组中的多个字段。`nf` 字段指定字段数，指令名如 `vlseg2e32.v`、`vsseg4e16.v`。active 元素的第 `i` 个 segment 包含多个 field，分别写入或读取连续 vector register group。

segment 指令包括 unit-stride、strided、indexed 变体，也有 fault-only-first unit-stride segment load。寄存器编号必须有足够连续空间容纳全部 field，每个 field 的 `EMUL` 都必须合法。segment 形式可高效实现 AoS 与 SoA 之间的访问模式。

## 7.9. Vector Load/Store Whole Register Instructions

whole-register load/store 把一个或多个完整 vector register 作为字节序列搬入或搬出内存，不依赖当前 `vtype`。示例包括：

```asm
vl1re8.v  vd, (rs1)
vl2re8.v  vd, (rs1)
vl4re8.v  vd, (rs1)
vl8re8.v  vd, (rs1)
vs1r.v    vs3, (rs1)
vs2r.v    vs3, (rs1)
vs4r.v    vs3, (rs1)
vs8r.v    vs3, (rs1)
```

这些指令常用于保存和恢复 vector register state。由于它们不依赖 `vtype`，在 `vtype.vill` 置位时仍可用于上下文管理。

# 8. Vector Memory Alignment Constraints

vector 内存元素的自然对齐约束由实现与执行环境定义。若某个 active 元素访问的地址未满足实现要求，可能产生 address-misaligned exception，或由硬件透明处理。inactive 与 tail 元素不应产生内存访问，也不应因其地址产生异常。

对于 segment、indexed 和 strided 访问，每个 active field 或元素按其实际内存 `EEW` 判断对齐。whole-register 指令按其字节访问序列处理，但执行环境仍可施加更强对齐要求。

可移植软件应尽量使 vector 内存访问按元素宽度自然对齐，并在需要处理任意字节地址时准备好接受实现可能的性能差异或异常处理路径。

# 9. Vector Memory Consistency Model

vector memory instructions 遵循 RISC-V 内存一致性模型。单条 vector memory 指令可包含多个元素访问；这些访问与其他 hart 或设备观察到的顺序取决于指令类型。

unit-stride 与 strided 指令的元素访问可被实现以高效方式执行，但必须满足架构定义的异常、mask 和内存模型约束。indexed-unordered 指令明确允许元素访问乱序；indexed-ordered 指令提供元素顺序约束。若程序需要在 vector memory 指令前后建立额外顺序，应使用适当的 `FENCE` 或平台定义的同步机制。

masked-off 元素不访问内存，因此不参与内存一致性顺序。fault-only-first load 可缩短 `vl`，使后续软件只消费已成功访问的前缀。
