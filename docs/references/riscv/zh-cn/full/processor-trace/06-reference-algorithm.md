# Chapter 6 Reference Algorithm

本章内容仅为 informative。

Figure 6.1 给出了 compressed branch trace 的 reference algorithm。图中使用以下术语：

- `te_inst`：encoder 发出的 packet type 名称，见 Chapter 5。
- `inst`：`instruction` 的缩写。
- `updiscon`：Uninferable PC discontinuity。它标识一种 instruction，该 instruction 导致 program counter 以无法仅从 source code 预测的量改变，即 `itype` values 8、10、12 或 14。
- `Qualified?`：满足 filtering criteria 的 instruction 是 qualified，并会被 traced。
- `Branch?`：instruction 是否为 branch，即 `itype` values 4 或 5。
- `branch map`：一个 vector，每个 bit 表示一个 branch 的 outcome。0 表示 branch was taken，1 表示 not taken。
- `e_ccd`：exception 已 signalled，或 context changed 且应被当作 uninferable PC discontinuity 处理，见 Table 3.4。
- `ppch`：privilege changed，或 context changed 且需要 precisely 报告，见 Table 3.4。
- `ppch_br`：同上，但 branch map not empty。
- `er_ccdn`：instruction retirement 和 exception 在同一 cycle signalled，或 context changed 且应作为 uninferable PC discontinuity 处理，或 context notification，见 Table 3.4。
- `exc_only`：exception signalled without simultaneous retirement。
- `cci`：可 imprecisely 报告的 context change，见 Table 3.4。
- `rep_br`：由于 branch map full 或 misprediction 而 report branches。
- `branches`：已遇到但尚未向 decoder 报告的 branches 数量。
- `pbc`：correctly predicted branches count；如果 branch predictor disabled 或不存在，则始终为 zero。
- `resync count`：用于跟踪何时需要发送 synchronization packet 的 counter，见 6.2。
- `max_resync`：安排 synchronization packet 的 resync counter value，见 6.2。
- `resync_br`：resync counter 已达到最大值，且 branch map 中仍有尚未输出的 entries，见 6.2。

Figure 6.1 展示逐条 instruction 的行为，只对应 single-retirement system 中看到的行为。虽然 core to encoder interface 允许 RISC-V hart 同时提供 multiple retiring instructions 的信息，但 encoder 生成的最终 packet sequence 必须与一次 retire one instruction 时相同。

假定 encoder 内有 3-stage pipeline，使 encoder 可以看到 current、previous 和 next instructions。所有 packets 都使用与 current instruction 相关的信息生成。图中的 orange diamonds 表示基于 previous instruction 的 decision，green diamond 表示基于 next instruction 的 decision，其他 diamonds 都基于 current instruction。

此外，encoder 还可以生成一种图中为清晰起见未显示的 packet type。support packet，即 format 3, subformat 3，见 5.5，会在以下情况下发送：

- encoder enabled 或 disabled，或者 configuration changed，用于通知 decoder encoder 的 operating mode；
- final qualified instruction 已 traced 之后，用于通知 decoder tracing has stopped；
- trace packets lost 时，例如写入 packet 的 buffer 已满。这种情况下，当下次有可用空间时，加载到 buffer 的第一个 packet 必须是 support packet。随后 tracing 将用 sync packet resume。

注意：如果 `halted` 或 `reset` sideband signals asserted（见 Table 3.5），encoder 会表现得像收到了一条 unqualified instruction：输出 `te_inst` 报告 previous instruction 的地址，随后输出 `te_support`。

## 6.1 Format selection

除两种情况外，packet format 都仅由相关 decision 的 `yes` 结果决定。

当单独报告 branch information（不带 address）时，format 1 与 format 0, subformat 0 的选择取决于 correctly predicted branches 的数量。如果 predictor 不支持或 disabled，该数量为 0。直到至少有 31 个 branches 需要报告时才会生成 packet。如果这 31 个 branches 中至少一个 outcome 没有被正确预测，则使用 format 1。如果全部预测正确，此时不输出任何内容，encoder 继续计数 correctly predicted branch outcomes。一旦某个 branch outcome 没有被正确预测，encoder 将输出一个 format 0, subformat 0 packet。另见 5.8。

图中间 `format 0/1/2` 情况的 format 选择也需要进一步说明：

