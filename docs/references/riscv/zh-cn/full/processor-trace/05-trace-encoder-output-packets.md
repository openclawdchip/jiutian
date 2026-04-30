# Chapter 5 Trace Encoder Output Packets

本节主体描述 Trace Encoder 输出 packets 的 payload。用于传输这些 packets 的 infrastructure 不在本文档范围内，因此不规定 packet 如何为 transport 封装。不过，必须向 encapsulator 提供以下信息：

- packet type；
- packet length，以 byte 为单位；
- packet payload。

两个示例 transport scheme 是 UltraSoC Messaging Infrastructure 和 Arm Trace Bus。Figure 5.1 展示 UltraSoC infrastructure 使用的 encapsulation：

- header byte 包含一个 5-bit field 指定 payload length（byte），一个 2-bit field 表示 `flow`（destination routing indicator），以及一个 bit 表示是否存在 optional 16-bit timestamp；
- `index` field 表示 packet source。bit 数取决于系统，trace encoder 发出的初始值为 zero，随着它通过 infrastructure 传播会被调整；
- optional 2-byte timestamp；
- packet payload。

Figure 5.1：Example encapsulated packet format。

另一种方式是，对 ATB 而言，packet source 由 `ATID` bus field 指示，并且没有 `flow` 的等价物，所以一个示例 encapsulation 可以是：

- 一个 5-bit field 指定 payload length，以 byte 为单位；
- 一个 bit 表示是否存在 optional 16-bit timestamp；
- optional 2-byte timestamp；
- packet payload。

可能希望 packet 起始处对齐到 ATB word。在这种情况下，一个 packet 的最后一个 beat 中的 `ATBYTES` bus field 可用于指示 valid bytes 的数量。

本节其余部分描述 payload portion 的内容，该内容应独立于 infrastructure。每个表中，fields 按 transmission order 列出：表中的第一个 field 最先传输，多 bit fields 按 LSB first 传输。

该 packet payload format 用于输出 encoded instruction trace。根据 encoding algorithm 的需求，使用三种不同 format。下列表格显示 payload 的 format，也就是不包括任何 encapsulation。

为了获得最佳性能，实际 packet length 可以使用 sign based compression 调整。最低限度应把该技术应用于 format 1 和 2 packets 的 `address` field；理想情况下则应应用于整个 packet，而不论 format。该技术从 packet 的最高有效端消除相同 bits，并相应调整 packet length。收到该 shortened packet 的 decoder 可以通过从收到的最高有效 bit 进行 sign-extension 来重建原始 full-length packet。

如果后续表中给出的 payload length，或应用 sign-based compression 后的 payload length，不是 whole bytes 的整数倍，则 payload 必须 sign-extended 到最近 byte boundary。

variable length packets 提供最大 encoding efficiency，但也带来一些挑战，尤其是在 packed packets 写入 memory 或经 communication channel offchip streaming 时，识别 packet boundaries。两个潜在解决方案如下：

- 如果 maximum packet payload length 是 `2^N-1`，例如 N 为 5 时最大长度为 31 bytes，并且 minimum packet payload length 是 1，则至少 `2^N` 个 zero bytes 的序列不可能出现在 packet payload 内。因此，在至少 `2^N` 个 zero bytes 的序列之后看到的第一个 non-zero byte 必然是某个 packet 的第一个 byte。该方法可用于 memory 或 data stream 中的 alignment。
- 适合写入 memory 的另一方法是把 memory 划分为 M bytes 的 blocks，例如 1 kbyte blocks，并把 packets 写入 memory，使得每个 block 的第一个 byte 总是一个 packet 的第一个 byte。这意味着 packets 不能跨越 block boundary，因此必须用 zero bytes 在 block 中最后一个 message 结束位置与 block boundary 之间填充。

## 5.1 Format 3 packets

Format 3 packets 用于 synchronization、报告 context 和 supporting information。共有 4 个 sub-formats。

本文档中使用的术语 `synchronization packet` 专指 format 3, subformat 0 和 subformat 1 packets。

## 5.2 Format 3 subformat 0 - Synchronisation

该 packet 包含 decoder 完全识别一条 instruction 所需的全部信息。它会在第一条 traced instruction 时发送，除非该 instruction 也正好是 exception handler 的第一条；也会在 resynchronisation timer 到期而安排 resynchronization 时发送。

