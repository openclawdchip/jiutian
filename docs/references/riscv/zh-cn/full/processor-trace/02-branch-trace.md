# Chapter 2 Branch Trace

Instruction delta tracing，也称为 branch tracing，通过从已知起始地址跟踪执行，并发送程序所经历的 delta 信息来工作。delta 通常由 jump、call、return 和 branch 类型指令引入，不过 interrupt 和 exception 也是 delta 的类型。

Instruction delta tracing 利用 processor 基于其正在执行的程序而表现出的确定性行为，为指令序列提供高效编码。

这种方法依赖 decoder 可获得 program binary 的离线副本，因此通常不适合动态程序、自修改程序，或禁止访问 program binary 的程序。

虽然 program binary 已经足够，但若能访问 assembly 或更高层 source code，将提升 decoder 在 debugger 中呈现 decoded trace 的能力，例如用 source code 行号、label、variable name 等标注 traced instructions。

该方法可以扩展到处理小段确定性的动态代码，方法是让 decoder 向 target 请求 instruction memory。memory lookup 通常会导致性能下降到不可接受的程度，不过它们适合检查中等规模的 jump table，例如 operating system 的 exception/interrupt vector pointers，这些指针可能在 boot up 时以及服务注册时被调整。静态链接程序和动态链接程序都可以用这种方式 trace。静态链接程序比较直接，因为它们通常在已知 address space 中运行，往往直接映射到 physical memory。动态链接程序要求 debugger 使用 trace 或 stop-mode debugging 跟踪 memory allocation 操作。

## 2.1 Instruction delta trace concepts

### 2.1.1 Sequential instructions

对于 RISC-V 这样的 ISA，所有指令都是无条件执行的，或者至少可以根据 program binary 判定它们是否执行，因此 delta 之间的指令被假定为顺序执行。所以 trace 中无需报告这些指令。trace 只需要包含 branch 是否 taken、taken indirect jump 的地址，或者其他 program counter discontinuity。

### 2.1.2 Uninferable PC discontinuities

uninferable program counter discontinuity 是一种不能仅从 program binary 推断出的 program counter 变化。在这些情况下，instruction delta trace 必须包含 destination address，也就是下一条有效指令的地址。

Indirect jump 是一个例子，其中下一条 instruction address 由寄存器内容决定，而不是由 program binary 中嵌入的常量决定。在这种情况下，必须 trace jump 后续指令的地址，也称为 jump target。

Interrupt 和 exception 是另一种形式的 uninferable PC discontinuity；下文会详细讨论。

### 2.1.3 Branches

branch 是一种指令，其 jump 是否发生取决于寄存器或 flag 的值。为了让 decoder 能跟随 program flow，trace 必须包含 branch 是否 taken。

对于 direct branch，如果 destination address 已编码在 program binary 中，无论是常量还是相对于 program counter 的常量偏移，都不需要进一步信息。Direct branch 是 RISC-V ISA 支持的唯一 branch 类型。

### 2.1.4 Interrupts and exceptions

Interrupt 是另一类 delta，通常相对于程序执行异步发生，而不是有意作为某条特定指令或事件的结果发生。Exception 可以同样理解，尽管它们通常能回溯到特定 instruction address。

decoder 通常不知道 interrupt 在指令序列中的什么位置发生，所以 trace 必须报告正常 program flow 停止的位置，并给出 asynchronous destination 的指示；这种指示可以简单到报告 exception type。当 interrupt 或 exception 发生时，之前退休的最后一条指令必须被 traced。随后还必须 trace 下一条有效 instruction address，也就是 trap handler 的第一条指令。

注意：并非所有 exception 和 interrupt 都会导致 trap。最明显的是，floating point exception 和 disabled interrupt 不会 trap。如果 exception 或 interrupt 不 trap，则 program counter 不改变。因此不需要 trace 所有 exception/interrupt，只需要 trace trap。本文档中，interrupt 和 exception 只有在导致 trap 被 taken 时才被 traced。

### 2.1.5 Synchronization

为了让 trace 具备鲁棒性，trace 中必须有规则的 synchronization points。Synchronization 通过发送完整值的 instruction address，并可能发送 context identifier 来完成。发送 synchronization 的原因也可能有助于 decoder 和 debugger。synchronization 频率是在鲁棒性与 trace bandwidth 之间的权衡。

