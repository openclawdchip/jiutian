# 第 5 章 Trigger Module

trigger 可以导致 breakpoint exception、进入 Debug Mode，或 trace action，而不必执行特殊指令。这使它们在调试 ROM 中的代码时非常有价值。它们可以在给定 memory address 处的 instruction execution 上触发，也可以在 load/store 中的 address/data 上触发。这些特性即使在没有 Debug Module 的情况下也可能有用，因此 Trigger Module 被拆分成一个可独立实现的部分。

每个 trigger 可以支持多种特性。debugger 可以按如下方式建立所有 trigger 及其特性的列表：

1. 向 `tselect` 写 0。
2. 读回 `tselect` 以确认该 trigger 存在。如果不存在，退出。
3. 读取 `tdata1`，并根据 trigger type 可能读取 `tdata2` 和 `tdata3`。
4. 如果 `type` 为 0，则该 trigger 不存在。退出循环。
5. 递增 `tselect` 的值并重复。

有两种方式检查给定 trigger 是否是最后一个，以支持这些实现：

1. 当完全没有实现 hardware trigger 时，所有相关 register 返回 0。上述算法在检查 `type` 时终止。
2. 当实现 2 个 trigger 时，`tselect` 只是选择二者之一的单个 bit。当 debugger 写 2 时，读回为 0，从而终止枚举。

## 5.1 Trigger Registers

trigger register 只能在 machine 和 Debug Mode 中访问，以防不受信任的 user code 在未经 OS 许可的情况下导致进入 Debug Mode。

表 5.1：Trigger Registers

| Address | Name |
|---|---|
| `0x7a0` | Trigger Select |
| `0x7a1` | Trigger Data 1 |
| `0x7a1` | Match Control |
| `0x7a1` | Instruction Count |
| `0x7a2` | Trigger Data 2 |
| `0x7a3` | Trigger Data 3 |

### 5.1.1 Trigger Select (`tselect`, at `0x7a0`)

该寄存器决定可通过其他 trigger register 访问哪个 trigger。可访问 trigger 集合必须从 0 开始，并且连续。

写入大于等于受支持 trigger 数量的值，可能导致该寄存器中出现与写入值不同的值。debugger 应读回该值，以确认写入的是有效 index。

因为 trigger 既可由 Debug Mode 使用，也可由 M Mode 使用，所以 debugger 如果修改该寄存器，必须恢复它。

字段：`index[XLEN-1:0]`。

### 5.1.2 Trigger Data 1 (`tdata1`, at `0x7a1`)

字段：

| Field | Description | Access | Reset |
|---|---|---|---|
| `type` | 0：该 `tselect` 处没有 trigger。1：trigger 是 legacy SiFive address match trigger；不应实现，本文不进一步记录。2：trigger 是 address/data match trigger；该寄存器剩余 bit 按 `mcontrol` 描述。3：trigger 是 instruction count trigger；该寄存器剩余 bit 按 `icount` 描述。15：该 trigger 存在（因此枚举不应终止），但当前不可用。其他值保留供未来使用。 | R | Preset |
| `dmode` | 0：Debug 和 M Mode 都可写选中 `tselect` 处的 `tdata` register。1：只有 Debug Mode 可写选中 `tselect` 处的 `tdata` register；其他 mode 的写入被忽略。该 bit 只能从 Debug Mode 写。 | R/W | 0 |
| `data` | trigger-specific data。 | R/W | Preset |

### 5.1.3 Trigger Data 2 (`tdata2`, at `0x7a2`)

trigger-specific data。字段：`data[XLEN-1:0]`。

### 5.1.4 Trigger Data 3 (`tdata3`, at `0x7a3`)

trigger-specific data。字段：`data[XLEN-1:0]`。

### 5.1.5 Match Control (`mcontrol`, at `0x7a1`)

当 `type` 为 2 时，该寄存器作为 `tdata1` 访问。

向该寄存器任意字段写入不支持的值，会导致 reset value 被写入。因此，当 debugger 想使用某特性时，必须写入相应值，然后读回寄存器以确定是否支持。

address 和 data trigger 的实现高度依赖 processor core 的实现方式。为适配不同实现，execute、load 和 store address/data trigger 可以在实现最方便的任意时间点 fire。debugger 可以按 `timing` 中描述请求特定 timing。表 5.2 建议了最佳用户体验的 timing。

表 5.2：建议的 Breakpoint Timing

| Match Type | Suggested Trigger Timing |
|---|---|
| Execute Address | Before |
| Execute Instruction | Before |
| Execute Address+Instruction | Before |
| Load Address | Before |
| Load Data | After |
| Load Address+Data | After |
| Store Address | Before |
| Store Data | Before |
| Store Address+Data | Before |

字段：