### Table 5.1 Packet format 3, subformat 0

| Field name | Bits | Description |
| --- | --- | --- |
| `format` | 2 | `11 (sync)`：synchronisation。 |
| `subformat` | 2 | `00 (start)`：Start of tracing，或 resync。 |
| `branch` | 1 | 如果 address 指向 branch instruction 且 branch was taken，则设为 0。如果 instruction 不是 branch，或 branch is not taken，则设为 1。 |
| `privilege` | `privilege_width_p` | reported instruction 的 privilege level。 |
| `context` | `context_width_p`，或若 `nocontext_p` 为 1 则为 0 | instruction context。 |
| `address` | `iaddress_width_p - iaddress_lsb_p` | Full instruction address。address alignment 由 `iaddress_lsb_p` 决定。为了重建原始 byte address，address 必须 left shifted。 |

### 5.2.1 Format 3 branch field

如果 reported address 指向 branch instruction，该 bit 表示 taken/not taken status。如果删除该 bit，并改为把 branch status `carried over` 到下一个 `te_inst` packet 中报告，整体效率会略有改善。规范考虑过这种做法，但存在若干 pathological cases 会失败。例如，第一条 traced instruction 是 branch，随后立即发生 exception。这会在连续两条 instruction 上生成 format 3 packets。第二个 packet 不包含 branch map，因此除了在中间插入 format 1 packet 之外，没有办法报告第一个 branch 的 branch status。这有两个问题：

- 需要在同一个 cycle 生成 2 个 packets，会显著增加 encoder complexity；
- 会使 Figure 6.1 中的 algorithm 复杂化。

## 5.3 Format 3 subformat 1 - Exception

该 packet 也包含 decoder 完全识别一条 instruction 所需的全部信息。它在 exception 后发送；除报告 exception handler 的地址外，还包含 exception cause 和 faulted instruction 的地址。

如果启用 implicit exception mode（见 2.2.3），则省略 `address`。

### Table 5.2 Packet format 3, subformat 1

| Field name | Bits | Description |
| --- | --- | --- |
| `format` | 2 | `11 (sync)`：synchronisation。 |
| `subformat` | 2 | `01 (exception)`：Exception cause 和 trap handler address。 |
| `branch` | 1 | 如果 address 指向 branch instruction 且 branch was taken，则设为 0。如果 instruction 不是 branch，或 branch is not taken，则设为 1。 |
| `privilege` | `privilege_width_p` | reported instruction 的 privilege level。 |
| `context` | `context_width_p`，或若 `nocontext_p` 为 1 则为 0 | instruction context。 |
| `ecause` | `ecause_width_p` | Exception cause。 |
| `interrupt` | 1 | Interrupt。 |
| `address` | `iaddress_width_p - iaddress_lsb_p` | Full instruction address。address alignment 由 `iaddress_lsb_p` 决定。为了重建原始 byte address，address 必须 left shifted。 |
| `tvalepc` | `iaddress_width_p` | 如果 `ecause` 为 2 且 `interrupt` 为 0，即 illegal instruction exception，则为 exception address；否则为 trap value。 |

### 5.3.1 Format 3 tvalepc field

该 field 报告 illegal instructions 的地址，否则报告 trap value。这保证在所有必需情况下报告 faulting instruction 的地址。trap value 对 hardware breakpoints、access 或 page faults、以及 mis-aligned 的 instructions、loads 或 stores 设置为 faulting instruction 的地址；但对 illegal instructions 不这样设置，illegal instruction 中它设置为 opcode。

## 5.4 Format 3 subformat 2 - Context

该 packet 只包含 context，并在 context changes 且可以 imprecisely 报告时输出，见 Table 3.4。

### Table 5.3 Packet format 3, subformat 2

| Field name | Bits | Description |
| --- | --- | --- |
| `format` | 2 | `11 (sync)`：synchronisation。 |
| `subformat` | 2 | `10 (context)`：Context change。 |
| `privilege` | `privilege_width_p` | new context 的 privilege level。 |
| `context` | `context_width_p` | instruction context。 |

## 5.5 Format 3 subformat 3 - Support

该 packet 提供 supporting information 以帮助 decoder。它在以下情况下发出：

- Trace enabled 或 disabled；
- operating mode 改变；
- 一个或多个 trace packets 无法发送，例如由于 packet transport infrastructure 的 back-pressure。