- 如果 correctly predicted branches 数量为 31 或更多，则始终使用 format 0, subformat 0。
- 否则，如果 jump target cache supported 且 enabled，并且正在报告的 address 位于 cache 中，则通常使用 format 0, subformat 1，报告与该 address 关联的 cache index。如果有 branches 需要报告，也会包含 branch information。不过，如果输出等价的 format 1 或 2 packet（包含 differential address，可带或不带 branch information）会得到更短 packet，则 encoder 可以选择这样做，见 5.8。
- 否则，如果有 branches 要报告，则使用 format 1；否则使用 format 2。

Packet formats 0、1 和 2 的组织方式使 address 通常为 final field。最小化表示 address 所需的 bits 数会降低 total packet size，并显著提升效率。见 Chapter 5。

## 6.2 Resynchronisation

根据 2.1.5，在 `a prolonged period of time` 后必须输出 format 3 synchronisation packet。确定这一点的确切机制未规定，但可选方案包括统计自上一条 synchronization message 发送以来发出的 `te_inst` packets 数量，或 elapsed clock cycles 数量。

需要 resync 时，主要目标是输出 format 3 packet，使 decoder 无需任何历史即可从该点开始 tracing。不过，如果 decoder 已经 synced，还要求它能无缝地继续跟随 execution path，一直到并穿过 format 3 packet。因此，在输出 format 3 packet 之前，如果存在任何 unreported branches，就必须为 preceding instruction 输出 format 1 packet，因为 format 3 不包含 branch map。如果 resync timer 已超过阈值，将发送 format 3。在此之前的 cycle，也就是 resync timer value 恰好达到阈值时，如果 branch map 非空，将生成 format 1。

## 6.3 Multiple retirement considerations

如本节前面所述，对 single-retirement system，reference algorithm 应用于每条 retired instruction。当 instructions 以 blocks retired 时，只需要考虑 block 中第一条和最后一条 instruction，因为中间所有指令都是 `uninteresting`，不会影响 encoder state；它们通过 Figure 6.1 的路径不经过任何 rectangular boxes。

多数情况下，block 的第一条或最后一条 instruction 中只有一条是 interesting，因此 encoder 不需要从一个 block 生成超过一个 packet。不过有少数情况并非如此，encoder 可能需要从同一个 block 生成两个 packets。

例如，如果 block 的第一条 instruction 是 first traced instruction，则它必须生成 packet。但如果该 block 也指示 exception 或 interrupt（`itype = 1` 或 `2`），那么 block 中最后一条 instruction 也必须生成 packet。

每 cycle 生成 multiple packets 会显著复杂化 encoder，而这类情况只会很少发生，因此 encoder 中的 elastic buffering 是首选方法。这样后续 blocks 可在 encoder 从一个 block 生成两个连续 packets 时排队。只要 hart 没有报告任何内容的 cycle，或者遇到 `itype = 0` 的 block（对 encoder 不感兴趣），encoder 就可以 drain elastic buffer。

存在 pathological cases，其中连续 blocks 可能都要求从 first 和 last instructions 生成 packets，但只有这些 blocks 也在连续 cycles 输入时才需要 elastic buffering。实践中可能发生这种情况的例子很少。迄今识别到的最坏情况是上面例子的变体：exception 是 `ecall`，而它又在 trap handler 的前几条指令中遇到其他形式的 exception 或 interrupt：

- Block 1：`itype = 1 (ecall)`，`iretires > 1`。从 first instruction（first traced）和 last instruction（ecall 前最后一条）生成 packet。
- Block 2：`itype = 1 or 2`（其他 exception 或 interrupt），`iretires > 0`。从 first instruction（ecall trap handler）和 last instruction（其他 exception 或 interrupt 前最后一条）生成 packet。
- Block 3：从 first instruction（其他 exception 或 interrupt trap handler）生成 packet。

因为 `ecall` 对 hart 的 fetch unit 已知且可 predicted，所以 block 2 可能在 block 1 之后的 cycle 出现。不过，可以合理假设其他 exception 或 interrupt 不可预测，因此 blocks 2 和 3 之间会有若干 cycles，这会允许 encoder `catch up`。建议 encoders 实现足够的 elastic buffering 以处理该情况；如果 elastic buffer 因某种原因 overflows，则应发出 support packet 指示 trace lost。