instruction trace encoder 需要在以下情况下完全 synchronise：

- reset 后或从 halt resume 后 traced 的第一条指令；
- 任何时候，只要某条指令被 traced，而前一条指令没有被 traced；
- 如果该指令是 interrupt service routine 或 exception handler 的第一条指令；
- 在经过较长一段时间之后。

### 2.1.6 End of trace

如果 tracing 因任何原因停止，必须输出最后一条 traced instruction 的地址。

tracing 可能停止的例子包括：

- hart 可能被 halted，即进入 debug mode；
- hart 可能被 reset；
- encoding 可能停止，例如通过 Trace-off trigger，见 3.2.4；
- encoder 实现的任何 filtering capability 的 matching criteria 可能不再满足；
- encoder 可能被 disabled。

## 2.2 Optional and run-time configurable modes

instruction trace encoder 可以支持多种 tracing mode。为了保证 decoder 正确处理 incoming packets，需要通知它当前 active configuration。每当 encoder configuration 改变时，encoder 都会发出一个 packet 来报告该 configuration。

这类 mode 的常见例子如下：

- delta address mode：program counter discontinuity 被编码为差值，而不是 absolute address value。
- full address mode：program counter discontinuity 被编码为 absolute address value。
- implicit exception mode：假定 exception 的 destination address，即 exception trap 的地址，decoder 已知，因此不在 trace 中编码。
- sequentially inferable jump mode：可以通过考虑两条指令的组合效果来推断 indirect jump 的 target。
- implicit return mode：function call return 的 destination address 从 call stack 推导，因此不在 trace 中编码。
- branch prediction mode：由 encoder branch predictor 以及 decoder 中相同副本正确预测的 branch，不编码为 taken/non-taken，而编码为更高效的 branch count number。
- jump target cache mode：不报告 uninferable jump target 的地址，而是缓存近期 jump targets，并报告 cache entry index，从而提升效率。

mode 可以有关联参数；更多细节见 Table 7.1。除 delta address mode 必须支持外，所有 mode 都是可选的。

### 2.2.1 Delta address mode

相关参数：无。

在 delta address mode 中，地址编码为当前指令实际地址与此前包含地址的 packet 所报告指令实际地址之间的差值。该 differential encoding 比 full address 需要更少 bit，因此 trace compression 更高效。

### 2.2.2 Full address mode

相关参数：无。

在 full address mode 中，trace 中所有地址都被编码为 absolute address，而不是 differential form。这类编码效率总是较低，但对 software decoder developer 而言可以是有用的 debugging aid。

### 2.2.3 Implicit exception mode

相关参数：无。

RISC-V Privileged ISA specification 将 exception handler base address 存储在 `utvec/stvec/mtvec` CSR registers 中。在某些 RISC-V 实现中，较低地址位存储在 `ucause/scause/mcause` CSR registers 中。

默认情况下，当 exception 或 interrupt 发生时，`*tvec` 和 `*cause` 值都会被报告。implicit exception mode 会从 trace 中省略 `*tvec`，即 trap handler address，从而提升效率。

只有当 decoder 能仅根据 exception cause 推断 trap handler 的地址时，才能使用该 mode。

### 2.2.4 Sequentially inferable jump mode

相关参数：`sijump_p`。

默认情况下，indirect jump 的 target 总是被视为 uninferable PC discontinuity。不过，如果指定 jump target 的寄存器被加载为常量，则在某些条件下它可以被视为 inferable。hart 必须识别具有 sequentially inferable targets 的 jump，并把该信息单独提供给 encoder。是否把该 jump 作为 inferable 处理的最终决定必须由 encoder 作出。为了让 decoder 能推断 jump target，constant load 和 jump 都必须被 traced。关于 sequentially inferable jump 的构成细节，见 3.1.1。

### 2.2.5 Implicit return mode

相关参数：`call_counter_size_p`、`return_stack_size_p`、`itype_width_p`。

虽然 function return 通常是 indirect jump，但行为良好的程序会使用标准 calling convention 返回到调用该函数的程序位置。对于这些程序，即使没有明确通知 return 的 destination address，也可以确定 execution path。implicit return mode 可以显著提升 trace encoder efficiency。