`options` field 是占位符，必须由 implementation specific 的 individual bits 集合替换，每个 bit 对应 encoder 支持的一种 optional mode。

### 5.5.1 Format 3 subformat 3 qual_status field

tracing 结束时，encoder 报告最后一条 traced instruction 的地址，随后发送一个 format 3, subformat 3（supporting information）packet。规范提供两个 code 来指示 tracing 已结束：`ended_rep` 和 `ended_upd`。这关联到 5.6.2 中详细描述的同一 ambiguous case。原则上，当最后一条 traced instruction 位于 `looplabel` 时，可以使用该节所述机制消除歧义。但该机制依赖于在创建 format 1/2 packet 时就知道下一条 instruction 会生成 format 3 packet。由于 encoding algorithm 使用 3-stage pipe 并可访问 previous、current、next instructions，这对 privilege change 或 exception 是可行的；但判断下一条 instruction 是否满足 filtering criteria 要复杂得多，通常无法得到，至少不增加昂贵的额外 pipeline stage 就无法得到。

因此需要不同机制，也就是使用两个 code 表示 tracing 已结束：

- `ended_rep` 表示如果 tracing 没有结束，preceding packet 本不会发出；这意味着 tracing 在第 1 次 loop iteration 中执行 `looplabel` 后停止。
- `ended_upd` 表示 preceding packet 无论如何都会因 uninferable PC discontinuity 而发出；这意味着 tracing 在第 2 次 loop iteration 中执行 `looplabel` 后停止。

### Table 5.4 Packet format 3, subformat 3

| Field name | Bits | Description |
| --- | --- | --- |
| `format` | 2 | `11 (sync)`：synchronisation。 |
| `subformat` | 2 | `11 (support)`：decoder 的 supporting information。 |
| `enable` | 1 | 指示 encoder 是否 enabled。 |
| `encoder_mode` | N | 标识 trace algorithm。细节和 bit 数 implementation dependent。目前 Branch trace 是唯一已定义 mode，由 value 0 表示。 |
| `qual_status` | 2 | qualification status：`00 (no_change)` filter qualification 无变化；`01 (ended_rep)` qualification ended，preceding `te_inst` 被显式发送以指示 last qualification instruction；`10 (trace_lost)` 一个或多个 packets lost；`11 (ended_upd)` qualification ended，preceding `te_inst` 即使不是最后的 qualified instruction，也会因 updiscon 而发送。 |
| `options` | N | 所有 run-time configuration bits 的值。bit 数和定义 implementation dependent。例子包括：`sequentially inferred jumps` 不报告 sequentially inferable jumps 的 target；`implicit return` 不报告 function return addresses；`implicit exception` 如果 trap vector 可由 `ecause` 判定，则从 format 3, subformat 1 `te_inst` packets 排除 `address`；`branch prediction` branch predictor enabled；`jump target cache` jump target cache enabled；`full address` 始终输出 full addresses，作为 SW debug option。 |

如果 encoder implementation 确实早期获得 filtering results，并且 designer 选择在最后的 qualified instruction 同时也是 uninferable PC discontinuity 后续指令时使用 `updiscon` bit，则 qualification loss 应始终用 `ended_rep` 指示。

## 5.6 Format 2 packets

该 packet 只包含 instruction address，用于必须报告 instruction 地址且没有未报告 branch information 的情况。除非 full address mode enabled（见 2.2.2），否则 address 采用 differential format。

### Table 5.5 Packet format 2

| Field name | Bits | Description |
| --- | --- | --- |
| `format` | 2 | `10 (addr-only)`：differential address 且没有 branch information。 |
| `address` | `iaddress_width_p - iaddress_lsb_p` | Differential instruction address。 |
| `notify` | 1 | 如果该 bit 的值不同于 `address` 的 MSB，则表示该 packet 正在报告的 instruction 不是 uninferable discontinuity 的 target，而是因为通过 `trigger[2]` 请求了 notification，见 3.2.4。 |
| `updiscon` | 1 | 如果该 bit 的值不同于 `notify`，则表示该 packet 正在报告的 instruction 是 uninferable discontinuity 后续指令，并且也是 exception、privilege change 或 resync 前的 instruction，也就是会紧接着一个 format 3 `te_inst`。 |
| `irreport` | 1 | 如果该 bit 的值不同于 `updiscon`，则表示 packet 报告的 instruction 要么是 return 后续指令且其地址不同于 `implicit_return` return address stack 栈顶的 predicted return address，要么是 exception、interrupt、privilege change 或 resync 前最后 retired 的 instruction 且必须报告当前 address stack depth 或 nested call count。 |
| `irdepth` | `return_stack_size_p + (return_stack_size_p > 0 ? 1 : 0) + call_counter_size_p` | 如果 `irreport` 不同于 `updiscon`，该 field 指示 return address stack 中的 entries 数量，即失败 return 的 entry number，或 nested call count。如果 `irreport` 与 `updiscon` 相同，该 field 中所有 bits 也与 `updiscon` 相同。 |

