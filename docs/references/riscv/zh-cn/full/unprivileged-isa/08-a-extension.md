# 第 8 章 `A` 原子指令标准扩展，版本 2.1

标准 atomic-instruction extension 命名为 `A`。它包含对 memory 执行 atomic read-modify-write 的指令，用于支持运行在同一 memory space 中的多个 RISC-V hart 之间的 synchronization。该扩展提供两种形式的 atomic instruction：load-reserved/store-conditional 指令，以及 atomic fetch-and-op memory 指令。两类 atomic instruction 都支持多种 memory consistency ordering，包括 unordered、acquire、release 和 sequentially consistent 语义。这些指令使 RISC-V 能够支持 RCsc memory consistency model。

> 经过大量争论，language community 和 architecture community 似乎终于把 release consistency 确定为标准 memory consistency model，因此 RISC-V atomic 支持围绕该模型构建。

## 8.1 指定 atomic instruction 的 ordering

base RISC-V ISA 具有 relaxed memory model，使用 `FENCE` 指令施加额外 ordering constraint。execution environment 把 address space 划分为 memory 和 I/O domain，`FENCE` 指令提供选项，对这两个 address domain 中一个或两个的访问排序。

为了更高效地支持 release consistency，每条 atomic instruction 具有两个 bit：`aq` 和 `rl`，用于指定其他 RISC-V hart 所观察到的额外 memory ordering constraint。这两个 bit 对两个 address domain 之一中的访问排序，即 atomic instruction 正在访问的那个 address domain：memory 或 I/O。对另一个 domain 中的访问不隐含 ordering constraint；若要跨两个 domain 排序，应使用 `FENCE` 指令。

如果两个 bit 都清零，则不会对 atomic memory operation 施加额外 ordering constraint。如果只设置 `aq` bit，则 atomic memory operation 被视为 acquire access，也就是说，同一 RISC-V hart 上后续 memory operation 不能被观察为发生在该 acquire memory operation 之前。如果只设置 `rl` bit，则 atomic memory operation 被视为 release access，也就是说，该 release memory operation 不能被观察为发生在同一 RISC-V hart 上任何更早 memory operation 之前。如果 `aq` 和 `rl` bit 都被设置，则 atomic memory operation 是 sequentially consistent 的；对同一 RISC-V hart 和同一 address domain 来说，它不能被观察为发生在任何更早 memory operation 之前，也不能被观察为发生在任何更晚 memory operation 之后。

## 8.2 Load-Reserved/Store-Conditional 指令

```text
31    27 26 25 24 20 19 15 14 12 11 7 6 0
funct5   aq rl rs2   rs1   funct3 rd   opcode
5        1  1  5     5     3      5    7

LR.W/D ordering 0   addr width dest AMO
SC.W/D ordering src addr width dest AMO
```

对单个 memory word 或 doubleword 的复杂 atomic memory operation 使用 load-reserved（`LR`）和 store-conditional（`SC`）指令执行。`LR.W` 从 `rs1` 中地址加载一个 word，把 sign-extended 值放入 `rd`，并登记一个 reservation set，也就是包含被寻址 word 中所有 byte 的一组 byte。`SC.W` 有条件地把 `rs2` 中的 word 写入 `rs1` 中地址：只有 reservation 仍然有效，并且 reservation set 包含将被写入的 byte 时，`SC.W` 才成功。如果 `SC.W` 成功，该指令把 `rs2` 中的 word 写入 memory，并向 `rd` 写入 0。如果 `SC.W` 失败，该指令不写 memory，并向 `rd` 写入非零值。不论成功还是失败，执行 `SC.W` 指令都会使该 hart 持有的任何 reservation 失效。`LR.D` 和 `SC.D` 对 doubleword 执行类似操作，并且只在 RV64 上可用。对于 RV64，`LR.W` 和 `SC.W` 会对放入 `rd` 的值 sign-extend。