只有当相关 call 已在较早 packet 中报告时，return 才能作为 inferable 处理。encoder 必须保证这一点。实现方法可以是使用 counter 跟踪正在 trace 的 nested calls 数量。counter 在 call 时递增，但 tail call 不递增；在 return 时递减。定义见 3.1.1。counter 不会 overflow 或 underflow，并且在发送 synchronization packet 时 reset 为 0。如果 count 非零，即相关 call 已经在较早 packet 中报告，则 return 将被视为 inferable，且不会生成 trace packet。

这种方案成本低，只要程序行为良好就能工作。encoder 不检查 return address 是否确实为相关 call 后续指令的地址。因此，任何修改 return address 的程序都不能使用该 mode 的这种最小实现进行 trace。

另一种做法是 encoder 维护 expected return addresses 的 stack，只有当实际 return address 与预测匹配时才把 return 视为 inferable。这对所有程序都是完全鲁棒的，但实现成本更高。在这种情况下，如果 return address 与预测不匹配，则必须通过 packet 显式报告，并同时报告当前 stack 上的 return address 数量。这保证 decoder 能确定正在报告哪个 return。

### 2.2.6 Branch prediction mode

相关参数：`bpred_size_p`。

如果没有 branch prediction，每个已执行 branch 的结果都会存储在 branch map 中：这是一个 bit vector，按时间顺序保存每个 branch 的 taken/non-taken 状态。

这种编码以每个 branch 1 bit 的代价已经很高效，但在某些情况下仍可能产生相对大量 trace packets。例如：

- 执行不包含 uninferable jump 的 tight loop。每次 loop iteration 都会向 branch map 添加一个 bit。
- 停留在 idle loop 中等待 interrupt。这会在实际上没有任何有趣事件发生时产生大量 trace。
- breakpoint，在某些实现中也会在 idle loop 中旋转。

通过在 encoder 中添加 branch predictor，可以获得显著编码效率提升。为了让 encoder 和 decoder 保持同步，decoder software 中需要实现行为完全相同的 predictor。

predictor 应包含 `2^bpred_size_p` 个 entry 的 lookup table。每个 entry 由 instruction address 的 bit `bpred_size_p:1` 索引；如果不支持 compressed instructions，则由 bit `bpred_size_p+1:2` 索引。每个 entry 包含 2-bit prediction state：

- `00`：predict not taken；如果 prediction fails，则转移到 `01`。
- `01`：predict not taken；如果 prediction succeeds，则转移到 `00`，否则转移到 `11`。
- `11`：predict taken；如果 prediction fails，则转移到 `10`。
- `10`：predict taken；如果 prediction succeeds，则转移到 `11`，否则转移到 `00`。

MSB 表示 predicted outcome，LSB 表示最近一次 actual outcome。prediction 必须失败两次，predicted value 才会改变。

发送 synchronization packet 时，lookup table entries 初始化为 `01`。

还应考虑其他 predictor，例如 gShare predictor，见 Hennessy & Patterson。需要进一步实验来确定不同 lookup table size 和 predictor algorithm 的收益。

### 2.2.7 Jump target cache mode

相关参数：`cache_size_p`。

默认情况下，uninferable jump 的 target address 会输出到 trace 中，通常采用 differential form。如果同一函数被重复调用，例如在 loop 中调用，则同一地址会反复输出。

通过向 encoder 添加 jump target cache 可以提升效率。为了让 encoder 和 decoder 保持同步，decoder software 中需要实现行为完全相同的 cache。即使是很小的 cache 也能带来显著改进。

cache 应包含 `2^cache_size_p` 个 entry，每个 entry 可包含一个 instruction address。它是 direct mapped，每个 entry 由 instruction address 的 bit `cache_size_p:1` 索引；如果不支持 compressed instructions，则由 bit `cache_size_p+1:2` 索引。

每个 uninferable jump target 首先与 cache 中相应 index 的 entry 比较。如果在 cache 中找到，则 trace index number，而不是 target address。如果未找到，则把该 index 的 entry 替换为当前 instruction address。

发送 synchronization packet 时，所有 cache entries 都 invalidated。