### 5.6.1 Format 2 notify field

该 bit 的编码方式使其大多数时候与 `address` field 的 MSB 取相同值，因此会被压缩掉，不影响 encoding efficiency。它用于覆盖由于 notification request 而报告地址的情况，该 request 通过把 `trigger[2]` input 设为 1 来 signal。

### 5.6.2 Format 2 notify and updiscon fields

这些 bits 的编码方式使其大多数时候通过取 packet 中前一个 bit 的相同值而被压缩掉，对效率无影响。`notify` 通常与 `address` field 的 MSB 相同，`updiscon` 通常与 `notify` 相同。它们用于覆盖一种 pathological case，否则 decoding software 将无法无歧义地重建 program execution。考虑以下 code fragment：

```text
looplabel - 4: opcode A
looplabel : opcode B
looplabel + 4: opcode C
:
looplabel + N:JALR # Jump to looplabel
```

这是一个通过 indirect jump 返回下一次 iteration 的 loop。它是 uninferable discontinuity，将通过 format 1 或 2 packet 报告。但注意，初次进入 loop 是从 `looplabel - 4` 的 instruction fall-through，不会显式报告。因此重建 program 的 execution path 时，`looplabel` 地址会遇到两次。乍看之下，decoder 似乎可在第一次到达 loop label 时判断这不是 execution 结束，因为前一条 instruction 不能导致 uninferable discontinuity。它可以继续重建 execution path，直到到达 `JALR`，再由此推导 `looplabel` 处的 `opcode B` 是 final retired instruction。然而存在这种方法不工作的情况。例如 `looplabel + 4` 处发生 exception 时，decoder 若没有 encoder 的附加信息，就无法判断它发生在第 1 次还是第 2 次 loop iteration。这就是 `updiscon` field 的目的。

需要考虑四种场景：

1. code 执行到第 1 次 loop iteration 结束，encoder 在 `JALR` 后使用 format 1/2 报告 `looplabel`，然后继续执行 loop 的第 2 次 pass。此时 `updiscon == notify`。下一个 packet 将是 format 1/2。
2. code 执行到第 1 次 loop iteration 结束并跳回 `looplabel`，但随后在第二次 iteration 的 `looplabel + 4` 发生 exception、privilege change 或 resync。此时 encoder 在 `JALR` 后使用 format 1/2 报告 `looplabel`，且 `updiscon == !notify`，下一个 packet 是 format 3。
3. 在第 1 次执行 `looplabel` 后立即发生 exception。此时 encoder 使用 format 0/1/2 报告 `looplabel`，且 `updiscon == notify`，下一个 packet 是 format 3。
4. hart 请求 encoder notify `looplabel` 处 instruction 的 retirement。此时 encoder 用 `notify == !address[MSB]` 报告第 1 次执行 `looplabel`，后续执行用 `notify == address[MSB]`，因为后续本来就会因 `JALR` 被报告。

从 decoder 角度看，decoder 收到一个 format 1/2，其中报告 loop 中第一条 instruction（`looplabel`）的地址。它从上一个 reported address 跟随 execution path，直到到达 `looplabel`。因为 `looplabel` 前面不是 uninferable discontinuity，decoder 必须考虑 `notify` 和 `updiscon` 的值，并且可能需要等待下一个 packet，才能确定是否已经到达 final retired instruction：

- 如果 `updiscon == !notify`，表示 case 2。decoder 必须继续，直到第二次遇到 `looplabel`。
- 如果 `updiscon == notify`，decoder 还不能区分 case 1 和 case 3，必须等待下一个 packet。
  - 如果下一个 packet 是 format 3，这是 case 3。decoder 已经到达正确 instruction。
  - 如果下一个 packet 是 format 1/2，这是 case 1。decoder 必须继续，直到第二次遇到 `looplabel`。