> compare-and-swap（CAS）和 LR/SC 都可以用来构建 lock-free data structure。经过广泛讨论，我们基于几个原因选择 LR/SC：1）CAS 受 ABA problem 影响，而 LR/SC 避免了该问题，因为它监视对地址的所有访问，而不只是检查 data value 是否变化；2）CAS 还需要一种新的 integer instruction format，以支持三个 source operand（address、compare value、swap value），并且需要不同的 memory system message format，这会使 microarchitecture 复杂化；3）此外，为避免 ABA problem，其他系统提供 double-wide CAS（DW-CAS），以允许在测试并递增 counter 的同时测试 data word。这需要一条指令读取五个 register 并写两个 register，同时还需要新的更大 memory system message type，进一步增加实现复杂度；4）LR/SC 对许多 primitive 提供更高效的实现，因为它只需要一次 load，而 CAS 需要两次 load（一次在 CAS 指令之前获得用于 speculative computation 的值，第二次作为 CAS 指令的一部分检查值在更新前是否未变）。

> LR/SC 相比 CAS 的主要缺点是 livelock；如下文所述，我们在某些情况下通过架构保证 eventual forward progress 来避免该问题。另一个顾虑是，当前 x86 架构及其 DW-CAS 的影响，是否会使假定 DW-CAS 是基本机器 primitive 的 synchronization library 和其他软件移植复杂化。一个可能的缓解因素是 x86 最近增加了 transactional memory 指令，这可能导致软件从 DW-CAS 迁移出去。

> 更一般地说，multi-word atomic primitive 是可取的，但它应采取什么形式仍有大量争论，并且保证 forward progress 会增加系统复杂度。我们当前想法是，作为可选 standard extension `T`，包含一个小型、容量受限的 transactional memory buffer，类似最初 transactional memory 提案中的设计。

值为 1 的 failure code 保留用于编码 unspecified failure。其他 failure code 当前保留，portable software 只应假定 failure code 为非零。

> 我们保留 failure code 1 表示 “unspecified”，这样简单实现可以使用 `SLT`/`SLTU` 指令已有 mux 返回该值。更具体的 failure code 可能在 ISA 的未来版本或扩展中定义。

对于 `LR` 和 `SC`，`A` 扩展要求 `rs1` 中保存的地址按 operand 大小自然对齐（即 64-bit word 需要 8-byte 对齐，32-bit word 需要 4-byte 对齐）。如果地址未自然对齐，将产生 address-misaligned exception 或 access-fault exception。对于除了 misalignment 之外本来能够完成的 memory access，如果该 misaligned access 不应被模拟，则可以产生 access-fault exception。

> 在大多数系统中，模拟 misaligned LR/SC sequence 是不实际的。

> Misaligned LR/SC sequence 还提出了同时访问多个 reservation set 的可能性，而当前定义并未提供这种能力。

实现可以在每次 `LR` 上登记任意大的 reservation set，只要 reservation set 包含被寻址 data word 或 doubleword 的全部 byte。`SC` 只能与 program order 中最近的 `LR` 配对。只有在 `LR` 和 `SC` 之间观察不到来自另一个 hart 对 reservation set 的 store，并且在 program order 中 `LR` 与该 `SC` 之间没有其他 `SC` 时，`SC` 才可以成功。只有在 `LR` 和 `SC` 之间观察不到来自 hart 之外的 device 对 `LR` 指令访问的 byte 的 write 时，`SC` 才可以成功。注意，该 `LR` 可能具有不同 effective address 和 data size，但把 `SC` 的地址作为 reservation set 的一部分保留了下来。

> 按照该模型，在具有 memory translation 的系统中，如果较早的 `LR` 使用具有不同 virtual address 的 alias 保留了同一 location，那么允许 `SC` 成功；但如果 virtual address 不同，也允许它失败。

为了适应 legacy device 和 bus，来自 RISC-V hart 之外 device 的 write 只要求在与 `LR` 访问的 byte 重叠时使 reservation 失效。当这些 write 访问 reservation set 中其他 byte 时，不要求它们使 reservation 失效。

如果地址不在 program order 中最近 `LR` 的 reservation set 内，`SC` 必须失败。如果在 `LR` 和 `SC` 之间可以观察到另一个 hart 对 reservation set 的 store，`SC` 必须失败。如果在 `LR` 和 `SC` 之间可以观察到某个其他 device 对 `LR` 访问的 byte 的 write，`SC` 必须失败。（如果这样的 device 写 reservation set 但不写 `LR` 访问的 byte，`SC` 可以失败，也可以不失败。）如果在 `LR` 和 `SC` 之间的 program order 中存在另一个 `SC`（到任何地址），则该 `SC` 必须失败。成功 LR/SC sequence 的 atomicity requirement 的精确定义由第 14.1 节中的 Atomicity Axiom 给出。