| Field | Description | Access | Reset |
|---|---|---|---|
| `maskmax` | 指定硬件支持的最大 naturally aligned powers-of-two（NAPOT）范围。值是该范围 byte 数的 log2。值 0 表示只支持精确值匹配（1 byte range）。值 63 对应最大 NAPOT range，即 `2^63` byte。 | R | Preset |
| `select` | 0：在 virtual address 上执行 match。1：在 load/store 的 data value 或 executed instruction 上执行 match。 | R/W | 0 |
| `timing` | 0：该 trigger 的 action 会在触发它的 instruction 执行前执行，但在所有先前 instruction committed 之后。1：该 trigger 的 action 会在触发它的 instruction 执行后执行。它应在下一条 instruction 执行前发生，但实现 trigger 而不实现该建议，仍比完全不实现 trigger 更好。多数硬件只会实现某一种 timing，可能依赖 `select`、`execute`、`load` 和 `store`。该 bit 主要用于硬件向 debugger 通知会发生什么。硬件可以把该 bit 完全实现为 writable，使 debugger 有更多控制。`timing=0` 的 data load trigger 会导致 debugger 让 core 运行时同一 load 再次发生。对于 data load trigger，debugger 必须先尝试用 `timing=1` 设置 breakpoint。并非全部具有相同 `timing` 值的一串 chained trigger 永远不会 fire（除非连续 instruction 匹配相应 trigger）。 | R/W | 0 |
| `action` | 决定 trigger match 时发生什么。0：raise breakpoint exception。（用于软件希望在没有外部 debugger attached 时使用 trigger module。）1：进入 Debug Mode。（仅在 `dmode=1` 时支持。）2：start tracing。3：stop tracing。4：为该 match emit trace data。若为 data access match，emit 相应 Load/Store Address/Data；若为 instruction execution，emit 其 PC。其他值保留供未来使用。 | R/W | 0 |
| `chain` | 0：当该 trigger match 时，执行配置的 action。1：当该 trigger 不 match 时，它阻止下一个 index 的 trigger match。 | R/W | 0 |
| `match` | 0：value 等于 `tdata2` 时匹配。1：value 的最高 M bit 与 `tdata2` 的最高 M bit 匹配时匹配；M 是 XLEN-1 减去 `tdata2` 中包含 0 的最低有效 bit 的 index。2：value 大于等于（unsigned）`tdata2` 时匹配。3：value 小于（unsigned）`tdata2` 时匹配。4：value 的低半部分与 `tdata2` 的低半部分相等时匹配，比较前 value 的低半部分与 `tdata2` 的高半部分 AND。5：value 的高半部分与 `tdata2` 的低半部分相等时匹配，比较前 value 的高半部分与 `tdata2` 的高半部分 AND。其他值保留供未来使用。 | R/W | 0 |
| `m` | 置位时，在 M mode 中 enable 该 trigger。 | R/W | 0 |
| `h` | 置位时，在 H mode 中 enable 该 trigger。 | R/W | 0 |
| `s` | 置位时，在 S mode 中 enable 该 trigger。 | R/W | 0 |
| `u` | 置位时，在 U mode 中 enable 该 trigger。 | R/W | 0 |
| `execute` | 置位时，trigger 在被执行 instruction 的 virtual address 或 opcode 上 fire。 | R/W | 0 |
| `store` | 置位时，trigger 在 store 的 virtual address 或 data 上 fire。 | R/W | 0 |
| `load` | 置位时，trigger 在 load 的 virtual address 或 data 上 fire。 | R/W | 0 |

### 5.1.6 Instruction Count (`icount`, at `0x7a1`)

当 `type` 为 3 时，该寄存器作为 `tdata1` 访问。

向该寄存器任意字段写入不支持的值，会导致 reset value 被写入。因此，当 debugger 想使用某特性时，必须写入相应值，然后读回寄存器以确定是否支持。

该 trigger type 旨在作为 single step 使用，对 external debugger 和 software monitor program 都有用。对于该场景，不必支持大于 1 的 `count`。在这些场景中，mode bit 中唯一有用的两种组合是仅 `u`，或 `m`、`h`、`s` 和 `u` 全部设置。

如果硬件把 `count` 限制为 1，并改变 mode bit 而不是递减 `count`，该寄存器可仅用 2 bit 实现：一个用于 `u`，一个用于绑在一起的 `m`、`h` 和 `s`。如果只需要支持 external debugger 或只需要支持 software monitor，则一个 bit 就足够。

字段：

| Field | Description | Access | Reset |
|---|---|---|---|
| `count` | 当 `count` 递减到 0 时，trigger fire。硬件也可以不把 `count` 从 1 改为 0，而是清除 `m`、`h`、`s` 和 `u`。如果该寄存器只是为了 single step 而存在，这允许 `count` hard-wired 为 1。 | R/W | 1 |
| `m` | 置位时，M mode 中每条 completed instruction 或 taken exception 都使 `count` 减 1。 | R/W | 0 |
| `h` | 置位时，H mode 中每条 completed instruction 或 taken exception 都使 `count` 减 1。 | R/W | 0 |
| `s` | 置位时，S mode 中每条 completed instruction 或 taken exception 都使 `count` 减 1。 | R/W | 0 |
| `u` | 置位时，U mode 中每条 completed instruction 或 taken exception 都使 `count` 减 1。 | R/W | 0 |
| `action` | 决定 trigger match 时发生什么。0：raise breakpoint exception。1：进入 Debug Mode（仅在 `dmode=1` 时支持）。2：start tracing。3：stop tracing。4：emit trace data。其他值保留供未来使用。 | R/W | 0 |