- 如果 `notify == !address[MSB]`，表示 case 4 的第一次 iteration。decoder 已到达正确 instruction。

该例使用 `looplabel + 4` 处的 exception，但任何可导致 `looplabel + 4` 产生 format 3 的事件都会有相同行为：privilege change、resync timer expiry，或者 `looplabel` 是最后一条 traced instruction，因为 tracing 因某种原因 disabled。更多讨论见 5.5.1。

注意：只实现 `notify` bit 也可以获得正确 decoder behavior，方法是在地址被报告且它不是 uninferable discontinuity 后续 instruction 时，将 `notify` 设置为 `address[MSB]` 的反值。然而这会低效得多，因为在 exception、interrupt 或 resync 前输出 format 1/2 时，`notify` 大多数时候都必须不同于 `address[MSB]`，原因是该 instruction 是 uninferable jump target 的概率很低。使用两个独立 bits 能带来更好的 compression。

### 5.6.3 Format 2 irreport and irdepth

这些 bits 的编码方式使其大多数时候与 `updiscon` field 取相同值，因此会被压缩掉，不影响 encoding efficiency。如果 `implicit_return` mode enabled，encoder 会跟踪 traced nested calls 的数量，方式可以是 simple count（`call_counter_size_p` 非零）或 predicted return addresses 的 stack（`return_stack_size_p` 非零）。

如果实现了 predicted return addresses stack，则 predicted return addresses 与 actual return addresses 比较；若发生 misprediction，将生成一个 `te_inst` packet，并把 `irreport` 设为与 `updiscon` 相反的值。

在某些情况下，如果 packet 报告 exception、interrupt、privilege change 或 resync 前的最后一条 instruction，也必须报告当前 stack depth 或 call count。需要关注两种情况：

- 如果 reported address 是 return 后续 instruction，且没有 mis-predicted，则 encoder 必须在当前 stack depth 或 call count 非零时报告它。否则 decoder 会尝试跟随 execution path，直到从最外层 nested call 遇到 reported address。
- 如果 reported address 不是 return 后续 instruction，则 encoder 必须报告当前 stack depth 或 call count，除非自上次 call 以来没有 return，或者自上次 return 以来至少有一个 unreported branch。前者中 decoder 会正确停在 innermost call；后者中 decoder 会正确停在没有 unprocessed branches 的 call 中。否则 decoder 会跟随 execution path 直到遇到 reported address，而多数情况下这会是正确点，但对 recursive functions 不能保证，因为 reported address 会在 execution path 中出现多次。

## 5.7 Format 1 packets

该 packet 包含 branch information，用于必须报告 branch information 的情况，例如 branch map 已满；或必须报告 instruction 地址且自 previous packet 以来至少有一个 branch 的情况。如果包含 address，则除非 full address mode enabled，见 2.2.2，否则 address 为 differential format。

### 5.7.1 Format 1 updiscon field

见 5.6.2。

### 5.7.2 Format 1 branch_map field

当 branch map 变满时必须报告，但大多数情况下无需报告 address。通过把 `branches` 设为 0 指示这一点。例外是最终 branch 前一条 instruction 立即导致 uninferable discontinuity，此时 `branches` 设为 31。

### Table 5.6 Packet format 1 - address, branch map

| Field name | Bits | Description |
| --- | --- | --- |
| `format` | 2 | `01 (diff-delta)`：包含 branch information，并可包含 differential address。 |
| `branches` | 5 | `branch_map` 中 valid bits 数。`branch_map` bits 数按如下确定：`0` 该 format 不会发生；`1` 为 1 bit；`2-3` 为 3 bits；`4-7` 为 7 bits；`8-15` 为 15 bits；`16-31` 为 31 bits。例如 `branches = 12` 时，`branch_map` 为 15 bits，12 个 LSBs valid。 |
| `branch_map` | 由 `branches` field 决定 | bits array，指示 branches 是否 taken。bit 0 表示执行的最旧 branch instruction。每个 bit：`0` branch taken，`1` branch not taken。 |
| `address` | `iaddress_width_p - iaddress_lsb_p` | Differential instruction address。 |
| `notify` | 1 | 同 Table 5.5。 |
| `updiscon` | 1 | 同 Table 5.5。 |
| `irreport` | 1 | 同 Table 5.5。 |
| `irdepth` | `return_stack_size_p + (return_stack_size_p > 0 ? 1 : 0) + call_counter_size_p` | 同 Table 5.5。 |