平台应提供一种方式来确定 reservation set 的大小和形状。

> platform specification 可以约束 reservation set 的大小和形状。例如，Unix platform 预计会要求 main memory 的 reservation set 具有固定大小、连续、自然对齐，并且不大于 virtual memory page size。

应使用对 memory 中 scratch word 的 store-conditional 指令强制使任何既有 load reservation 失效：

- 在 preemptive context switch 期间；
- 在必要时改变 virtual 到 physical address mapping 时，例如迁移可能包含 active reservation 的 page 时。

> hart 执行 `LR` 或 `SC` 时会使该 hart 的 reservation 失效，这意味着一个 hart 一次只能持有一个 reservation，并且 `SC` 只能与 program order 中最近的 `LR` 配对，`LR` 也只能与下一条后续 `SC` 配对。这是对第 14.1 节 Atomicity Axiom 的一种限制，以确保软件能在预期常见实现上正确运行；这些实现以这种方式操作。

`SC` 指令绝不会被另一个 RISC-V hart 观察为发生在建立 reservation 的 `LR` 指令之前。可以通过在 `LR` 指令上设置 `aq` bit，使 LR/SC sequence 具有 acquire semantics。可以通过在 `SC` 指令上设置 `rl` bit，使 LR/SC sequence 具有 release semantics。在 `LR` 指令上设置 `aq` bit，并在 `SC` 指令上同时设置 `aq` 和 `rl` bit，会使 LR/SC sequence sequentially consistent，意味着它不能与同一 hart 上更早或更晚的 memory operation 重排序。

如果 `LR` 和 `SC` 上两个 bit 都未设置，则 LR/SC sequence 可以被观察为发生在同一 RISC-V hart 周围 memory operation 之前或之后。当 LR/SC sequence 用于实现 parallel reduction operation 时，这可能是合适的。

软件不应在未同时设置 `aq` bit 的情况下设置 `LR` 指令上的 `rl` bit，也不应在未同时设置 `rl` bit 的情况下设置 `SC` 指令上的 `aq` bit。`LR.rl` 和 `SC.aq` 指令不保证提供比两个 bit 都清零更强的 ordering，但可能导致较低性能。

```asm
# a0 holds address of memory location
# a1 holds expected value
# a2 holds desired value
# a0 holds return value, 0 if successful, !0 otherwise
cas:
    lr.w  t0, (a0)        # Load original value.
    bne   t0, a1, fail    # Doesn't match, so fail.
    sc.w  t0, a2, (a0)    # Try to update.
    bnez  t0, cas         # Retry if store-conditional failed.
    li    a0, 0           # Set return to success.
    jr    ra              # Return.
fail:
    li    a0, 1           # Set return to failure.
    jr    ra              # Return.
```

图 8.1：使用 LR/SC 实现 compare-and-swap 函数的示例代码。

LR/SC 可用于构造 lock-free data structure。图 8.1 展示了使用 LR/SC 实现 compare-and-swap 函数的示例。如果内联，compare-and-swap 功能只需要四条指令。

## 8.3 Store-Conditional 指令的 eventual success

标准 `A` 扩展定义 constrained LR/SC loop，具有以下性质：

- 该 loop 只包含一个 LR/SC sequence，以及在失败情况下重试该 sequence 的代码，并且必须由至多 16 条顺序放置在 memory 中的指令构成。
- LR/SC sequence 以一条 `LR` 指令开始，以一条 `SC` 指令结束。在 `LR` 和 `SC` 指令之间动态执行的代码，只能包含 base `I` instruction set 中的指令，但不包括 load、store、backward jump、taken backward branch、`JALR`、`FENCE`、`FENCE.I` 和 `SYSTEM` 指令。如果支持 `C` 扩展，则上述 `I` 指令的 compressed form 也被允许。
- 用于重试失败 LR/SC sequence 的代码可以包含 backward jump 和/或 branch，以重复 LR/SC sequence；但除此之外，与 `LR` 和 `SC` 之间的代码具有相同约束。
- `LR` 和 `SC` 地址必须位于具有 LR/SC eventuality property 的 memory region 内。execution environment 负责传达哪些 region 具有该属性。
- `SC` 必须到达与同一 hart 最近执行的 `LR` 相同的 effective address，并且 data size 相同。

