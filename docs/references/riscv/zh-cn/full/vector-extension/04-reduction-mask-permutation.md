# 14. Vector Reduction Operations

vector reduction 指令把 vector 源中的 active 元素规约为一个标量式结果，并把结果写入 destination vector register 的元素 0。通常 `vs1[0]` 提供初始 accumulator，`vs2` 提供待规约 vector。inactive 与 tail 元素不参与规约。

reduction 指令的 destination 是 vector register，但只有元素 0 定义为规约结果；其他元素按 tail/agnostic 规则处理。若没有 active 元素，则结果为初始 accumulator。

## 14.1. Vector Single-Width Integer Reduction Instructions

```asm
vredsum.vs   vd, vs2, vs1, vm
vredand.vs   vd, vs2, vs1, vm
vredor.vs    vd, vs2, vs1, vm
vredxor.vs   vd, vs2, vs1, vm
vredminu.vs  vd, vs2, vs1, vm
vredmin.vs   vd, vs2, vs1, vm
vredmaxu.vs  vd, vs2, vs1, vm
vredmax.vs   vd, vs2, vs1, vm
```

`vredsum` 执行 modulo `2^SEW` 加法规约。逻辑规约执行 AND、OR、XOR。`min/max` 规约按有符号或无符号比较选择结果。

## 14.2. Vector Widening Integer Reduction Instructions

```asm
vwredsumu.vs  vd, vs2, vs1, vm
vwredsum.vs   vd, vs2, vs1, vm
```

widening integer reduction 将 single-width 元素零扩展或符号扩展，并在 double-width accumulator 中求和。`vs1[0]` 与 destination 元素 0 为 double-width。

## 14.3. Vector Single-Width Floating-Point Reduction Instructions

```asm
vfredusum.vs  vd, vs2, vs1, vm
vfredosum.vs  vd, vs2, vs1, vm
vfredmin.vs   vd, vs2, vs1, vm
vfredmax.vs   vd, vs2, vs1, vm
```

`vfredusum` 是 unordered floating-point sum reduction；实现可以用任意树形顺序组合 active 元素，因此结果可能因舍入顺序不同而不同，但必须符合规范允许的浮点异常与 NaN 行为。`vfredosum` 是 ordered sum reduction，按元素顺序从 `vs1[0]` 开始累加。`vfredmin/max` 按浮点 min/max 语义规约。

## 14.4. Vector Widening Floating-Point Reduction Instructions

```asm
vfwredusum.vs  vd, vs2, vs1, vm
vfwredosum.vs  vd, vs2, vs1, vm
```

widening floating-point reduction 将较窄浮点元素扩展后，在较宽 accumulator 中规约。unordered 与 ordered 区别同 single-width 浮点规约。

# 15. Vector Mask Instructions

mask 指令操作一 bit-per-element 的 mask register。mask logical 指令把 vector register 当作 mask bit 集合处理，不依赖当前 `SEW`。mask-producing 指令的 tail 始终按 tail-agnostic 处理。

## 15.1. Vector Mask-Register Logical Instructions

```asm
vmand.mm    vd, vs2, vs1
vmnand.mm   vd, vs2, vs1
vmandnot.mm vd, vs2, vs1
vmxor.mm    vd, vs2, vs1
vmor.mm     vd, vs2, vs1
vmnor.mm    vd, vs2, vs1
vmornot.mm  vd, vs2, vs1
vmxnor.mm   vd, vs2, vs1
vmnot.m     vd, vs1
vmmv.m      vd, vs1
```

这些指令对 mask bit 执行布尔逻辑。`vmnot.m` 和 `vmmv.m` 是伪指令形式，可由基本 mask logical 编码表达。

## 15.2. Vector count population in mask `vcpop.m`

```asm
vcpop.m rd, vs2, vm
```

`vcpop.m` 统计 active mask bit 中为 1 的数量，并把计数写入标量 `rd`。若使用 mask，只有 `v0` 允许的元素参与计数。

## 15.3. `vfirst` find-first-set mask bit

```asm
vfirst.m rd, vs2, vm
```

`vfirst.m` 查找第一个 active 且 mask bit 为 1 的元素索引，并写入标量 `rd`。若不存在这样的元素，写入 -1。

## 15.4. `vmsbf.m` set-before-first mask bit