### Table 5.7 Packet format 1 - no address, branch map

| Field name | Bits | Description |
| --- | --- | --- |
| `format` | 2 | `01 (diff-delta)`：包含 branch information，并可包含 differential address。 |
| `branches` | 5 | `branch_map` 中 valid bits 数。`0` 表示 packet 中有 31 bits 且无 `address`；`1-31` 对该 format 不会发生。 |
| `branch_map` | 31 | bits array，指示 branches 是否 taken。bit 0 表示执行的最旧 branch instruction。每个 bit：`0` branch taken，`1` branch not taken。 |

选择 sizes（1、3、7、15、31）是为了最小化效率损失。平均而言，因为要报告的 branches 数量小于所选 `branch_map` field size，会有一些 wasted bits。使用渐进式 sizes 使较短 packets 的 wasted bits 平均更少。如果 updiscons 之间的 branches 数量随机分布，则生成 large branch count packets 的概率较低，因此 longer packets 中增加的浪费对整体影响较小。此外，在较低 branch counts 时 packet 生成速率可能更高，因此减少该情形下的浪费会在最重要的时候提升整体 bandwidth。

### 5.7.3 Format 1 irstatus and irdepth fields

见 5.6.3。

## 5.8 Format 0 packets

该 format 用于 optional efficiency extensions。目前定义了两个 extension：报告 correctly predicted branches 的 count，以及报告 jump target cache index。

如果 branch prediction supported 且 enabled，则可选择输出完整 branch map（通过 format 1），或输出 correctly predicted branches 的 count。如果 correctly predicted branches 数量至少为 31，则使用 count format。如果有 31 个 unreported branches，即 branch map 已满，但并非全部预测正确，则输出 branch map。branch count 在以下条件下输出：

- branch 被 mis-predicted。count value 是 correctly predicted branches 数量减 31。不提供 address information；它隐式为 prediction failed 的 branch 的地址。
- updiscon、interrupt 或 exception 要求 encoder 输出 address。此时 encoder 输出 branch count，即 correctly predicted branches 数量减 31。
- branch count 达到最大值。严格说该情况不需要 address，但为避免必须区分它和上述情况的 packet format，会包含 address。它极少发生，因此可忽略 bandwidth impact。

如果 jump target cache supported 且 enabled，并且 updiscon 后要报告的 address 在 cache 中，则 encoder 可使用 format 0, subformat 1 输出 cache index。不过，如果 resulting packet 更短，encoder 仍可选择使用 format 1 或 2 输出 differential address。differential address 为 zero 或很小时可能出现这种情况。

### Table 5.8 Packet format 0, subformat 0 - no address, branch count

| Field name | Bits | Description |
| --- | --- | --- |
| `format` | 2 | `00 (opt-ext)`：optional efficiency extensions 的 formats。 |
| `subformat` | 见 5.8.1 | `0 (correctly predicted branches)`。 |
| `branch_count` | 32 | correctly predicted branches 数量减 31 的 count。 |
| `branch_fmt` | 2 | `00 (no-addr)`：packet 不包含 address，且最后一次正确预测之后的 branch 失败。`01-11` 对该 format 不会发生。 |

### 5.8.1 Format 0 subformat field

该 field 的宽度取决于支持的 optional formats 数量。目前定义两个 optional formats：correctly predicted branches 和 jump target cache。宽度由 `f0s_width` discovery field 指定，见 7.1。如果支持多个 optional formats，field width 必须非零。但如果只支持一个 optional format，可省略该 field，并从 support packet 中的 `options` field 推断该 field 的值，见 5.5。该规定允许未来增加 additional formats，而不降低现有 formats 的效率。

### 5.8.2 Format 0 branch_fmt field

该 field 的编码方式使得不需要 address 时它为 zero，从而允许 `branch_count` field 的 upper bits 被压缩掉。

当报告不带 address 的 branch count 时，是因为某个 branch prediction failed。然而，当 branch count 连同 address 一起报告时，原因可能是 packet 由 uninferable discontinuity、exception 发起，或在 `branch_count` 为 `0xffff_ffff` 时遇到了 branch。后一种情况下，reported address 总是 branch 的地址；前几种情况下也可能是。如果它是 branch，则必须明确说明 prediction 是否满足。如果满足，则 reported address 是最后一个 correctly predicted branch 的地址。