不位于 constrained LR/SC loop 内的 LR/SC sequence 是 unconstrained。Unconstrained LR/SC sequence 在某些实现上的某些尝试中可能成功，但在其他实现上可能永远不成功。

> 我们把 LR/SC loop 长度限制为在 base ISA 中适合 64 个连续 instruction byte，以避免对 instruction cache 和 TLB 的大小与 associativity 施加过度限制。类似地，我们禁止 loop 内有其他 load 和 store，以避免对在 private cache 中跟踪 reservation 的简单实现的数据 cache associativity 施加限制。对 branch 和 jump 的限制限制了 sequence 中可以花费的时间。禁止 floating-point operation 和 integer multiply/divide，是为了简化 operating system 在缺少适当硬件支持的实现上对这些指令的模拟。

> 软件并未被禁止使用 unconstrained LR/SC sequence，但 portable software 必须检测 sequence 反复失败的情况，然后回退到不依赖 unconstrained LR/SC sequence 的替代代码序列。实现被允许无条件使任何 unconstrained LR/SC sequence 失败。

如果 hart `H` 进入 constrained LR/SC loop，execution environment 必须保证以下事件之一最终发生：

- `H` 或某个其他 hart 对 `H` 的 constrained LR/SC loop 中 `LR` 指令的 reservation set 执行一次成功的 `SC`。
- 某个其他 hart 对 `H` 的 constrained LR/SC loop 中 `LR` 指令的 reservation set 执行 unconditional store 或 AMO 指令，或者系统中的某个其他 device 写该 reservation set。
- `H` 执行一个 branch 或 jump，退出 constrained LR/SC loop。
- `H` 发生 trap。

注意，这些定义允许实现因任何原因偶尔使 `SC` 指令失败，只要不违反上述保证。

> eventuality guarantee 的一个结果是：如果 execution environment 中一些 hart 正在执行 constrained LR/SC loop，并且 execution environment 中没有其他 hart 或 device 对该 reservation set 执行 unconditional store 或 AMO，那么至少一个 hart 最终会退出其 constrained LR/SC loop。相反，如果其他 hart 或 device 持续写该 reservation set，则不保证任何 hart 会退出其 LR/SC loop。

Load 和 load-reserved 指令本身不会阻碍其他 hart 的 LR/SC sequence 取得进展。我们指出，该约束意味着，除其他含义外，其他 hart（可能位于同一 core 内）执行的 load 和 load-reserved 指令不能无限期阻碍 LR/SC 进展。例如，由共享 cache 的另一个 hart 导致的 cache eviction 不能无限期阻碍 LR/SC 进展。通常，这意味着 reservation 的跟踪独立于任何 shared cache eviction。类似地，hart 内 speculative execution 导致的 cache miss 不能无限期阻碍 LR/SC 进展。

> 这些定义允许 `SC` 指令因实现原因 spurious fail，只要最终取得 progress。

> CAS 的一个优点是，它保证某个 hart 最终取得 progress，而 LR/SC atomic sequence 在某些系统上可能无限期 livelock。为避免这一顾虑，我们为某些 LR/SC sequence 增加了 livelock freedom 的架构保证。

> 本规范较早版本施加了更强的 starvation-freedom guarantee。不过，较弱的 livelock-freedom guarantee 足以实现 C11 和 C++11 语言，并且在某些 microarchitectural style 中更容易提供。

## 8.4 Atomic Memory Operation

```text
31    27 26 25 24 20 19 15 14 12 11 7 6 0
funct5   aq rl rs2   rs1   funct3 rd   opcode
5        1  1  5     5     3      5    7

AMOSWAP.W/D    ordering src addr width dest AMO
AMOADD.W/D     ordering src addr width dest AMO
AMOAND.W/D     ordering src addr width dest AMO
AMOOR.W/D      ordering src addr width dest AMO
AMOXOR.W/D     ordering src addr width dest AMO
AMOMAX[U].W/D  ordering src addr width dest AMO
AMOMIN[U].W/D  ordering src addr width dest AMO
```