```asm
vmsbf.m vd, vs2, vm
```

`vmsbf.m` 在结果 mask 中设置位于第一个 set bit 之前的 active 元素；第一个 set bit 本身及其之后元素清零。若源中没有 set bit，则所有 active 元素置 1。

## 15.5. `vmsif.m` set-including-first mask bit

```asm
vmsif.m vd, vs2, vm
```

`vmsif.m` 设置第一个 set bit 之前及第一个 set bit 本身的 active 元素；之后元素清零。若源中没有 set bit，则所有 active 元素置 1。

## 15.6. `vmsof.m` set-only-first mask bit

```asm
vmsof.m vd, vs2, vm
```

`vmsof.m` 只设置第一个 active set bit 对应的结果元素；其他 active 元素清零。若源中没有 set bit，则 active 结果全为 0。

## 15.7. Example using vector mask instructions

mask 指令可组合实现条件循环、查找终止符、压缩存储前缀和分支条件。例如先用比较生成 mask，再用 `vfirst.m` 找到第一个满足条件的元素；若返回 -1，则本次 vector chunk 内没有匹配项，可继续下一 chunk。

## 15.8. Vector Iota Instruction

```asm
viota.m vd, vs2, vm
```

`viota.m` 对每个 active 元素写入其之前 active 且 set 的 mask bit 数量。它常用于 compress、prefix compaction 和把 mask 转换为写入偏移。

## 15.9. Vector Element Index Instruction

```asm
vid.v vd, vm
```

`vid.v` 将元素索引写入 active destination 元素，即元素 `i` 得到值 `i`。inactive 与 tail 元素按策略处理。

# 16. Vector Permutation Instructions

permutation 指令在 vector register 内或与标量之间重新排列元素。它们包括 scalar move、slide、gather、compress 和 whole register move。

## 16.1. Integer Scalar Move Instructions

```asm
vmv.x.s rd, vs2
vmv.s.x vd, rs1
```

`vmv.x.s` 把 `vs2` 的元素 0 移到标量 `x` register。`vmv.s.x` 把标量 `x` register 写入 `vd` 的元素 0。其他元素按 tail 策略或保持规则处理。某些 scalar move 指令在 `vstart` 非零时非法，因为它们只定义对元素 0 的特殊访问。

## 16.2. Floating-Point Scalar Move Instructions

```asm
vfmv.f.s rd, vs2
vfmv.s.f vd, rs1
```

这些指令在 vector 元素 0 与 floating-point scalar register 之间移动浮点值。格式和 NaN boxing 行为遵循相应浮点扩展约束。

## 16.3. Vector Slide Instructions

```asm
vslideup.vx/vi
vslidedown.vx/vi
vslide1up.vx
vslide1down.vx
vfslide1up.vf
vfslide1down.vf
```

`vslideup` 将元素向更高索引滑动 offset 个位置，低索引空出的元素保持或按策略处理。`vslidedown` 将元素向低索引滑动。`vslide1up` 与 `vslide1down` 一次滑动一个元素，并在空位插入标量整数或浮点值。slide 指令支持构建移位窗口、队列和卷积邻域。

## 16.4. Vector Register Gather Instructions

```asm
vrgather.vv/vx/vi
vrgatherei16.vv
```

gather 指令用 index 选择源 vector 元素并写入 destination。若 index 超出 `VLMAX`，结果元素为 0。`vrgatherei16.vv` 使用 16 bit index 元素以降低 index register 压力。gather 与 memory indexed load 不同，它只在 register 内重排。

## 16.5. Vector Compress Instruction

```asm
vcompress.vm vd, vs2, vs1
```

`vcompress.vm` 按 mask 将 `vs2` 中 mask 为 1 的 active 元素压缩到 destination 的连续低索引元素中。它常与 `viota.m` 或 mask 比较配合，用于过滤数据。source 与 destination 重叠有严格限制；不满足限制的编码保留或非法。

## 16.6. Whole Vector Register Move

```asm
vmv1r.v vd, vs2
vmv2r.v vd, vs2
vmv4r.v vd, vs2
vmv8r.v vd, vs2
```

whole vector register move 复制一个或多个完整 vector register，不依赖当前 `vtype`。这些指令用于 register state 管理和实现内部搬移。寄存器编号必须满足对应 register group 对齐和范围约束。