### Table 5.9 Packet format 0, subformat 0 - address, branch count

| Field name | Bits | Description |
| --- | --- | --- |
| `format` | 2 | `00 (opt-ext)`。 |
| `subformat` | 见 5.8.1 | `0 (correctly predicted branches)`。 |
| `branch_count` | 32 | correctly predicted branches 数量减 31 的 count。 |
| `branch_fmt` | 2 | `10 (addr)`：packet 包含 `address`。如果它指向 branch instruction，则 branch predicted correctly。`11 (addr-fail)`：packet 包含指向 prediction failed branch 的 `address`。`00,01` 对该 format 不会发生。 |
| `address` | `iaddress_width_p - iaddress_lsb_p` | Differential instruction address。 |
| `notify` | 1 | 同 Table 5.5。 |
| `updiscon` | 1 | 同 Table 5.5。 |
| `irreport` | 1 | 同 Table 5.5。 |
| `irdepth` | `return_stack_size_p + (return_stack_size_p > 0 ? 1 : 0) + call_counter_size_p` | 同 Table 5.5。 |

### Table 5.10 Packet format 0, subformat 1 - jump target index, branch map

| Field name | Bits | Description |
| --- | --- | --- |
| `format` | 2 | `00 (opt-ext)`。 |
| `subformat` | 见 5.8.1 | `1 (jump target cache)`。 |
| `index` | `cache_size_p` | 包含 target address 的 entry 的 jump target cache index。 |
| `branches` | 5 | `branch_map` 中 valid bits 数。长度规则同 Table 5.6；`0` 对该 format 不会发生。 |
| `branch_map` | 由 `branches` field 决定 | bits array，指示 branches 是否 taken。bit 0 表示执行的最旧 branch instruction。`0` branch taken，`1` branch not taken。 |
| `irreport` | 1 | 如果该 bit 的值不同于 `branch_map[MSB]`，则表示 packet 报告的 instruction 要么是 return 后续 instruction 且其地址不同于 `implicit_return` return address stack 栈顶 predicted return address，要么是 exception、interrupt、privilege change 或 resync 前最后 retired 的 instruction 且需要报告当前 address stack depth 或 nested call count。 |
| `irdepth` | `return_stack_size_p + (return_stack_size_p > 0 ? 1 : 0) + call_counter_size_p` | 如果 `irreport` 不同于 `branch_map[MSB]`，该 field 指示 return address stack entries 数或 nested call count。如果相同，所有 bits 也与 `branch_map[MSB]` 相同。 |

### Table 5.11 Packet format 0, subformat 1 - jump target index, no branch map

| Field name | Bits | Description |
| --- | --- | --- |
| `format` | 2 | `00 (opt-ext)`。 |
| `subformat` | 见 5.8.1 | `1 (jump target cache)`。 |
| `index` | `cache_size_p` | 包含 target address 的 entry 的 jump target cache index。 |
| `branches` | 5 | `branch_map` 中 valid bits 数。`0` 表示 packet 中无 `branch_map`；`1-31` 对该 format 不会发生。 |
| `irreport` | 1 | 如果该 bit 的值不同于 `branches[MSB]`，含义同 Table 5.10，只是比较对象换为 `branches[MSB]`。 |
| `irdepth` | `return_stack_size_p + (return_stack_size_p > 0 ? 1 : 0) + call_counter_size_p` | 如果 `irreport` 不同于 `branches[MSB]`，该 field 指示 return address stack entries 数或 nested call count。如果相同，所有 bits 也与 `branches[MSB]` 相同。 |

### 5.8.3 Format 0 irstatus and irdepth fields

这些 bits 的编码方式使其大多数时候与紧邻的 preceding bit 取相同值；该 preceding bit 取决于具体 packet format，可能是 `updiscon`、`branch_map[MSB]` 或 `branches[MSB]`。目的和行为如 5.6.3 所述。

对 jump target cache（subformat 1）而言，包含这些 fields 是为了允许使用该 format 报告在 implicit return prediction 中失败但位于 jump target cache 中的 return addresses。如果所有 implicit return failures 都使用 format 1 报告，实现可以省略这些 fields。