atomic memory operation（AMO）指令执行 read-modify-write operation，用于 multiprocessor synchronization，并使用 `R-type` instruction format 编码。这些 AMO 指令原子地从 `rs1` 中地址加载一个 data value，把该值放入寄存器 `rd`，对所加载值和 `rs2` 中原始值应用一个 binary operator，然后把结果存回 `rs1` 中地址。AMO 可以操作 memory 中的 64-bit word（仅 RV64）或 32-bit word。对于 RV64，32-bit AMO 始终对放入 `rd` 的值 sign-extend。

对于 AMO，`A` 扩展要求 `rs1` 中保存的地址按 operand 大小自然对齐（即 64-bit word 需要 8-byte 对齐，32-bit word 需要 4-byte 对齐）。如果地址未自然对齐，将产生 address-misaligned exception 或 access-fault exception。对于除了 misalignment 之外本来能够完成的 memory access，如果该 misaligned access 不应被模拟，则可以产生 access-fault exception。第 22 章描述的 `Zam` 扩展放宽该要求，并规定 misaligned AMO 的语义。

支持的 operation 包括 swap、integer add、bitwise AND、bitwise OR、bitwise XOR，以及 signed 和 unsigned integer maximum 与 minimum。在没有 ordering constraint 的情况下，这些 AMO 可用于实现 parallel reduction operation；在这种情况下，通常会通过写入 `x0` 丢弃 return value。

> 我们提供 fetch-and-op 风格的 atomic primitive，是因为它们比 LR/SC 或 CAS 更适合扩展到高度并行系统。简单 microarchitecture 可以用 LR/SC primitive 实现 AMO，只要实现能够保证 AMO 最终完成。更复杂的实现也可以在 memory controller 中实现 AMO，并且当 destination 为 `x0` 时，可以优化掉对原始值的取回。

> AMO 集合被选择为高效支持 C11/C++11 atomic memory operation，同时也支持 memory 中的 parallel reduction。AMO 的另一个用途是对 I/O space 中 memory-mapped device register 进行 atomic update（例如设置、清除或切换 bit）。

为了帮助实现 multiprocessor synchronization，AMO 可选地提供 release consistency semantics。如果设置 `aq` bit，则该 RISC-V hart 中没有后续 memory operation 能被观察为发生在 AMO 之前。相反，如果设置 `rl` bit，则其他 RISC-V hart 不会观察到 AMO 发生在该 RISC-V hart 中 AMO 之前的 memory access 之前。在 AMO 上同时设置 `aq` 和 `rl` bit，会使该 sequence sequentially consistent，意味着它不能与同一 hart 上更早或更晚的 memory operation 重排序。

> AMO 被设计为高效实现 C11 和 C++11 memory model。虽然 `FENCE R, RW` 指令足以实现 acquire operation，`FENCE RW, W` 足以实现 release，但与设置相应 `aq` 或 `rl` bit 的 AMO 相比，二者都隐含了额外且不必要的 ordering。

图 8.2 展示了一个由 test-and-test-and-set spinlock 保护 critical section 的示例代码序列。注意，第一个 AMO 标记为 `aq`，用于把 lock acquisition 排在 critical section 之前；第二个 AMO 标记为 `rl`，用于把 critical section 排在 lock relinquishment 之前。

> 我们建议在 lock acquire 和 release 中都使用上面展示的 AMO Swap idiom，以简化 speculative lock elision 的实现。

`A` 扩展中的指令也可以用于提供 sequentially consistent load 和 store。Sequentially consistent load 可以实现为同时设置 `aq` 和 `rl` 的 `LR`。Sequentially consistent store 可以实现为 `AMOSWAP`：它把旧值写入 `x0`，并同时设置 `aq` 和 `rl`。

```asm
li           t0, 1              # Initialize swap value.
again:
    lw           t1, (a0)        # Check if lock is held.
    bnez         t1, again       # Retry if held.
    amoswap.w.aq t1, t0, (a0)    # Attempt to acquire lock.
    bnez         t1, again       # Retry if held.
    # ...
    # Critical section.
    # ...
    amoswap.w.rl x0, x0, (a0)    # Release lock by storing 0.
```

图 8.2：mutual exclusion 示例代码。`a0` 包含 lock 的地址。
