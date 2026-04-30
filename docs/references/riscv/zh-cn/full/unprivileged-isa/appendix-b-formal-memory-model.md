# Appendix B Formal Memory Model Specifications, Version 0.1

为便于对 RVWMO 进行形式化分析，本附录使用不同工具和建模方法给出若干形式化版本。若这些模型之间存在差异，这些差异并非有意为之；预期是这些模型描述完全相同的合法行为集合。

本附录应视为 commentary。所有规范性内容都在 Chapter 14 以及 ISA 规范主体的其余部分中给出。当前已知的所有差异列在 Section A.7 中；其他任何差异都不是有意的。

## B.1 Formal Axiomatic Specification in Alloy

这里给出用 Alloy（`http://alloy.mit.edu`）表达的 RVWMO memory model 形式化规格。该模型可在线获得，地址为 `https://github.com/daniellustig/riscv-memory-model`。

在线材料还包含一些 litmus tests，以及一些示例，展示如何使用 Alloy 对 Section A.5 中的若干映射进行模型检查。

```alloy
// = RVWMO PPO =
// Preserved Program Order
fun ppo : Event -> Event {
  // same-address ordering
  po_loc :> Store
  + rdw
  + (AMO + StoreConditional) <: rfi

  // explicit synchronization
  + ppo_fence
  + Acquire <: ^po :> MemoryEvent
  + MemoryEvent <: ^po :> Release
  + RCsc <: ^po :> RCsc
  + pair

  // syntactic dependencies
  + addrdep
  + datadep
  + ctrldep :> Store

  // pipeline dependencies
  + (addrdep + datadep).rfi
  + addrdep.^po :> Store
}

// the global memory order respects preserved program order
fact { ppo in ^gmo }
```

图 B.1：用 Alloy 形式化的 RVWMO memory model（1/5：PPO）。这里的 `ppo` 函数把 Chapter 14 中的 preserved program order 规则编码为 `Event -> Event` 关系：同地址排序、显式同步、语法依赖和流水线依赖都被纳入其中。最后的 `fact` 要求 global memory order 尊重 `ppo`。

```alloy
// = RVWMO axioms =

// Load Value Axiom
fun candidates[r : MemoryEvent] : set MemoryEvent {
  (r.~^gmo & Store & same_addr[r]) // writes preceding r in gmo
  + (r.^~po & Store & same_addr[r]) // writes preceding r in po
}

fun latest_among[s : set Event] : Event { s - s.~^gmo }

pred LoadValue {
  all w : Store | all r : Load |
    w -> r in rf <=> w = latest_among[candidates[r]]
}

// Atomicity Axiom
pred Atomicity {
  all r : Store.~pair | // starting from the lr,
    no x : Store & same_addr[r] | // there is no store x to the same addr
      x not in same_hart[r]       // such that x is from a different hart,
      and x in r.~rf.^gmo         // x follows (the store r reads from) in gmo,
      and r.pair in x.^gmo        // and r follows x in gmo
}

// Progress Axiom implicit: Alloy only considers finite executions
pred RISCV_mm { LoadValue and Atomicity /* and Progress */ }
```

图 B.2：用 Alloy 形式化的 RVWMO memory model（2/5：Axioms）。`LoadValue` 按 Load Value Axiom 为每个 load 选择其读取的 store：候选 store 包括在 `gmo` 中先于该 load 的同地址 store，以及在 program order 中先于该 load 的同地址 store，然后选择其中按 `gmo` 最新的一个。`Atomicity` 对 `lr/sc` 配对施加限制：在 `lr` 所读 store 与对应 `sc` 之间，不能有来自其他 hart、同地址且按 `gmo` 介入的 store。Progress Axiom 在 Alloy 中隐含，因为 Alloy 只考虑有限执行。

```alloy
// Basic model of memory
sig Hart { // hardware thread
  start : one Event
}

sig Address {}

abstract sig Event {
  po : lone Event // program order
}

abstract sig MemoryEvent extends Event {
  address : one Address,
  acquireRCpc : lone MemoryEvent,
  acquireRCsc : lone MemoryEvent,
  releaseRCpc : lone MemoryEvent,
  releaseRCsc : lone MemoryEvent,
  addrdep : set MemoryEvent,
  ctrldep : set Event,
  datadep : set MemoryEvent,
  gmo : set MemoryEvent, // global memory order
  rf : set MemoryEvent
}

sig LoadNormal extends MemoryEvent {} // l{b|h|w|d}
sig LoadReserve extends MemoryEvent { // lr
  pair : lone StoreConditional
}
sig StoreNormal extends MemoryEvent {} // s{b|h|w|d}

// all StoreConditionals in the model are assumed to be successful
sig StoreConditional extends MemoryEvent {} // sc
sig AMO extends MemoryEvent {} // amo
sig NOP extends Event {}

fun Load : Event { LoadNormal + LoadReserve + AMO }
fun Store : Event { StoreNormal + StoreConditional + AMO }

sig Fence extends Event {
  pr : lone Fence, // opcode bit
  pw : lone Fence, // opcode bit
  sr : lone Fence, // opcode bit
  sw : lone Fence  // opcode bit
}

sig FenceTSO extends Fence {}

/* Alloy encoding detail: opcode bits are either set (encoded, e.g.,
 * as f.pr in iden) or unset (f.pr not in iden). The bits cannot be used for
 * anything else.
 */
fact { pr + pw + sr + sw in iden }

// likewise for ordering annotations
fact { acquireRCpc + acquireRCsc + releaseRCpc + releaseRCsc in iden }

// don't try to encode FenceTSO via pr/pw/sr/sw; just use it as-is
fact { no FenceTSO.(pr + pw + sr + sw) }
```

图 B.3：用 Alloy 形式化的 RVWMO memory model（3/5：memory 的基本模型）。该片段定义 hart、address、event、memory event、load/store/AMO/fence 等基本对象。`MemoryEvent` 携带地址、ordering annotation、依赖、`gmo` 和 `rf`。`Fence` 的 `pr/pw/sr/sw` 被建模为 opcode bit；`FenceTSO` 不通过这些 bit 编码，而作为独立类别使用。模型中所有 `StoreConditional` 都假定成功。

```alloy
// = Basic model rules =

// Ordering annotation groups
fun Acquire : MemoryEvent { MemoryEvent.acquireRCpc + MemoryEvent.acquireRCsc }
fun Release : MemoryEvent { MemoryEvent.releaseRCpc + MemoryEvent.releaseRCsc }
fun RCpc : MemoryEvent { MemoryEvent.acquireRCpc + MemoryEvent.releaseRCpc }
fun RCsc : MemoryEvent { MemoryEvent.acquireRCsc + MemoryEvent.releaseRCsc }

// There is no such thing as store-acquire or load-release, unless it's both
fact { Load & Release in Acquire }
fact { Store & Acquire in Release }

// FENCE PPO
fun FencePRSR : Fence { Fence.(pr & sr) }
fun FencePRSW : Fence { Fence.(pr & sw) }
fun FencePWSR : Fence { Fence.(pw & sr) }
fun FencePWSW : Fence { Fence.(pw & sw) }

fun ppo_fence : MemoryEvent -> MemoryEvent {
  (Load <: ^po :> FencePRSR).(^po :> Load)
  + (Load <: ^po :> FencePRSW).(^po :> Store)
  + (Store <: ^po :> FencePWSR).(^po :> Load)
  + (Store <: ^po :> FencePWSW).(^po :> Store)
  + (Load <: ^po :> FenceTSO).(^po :> MemoryEvent)
  + (Store <: ^po :> FenceTSO).(^po :> Store)
}

// auxiliary definitions
fun po_loc : Event -> Event { ^po & address.~address }
fun same_hart[e : Event] : set Event { e + e.^~po + e.^po }
fun same_addr[e : Event] : set Event { e.address.~address }

// initial stores
fun NonInit : set Event { Hart.start.*po }
fun Init : set Event { Event - NonInit }

fact { Init in StoreNormal }
fact { Init -> (MemoryEvent & NonInit) in ^gmo }
fact { all e : NonInit | one e.*~po.~start } // each event is in exactly one hart
fact { all a : Address | one Init & a.~address } // one init store per address
fact { no Init <: po and no po :> Init }
```

图 B.4：用 Alloy 形式化的 RVWMO memory model（4/5：基本模型规则）。该部分把 acquire/release、RCpc/RCsc 分组，定义 fence 对 `ppo` 的贡献，并定义 `po_loc`、`same_hart`、`same_addr` 等辅助关系。初始 store 被建模为每个地址恰好一个，且初始 store 在 `gmo` 中先于非初始 memory event；初始 store 不参与 `po`。

```alloy
// po
fact { acyclic[po] }

// gmo
fact { total[^gmo, MemoryEvent] } // gmo is a total order over all MemoryEvents

// rf
fact { rf.~rf in iden } // each read returns the value of only one write
fact { rf in Store <: address.~address :> Load }
fun rfi : MemoryEvent -> MemoryEvent { rf & (*po + *~po) }

// dep
fact { no StoreNormal <: (addrdep + ctrldep + datadep) }
fact { addrdep + ctrldep + datadep + pair in ^po }
fact { datadep in datadep :> Store }
fact { ctrldep.*po in ctrldep }
fact { no pair & (^po :> (LoadReserve + StoreConditional)).^po }
fact { StoreConditional in LoadReserve.pair } // assume all SCs succeed

// rdw
fun rdw : Event -> Event {
  (Load <: po_loc :> Load) // start with all same-address load-load pairs,
  - (~rf.rf)               // subtract pairs that read from the same store,
  - (po_loc.rfi)           // and subtract out "fri-rfi" patterns
}

// filter out redundant instances and/or visualizations
fact { no gmo & gmo.gmo } // keep the visualization uncluttered
fact { all a : Address | some a.~address }

// = Optional: opcode encoding restrictions =

// the list of blessed fences
fact { Fence in
  Fence.pr.sr
  + Fence.pw.sw
  + Fence.pr.pw.sw
  + Fence.pr.sr.sw
  + FenceTSO
  + Fence.pr.pw.sr.sw
}

pred restrict_to_current_encodings {
  no (LoadNormal + StoreNormal) & (Acquire + Release)
}

// = Alloy shortcuts =
pred acyclic[rel : Event -> Event] { no iden & ^rel }

pred total[rel : Event -> Event, bag : Event] {
  all disj e, e' : bag | e -> e' in rel + ~rel
  acyclic[rel]
}
```

图 B.5：用 Alloy 形式化的 RVWMO memory model（5/5：Auxiliaries）。这里规定 `po` 无环，`gmo` 是所有 `MemoryEvent` 上的全序，`rf` 每个读只来自一个写且地址匹配。依赖关系必须位于 `po` 之内；`rdw` 从同地址 load-load 对中排除读自同一 store 的情形和 `fri-rfi` 模式。可选的编码限制列出当前被认可的 fence 组合，并可禁止 normal load/store 携带 acquire/release annotation。最后给出 Alloy 中的 `acyclic` 和 `total` 简写谓词。

## B.2 Formal Axiomatic Specification in Herd

`herd` 工具以 memory model 和 litmus test 为输入，并在该 memory model 上模拟该测试的执行。Memory model 使用领域专用语言 Cat 编写。本节提供两个 RVWMO 的 Cat memory model。第一个模型（Figure B.7）在 Cat 模型能表达的范围内，尽量遵循 Chapter 14 以 global memory order 定义的 RVWMO。第二个模型（Figure B.8）是与之等价但更高效的、基于 partial order 的 RVWMO 模型。

`herd` 模拟器是 `diy` 工具套件的一部分；软件和文档见 `http://diy.inria.fr`。这些模型和更多材料可在线获得，地址为 `http://diy.inria.fr/cats7/riscv/`。

```cat
(***********)
(* Utilities *)
(***********)

(* All fence relations *)
let fence.r.r = [R]; fencerel(Fence.r.r); [R]
let fence.r.w = [R]; fencerel(Fence.r.w); [W]
let fence.r.rw = [R]; fencerel(Fence.r.rw); [M]
let fence.w.r = [W]; fencerel(Fence.w.r); [R]
let fence.w.w = [W]; fencerel(Fence.w.w); [W]
let fence.w.rw = [W]; fencerel(Fence.w.rw); [M]
let fence.rw.r = [M]; fencerel(Fence.rw.r); [R]
let fence.rw.w = [M]; fencerel(Fence.rw.w); [W]
let fence.rw.rw = [M]; fencerel(Fence.rw.rw); [M]

let fence.tso =
  let f = fencerel(Fence.tso) in
  ([W]; f; [W]) | ([R]; f; [M])

let fence =
  fence.r.r | fence.r.w | fence.r.rw |
  fence.w.r | fence.w.w | fence.w.rw |
  fence.rw.r | fence.rw.w | fence.rw.rw |
  fence.tso

(* Same address, no W to the same address in-between *)
let po-loc-no-w = po-loc \ (po-loc?; [W]; po-loc)

(* Read same write *)
let rsw = rf^-1; rf

(* Acquire, or stronger *)
let AQ = Acq | AcqRel

(* Release or stronger *)
and RL = Rel | AcqRel

(* All RCsc *)
let RCsc = Acq | Rel | AcqRel

(* Amo events are both R and W, relation rmw relates paired lr/sc *)
let AMO = R & W
let StCond = range(rmw)

(***********)
(* ppo rules *)
(***********)

(* Overlapping-Address Orderings *)
let r1 = [M]; po-loc; [W]
and r2 = ([R]; po-loc-no-w; [R]) \ rsw
and r3 = [AMO | StCond]; rfi; [R]

(* Explicit Synchronization *)
and r4 = fence
and r5 = [AQ]; po; [M]
and r6 = [M]; po; [RL]
and r7 = [RCsc]; po; [RCsc]
and r8 = rmw

(* Syntactic Dependencies *)
and r9 = [M]; addr; [M]
and r10 = [M]; data; [W]
and r11 = [M]; ctrl; [W]

(* Pipeline Dependencies *)
and r12 = [R]; (addr | data); [W]; rfi; [R]
and r13 = [R]; addr; [M]; po; [W]

let ppo = r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 | r9 | r10 | r11 | r12 | r13
```

图 B.6：`riscv-defs.cat`，preserved program order 的 herd 定义（1/3）。该 Cat 片段先定义所有 fence 关系、同地址且中间没有同地址写的 `po-loc-no-w`、读同一写的 `rsw`、acquire/release 分组、`AMO` 与 `StCond`，然后用规则 `r1` 到 `r13` 对应 Chapter 14 的 overlapping-address ordering、explicit synchronization、syntactic dependency 和 pipeline dependency，最后把这些规则合并为 `ppo`。

```cat
Total

(* Notice that herd has defined its own rf relation *)
(* Define ppo *)
include "riscv-defs.cat"

(********************************)
(* Generate global memory order *)
(********************************)

let gmo0 =
  (* precursor: i.e., build gmo as a total order that includes gmo0 *)
  loc & (W \ FW) * FW |       # Final write after any write to the same location
  ppo |                       # ppo compatible
  rfe                         # includes herd external rf (optimization)

(* Walk over all linear extensions of gmo0 *)
with gmo from linearisations(M \ IW, gmo0)

(* Add initial writes upfront -- convenient for computing rfGMO *)
let gmo = gmo | loc & IW * (M \ IW)

(*********)
(* Axioms *)
(*********)

(* Compute rf according to the load value axiom, aka rfGMO *)
let WR = loc & ([W]; (gmo | po); [R])
let rfGMO = WR \ (loc & ([W]; gmo); WR)

(* Check equality of herd rf and of rfGMO *)
empty (rf \ rfGMO) | (rfGMO \ rf) as RfCons

(* Atomicity axiom *)
let infloc = (gmo & loc)^-1
let inflocext = infloc & ext
let winside = (infloc; rmw; inflocext) & (infloc; rf; rmw; inflocext) & [W]
empty winside as Atomic
```

图 B.7：`riscv.cat`，RVWMO memory model 的 herd 版本（2/3）。该模型生成一个包含 `gmo0` 的 `gmo` 全序：`gmo0` 强制 final write、`ppo` 兼容性和外部 `rf` 优化。随后根据 Load Value Axiom 计算 `rfGMO`，并要求 herd 自身的 `rf` 与 `rfGMO` 相等；Atomicity Axiom 通过禁止 `winside` 非空来表达。

```cat
Partial

(***************)
(* Definitions *)
(***************)

(* Define ppo *)
include "riscv-defs.cat"

(* Compute coherence relation *)
include "cos-opt.cat"

(*********)
(* Axioms *)
(*********)

(* Sc per location *)
acyclic co | rf | fr | po-loc as Coherence

(* Main model axiom *)
acyclic co | rfe | fr | ppo as Model

(* Atomicity axiom *)
empty rmw & (fre; coe) as Atomic
```

图 B.8：`riscv.cat`，RVWMO memory model 的另一种 herd 表示（3/3）。该版本使用 partial order 风格，导入 `riscv-defs.cat` 与 `cos-opt.cat`。它通过每个地址上的 `co | rf | fr | po-loc` 无环性表达 coherence，通过 `co | rfe | fr | ppo` 无环性表达主模型约束，并用 `empty rmw & (fre; coe)` 表达 Atomicity Axiom。

## B.3 An Operational Memory Model

这是 RVWMO memory model 的另一种表示方式，采用 operational 风格。它的目标是允许与公理化表示完全相同的外延行为：对任意给定程序，当且仅当公理化表示允许某个执行时，该 operational 表示才允许该执行。

公理化表示被定义为完整 candidate executions 上的谓词。与之相对，这里的 operational 表示带有抽象微架构风格：它被表达为状态机，其中的状态是硬件机器状态的抽象表示，并且显式包含乱序和推测执行，但抽象掉更具体的微架构细节，例如 register renaming、store buffers、cache hierarchies、cache protocols 等。因此，它可以提供有用的直观理解。它还可以增量构造执行，使交互式和随机地探索更大示例的行为成为可能；公理化模型则需要完整的 candidate executions，然后在其上检查 axioms。

该 operational 表示覆盖 mixed-size execution，即可能存在不同 2 的幂字节大小且相互重叠的内存访问。Misaligned accesses 被拆分为单字节访问。

该 operational model 连同 RISC-V ISA 语义的一个片段（RV64I 和 A）已集成到 `rmem` 探索工具中（`https://github.com/rems-project/rmem`）。`rmem` 可以穷尽式、伪随机和交互式地探索 litmus tests（见 A.2）以及小型 ELF binaries。在 `rmem` 中，ISA 语义用 Sail 显式表达（Sail 语言见 `https://github.com/rems-project/sail`，RISC-V ISA 模型见 `https://github.com/rems-project/sail-riscv`），并发语义用 Lem 表达（Lem 语言见 `https://github.com/rems-project/lem`）。

`rmem` 有命令行界面和 Web 界面。Web 界面完全在客户端运行，并与 litmus test 库一起在线提供：`http://www.cl.cam.ac.uk/~pes20/rmem`。命令行界面比 Web 界面更快，尤其是在 exhaustive mode 下。

下面非正式介绍模型状态和转换。形式化模型的描述从下一小节开始。

术语：与公理化表示不同，这里每个 memory operation 要么是 load，要么是 store。因此，AMO 会产生两个不同的 memory operation：一个 load 和一个 store。当与“instruction”连用时，术语“load”和“store”指会产生此类 memory operation 的指令；因此二者都包含 AMO instructions。术语“acquire”指带 acquire-RCpc 或 acquire-RCsc annotation 的指令（或其 memory operation）。术语“release”指带 release-RCpc 或 release-RCsc annotation 的指令（或其 memory operation）。

**Model states** 一个 model state 由 shared memory 和一组 hart states 组成。

```text
Hart 0 ... Hart n
    \       /
  Shared Memory
```

Shared memory state 记录目前已经 propagate 的所有 memory store operations，并按它们 propagate 的顺序排列。为了效率也可以采用其他表示，但为了说明简单，这里保留这种表示。

每个 hart state 主要由一棵 instruction instances 树组成，其中一些实例已经 finished，另一些尚未 finished。尚未 finished 的 instruction instances 可以被 restart，例如当它们依赖一个乱序或推测 load，而该 load 后来证明不可靠时。

Conditional branch 和 indirect jump instructions 可能在 instruction tree 中有多个后继。当这类指令 finished 时，未被采用的替代路径会连同其下方 instruction instances 子树一起被丢弃。

Instruction tree 中每个 instruction instance 都有一个 state，其中包含 intra-instruction semantics（该指令的 ISA pseudocode）的 execution state。该模型使用 Sail 中的 intra-instruction semantics 形式化。可以把一条指令的 execution state 理解为 pseudocode control state、pseudocode call stack 和局部变量值的表示。

Instruction instance state 还包括关于该实例的 memory 与 register footprints、register reads 与 writes、memory operations、是否 finished 等信息。

**Model transitions** 对任意 model state，该模型定义一组 allowed transitions，其中每个 transition 都是到一个新的 abstract machine state 的单个 atomic step。一条指令的执行通常会涉及许多 transitions，并且这些 transitions 可以在 operational-model execution 中与来自其他指令的 transitions 交错。每个 transition 都来自单个 instruction instance；它会改变该实例的 state，也可能依赖或改变该 hart state 的其余部分和 shared memory state，但不依赖其他 hart states，也不会改变其他 hart states。以下先介绍 transitions；Section B.3.5 会为每个 transition 给出 precondition 和 post-transition model state 的构造。

适用于所有指令的 transitions：

- **Fetch instruction**：该 transition 表示获取并解码一个新的 instruction instance，作为先前已获取 instruction instance（或 initial fetch address）的 program order successor。

  模型假定 instruction memory 固定；它不描述 self-modifying code 的行为。特别地，Fetch instruction transition 不会生成 memory load operations，shared memory 也不参与该 transition。相反，模型依赖一个外部 oracle：给定一个 memory location 时，该 oracle 提供 opcode。

- **Register write**：写入一个 register value。

- **Register read**：从最近的 program-order-predecessor instruction instance 读取 register value，该前序实例写入该 register。

- **Pseudocode internal step**：覆盖 pseudocode 内部计算，例如 arithmetic、function calls 等。

- **Finish instruction**：到此时，instruction pseudocode 已完成，该指令不能再被 restart，memory accesses 不能再被丢弃，并且所有 memory effects 都已经发生。对 conditional branch 和 indirect jump instructions，从并非写入 `pc` register 的地址获取的任何 program order successors，连同其下方 instruction instances 子树都会被丢弃。

特定于 load instructions 的 transitions：

- **Initiate memory load operations**：此时 load instruction 的 memory footprint 暂时已知（若较早指令 restart，它可能改变），它的各个 memory load operations 可以开始被满足。

- **Satisfy memory load operation by forwarding from unpropagated stores**：通过从 program-order-previous memory store operations 转发，部分或完全满足单个 memory load operation。

- **Satisfy memory load operation from memory**：从 memory 完全满足单个 memory load operation 仍未满足的 slices。

- **Complete load operations**：此时该指令的所有 memory load operations 都已经被完全满足，instruction pseudocode 可以继续执行。Load instruction 在 Finish instruction transition 前都可能被 restart。不过，在某些条件下，即使 load instruction 尚未 finished，模型也可能把它视为 non-restartable（例如见 Propagate store operation）。

特定于 store instructions 的 transitions：

- **Initiate memory store operation footprints**：此时 store 的 memory footprint 暂时已知。

- **Instantiate memory store operation values**：此时 memory store operations 已有其值，program-order-successor memory load operations 可以通过从它们转发而被满足。

- **Commit store instruction**：此时 store operations 保证会发生（该指令不能再被 restart 或丢弃），并且它们可以开始 propagate 到 memory。

- **Propagate store operation**：把单个 memory store operation propagate 到 memory。

- **Complete store operations**：此时该指令的所有 memory store operations 都已 propagate 到 memory，instruction pseudocode 可以继续执行。

特定于 `sc` instructions 的 transitions：

- **Early sc fail**：使 `sc` 失败，原因可以是自发失败，也可以是因为它没有与一个 program-order-previous `lr` 配对。

- **Paired sc**：该 transition 表示 `sc` 与一个 `lr` 配对，并且可能成功。

- **Commit and propagate store operation of an sc**：这是 Commit store instruction 与 Propagate store operation 的 atomic execution；只有当 `lr` 所读 store 尚未被覆盖时才启用。

- **Late sc fail**：使 `sc` 失败，原因可以是自发失败，也可以是因为 `lr` 所读 store 已被覆盖。

特定于 AMO instructions 的 transitions：

- **Satisfy, commit and propagate operations of an AMO**：这是满足 load operation、执行所需算术并 propagate store operation 所需所有 transitions 的 atomic execution。

特定于 fence instructions 的 transitions：

- **Commit fence**

标记为 `◦` 的 transitions 在其 precondition 满足后总是可以 eager 地执行，而不会排除其他行为；标记为 `•` 的 transitions 则不能。虽然 Fetch instruction 标记为 `•`，只要不是无限多次执行，也可以 eager 地执行。

在上述 transitions 之前、之间和之后，都可以出现任意数量的 Pseudocode internal step transitions。此外，在获取下一程序位置的指令之前，总会有一个 Fetch instruction transition 可用。

至此，operational model 的非正式描述结束。以下各节描述形式化 operational model。

### B.3.1 Intra-instruction Pseudocode Execution

每个 instruction instance 的 intra-instruction semantics 被表达为状态机，本质上是在运行 instruction pseudocode。给定一个 pseudocode execution state，它计算下一个 state。多数 states 标识一个 pending memory 或 register operation，这是 pseudocode 请求 memory model 执行的操作。States 如下（这是 tagged union；tag 在原文中以 small-caps 表示）：

- `Load mem(kind, address, size, load continuation)` - memory load operation
- `Early sc fail(res continuation)` - 允许 `sc` early fail
- `Store ea(kind, address, size, next state)` - memory store effective address
- `Store memv(mem value, store continuation)` - memory store value
- `Fence(kind, next state)` - fence
- `Read reg(reg name, read continuation)` - register read
- `Write reg(reg name, reg value, next state)` - register write
- `Internal(next state)` - pseudocode internal step
- `Done` - pseudocode 结束

这里：

- `mem value` 和 `reg value` 是 byte lists；
- `address` 是 XLEN 位整数；
- 对 load/store，`kind` 标识它是否为 `lr/sc`、acquire-RCpc/release-RCpc、acquire-RCsc/release-RCsc、acquire-release-RCsc；
- 对 fence，`kind` 标识它是 normal 还是 TSO，并且对 normal fences，还标识 predecessor 和 successor ordering bits；
- `reg name` 标识一个 register 及其一个 slice（起始和结束 bit indices）；
- continuations 描述 instruction instance 在 surrounding memory model 可能提供的每个值下如何继续：`load continuation` 和 `read continuation` 分别接收从 memory loaded 的值和从前一个 register write read 的值；`store continuation` 对失败的 `sc` 接收 `false`，其他所有情形接收 `true`；`res continuation` 在 `sc` 失败时接收 `false`，否则接收 `true`。

例如，给定 load instruction `lw x1,0(x2)`，一次执行通常如下。Initial execution state 会从给定 opcode 的 pseudocode 计算出来。可以预期它是 `Read reg(x2, read continuation)`。把 register `x2` 最近写入的值提供给 `read continuation`（若需要，instruction semantics 会阻塞直到 register value 可用），假设该值为 `0x4000`，则 `read continuation` 返回 `Load mem(plain load, 0x4000, 4, load continuation)`。把从 memory location `0x4000` loaded 的 4-byte value 提供给 `load continuation`，假设该值为 `0x42`，则 `load continuation` 返回 `Write reg(x1, 0x42, Done)`。在上述 states 之前和之间，可能出现许多 `Internal(next state)` states。

注意，写入 memory 被拆成两步：`Store ea` 和 `Store memv`。第一步使 store 的 memory footprint 暂时已知；第二步加入要存储的值。模型在 pseudocode 中保证二者配对（`Store ea` 后跟 `Store memv`），但它们之间可以有其他 steps。

`Store ea` 可以在要存储的值确定之前发生，这是可观察的。例如，为使 operational model 允许 litmus test `LB+fence.r.rw+data-po`（RVWMO 也允许它），Hart 1 中第一个 store 必须在其值确定前执行 `Store ea` step，这样第二个 store 才能看到它面向一个不重叠的 memory footprint，从而允许第二个 store 乱序 commit 且不违反 coherence。

每条指令的 pseudocode 最多执行一个 store 或一个 load；AMO 除外，AMO 恰好执行一个 load 和一个 store。随后，hart semantics 会把这些 memory accesses 拆分成架构原子单元（见下面的 Initiate memory load operations 和 Initiate memory store operation footprints）。

非正式地，一个 register read 的每个 bit 应该由 program order 中最近、能够写入该 bit 的 instruction instance 的 register write 来满足；如果没有这样的 write，则来自 hart 的 initial register state。因此，了解每个 instruction instance 的 register write footprint 至关重要；该 footprint 在 instruction instance 创建时计算（见下面 Fetch instruction 的动作）。模型在 pseudocode 中保证每条指令对每个 register bit 最多执行一次 register write，并且不会尝试读取自己刚写入的 register value。

模型中的 data-flow dependencies（address 和 data）源于如下事实：每个 register read 必须等待相应 register write 被执行，如上所述。

### B.3.2 Instruction Instance State

每个 instruction instance `i` 的 state 包括：

- `program loc`：该指令被 fetch 的 memory address；
- `instruction kind`：标识这是 load、store、AMO、fence、branch/jump，还是“simple” instruction（这也包括一种类似于 pseudocode execution states 中描述的 `kind`）；
- `src regs`：source `reg names` 集合（包括 system registers），由该指令的 pseudocode 静态确定；
- `dst regs`：destination `reg names`（包括 system registers），由该指令的 pseudocode 静态确定；
- `pseudocode state`（有时简称 `state`）：以下三者之一（这是 tagged union；tag 在原文中以 small-caps 表示）：
  - `Plain(isa state)` - 准备进行 pseudocode transition
  - `Pending mem loads(load continuation)` - 请求 memory load operation(s)
  - `Pending mem stores(store continuation)` - 请求 memory store operation(s)
- `reg reads`：该实例已经执行的 register reads；对每个 read，记录它从哪些 register write slices 读得；
- `reg writes`：该实例已经执行的 register writes；
- `mem loads`：一组 memory load operations；对每个 operation，记录尚未满足的 slices（尚未满足的 byte indices），并且对已满足 slices，记录满足它的 store slices（每个 store slice 由一个 memory store operation 和其 byte indices 子集组成）；
- `mem stores`：一组 memory store operations；对每个 operation，记录一个 flag，表示它是否已经 propagated（传递到 shared memory）；
- 记录该实例是否 committed、finished 等的信息。

每个 memory load operation 包含一个 memory footprint（address 和 size）。每个 memory store operation 包含一个 memory footprint，并且在可用时包含一个 value。

如果一个 load instruction instance 有非空的 `mem loads`，且所有 load operations 都已 satisfied（即没有 unsatisfied load slices），则称它 entirely satisfied。

非正式地，如果某个 instruction instance 的 source registers 所依赖的 load（以及 `sc`）instructions 已经 finished，则称该实例具有 fully determined data。类似地，如果其 memory operation address register 所依赖的 load（以及 `sc`）instructions 已经 finished，则称该实例具有 fully determined memory footprint。形式化地，先定义 fully determined register write 的概念：instruction instance `i` 的 `reg writes` 中的 register write `w`，若满足以下条件之一，则称为 fully determined：

1. `i` 已经 finished；或
2. `w` 写入的值不受 `i` 执行的 memory operation 影响（即不受从 memory loaded 的值或 `sc` 结果影响），并且对 `i` 已执行且影响 `w` 的每个 register read，`i` 所读取的 register write 是 fully determined（或 `i` 从 initial register state 读取）。

现在，若对来自 `reg reads` 的每个 register read `r`，`r` 所读的 register writes 都 fully determined，则称 instruction instance `i` 具有 fully determined data。若对来自 `reg reads`、且流入 `i` 的 memory operation address 的每个 register read `r`，`r` 所读的 register writes 都 fully determined，则称 instruction instance `i` 具有 fully determined memory footprint。

`rmem` 工具会为每个 register write 记录一个集合：在执行该 write 时，该指令已经从其他指令读取过的 register writes 集合。通过谨慎安排该工具所覆盖指令的 pseudocode，可以使该集合恰好等于该 write 所依赖的 register writes 集合。

### B.3.3 Hart State

单个 hart 的 model state 包括：

- `hart id`：该 hart 的唯一标识符；
- `initial register state`：每个 register 的 initial register value；
- `initial fetch address`：initial instruction fetch address；
- `instruction tree`：按 program order 排列的一棵 instruction instances 树，包含已经 fetched 且未被 discarded 的实例。

### B.3.4 Shared Memory State

Shared memory 的 model state 包含一个 memory store operations 列表，按它们 propagate 到 shared memory 的顺序排列。

当 store operation propagate 到 shared memory 时，它只是被加入该列表末尾。当 load operation 从 memory satisfied 时，对该 load operation 的每个 byte，返回最近的相应 store slice。

在多数用途下，把 shared memory 想象为一个 array 会更简单，也就是从 memory locations 到 memory store operation slices 的 map，其中每个 memory location 都映射到对该 location 最近的 memory store operation 的 one-byte slice。然而，这个抽象不足以正确处理 `sc` instruction。RVWMO Atomicity Axiom 允许与 `sc` 属于同一 hart 的 store operations 介入 `sc` 的 store operation 与配对 `lr` 所读 store operations 之间。为了允许这种 store operations 介入、并禁止其他 store operations 介入，array 抽象必须扩展以记录更多信息。这里使用 list，因为它非常简单；但更高效、更可扩展的实现很可能应使用更好的表示。

### B.3.5 Transitions

以下每个段落描述一种 system transition。描述先给出当前 system state 上的条件。只有满足该条件时，该 transition 才能在当前 state 中发生。条件之后给出 action；当 transition 发生时，该 action 被应用到当前 state，以生成新的 system state。

**Fetch instruction** instruction instance `i` 的一个可能 program-order-successor 可以从 address `loc` fetched，如果：

1. 它尚未被 fetched，也就是说，hart 的 instruction tree 中 `i` 的 immediate successors 没有来自 `loc` 的实例；并且
2. 如果 `i` 的 pseudocode 已经写入一个地址 `topc`，则 `loc` 必须是该地址；否则 `loc` 为：
   - 对 conditional branch，为 successor address 或 branch target address；
   - 对 direct jump and link instruction（`jal`），为 target address；
   - 对 indirect jump instruction（`jalr`），为任意地址；
   - 对其他任何指令，为 `i.program loc + 4`。

Action：为 program memory 中位于 `loc` 的指令构造一个 freshly initialized instruction instance `i'`，其 state 为 `Plain(isa state)`；该 state 从 instruction pseudocode 计算，包括 pseudocode 中可用的静态信息，例如 instruction kind、`src regs` 和 `dst regs`。然后把 `i'` 加入 hart 的 instruction tree，作为 `i` 的 successor。

可能的下一个 fetch addresses（`loc`）在 fetch `i` 之后立即可用，模型不需要等待 pseudocode 写入 `pc`；这允许乱序执行，以及越过 conditional branches 和 jumps 的推测执行。对大多数指令，这些地址很容易从 instruction pseudocode 获得。唯一例外是 indirect jump instruction（`jalr`），其地址依赖某个 register 中保存的值。原则上，数学模型应允许在这里推测任意地址。`rmem` 工具中的 exhaustive search 通过多次运行 exhaustive search 来处理这一点，并为每个 indirect jump 使用不断增长的 possible next fetch addresses 集合。初始搜索使用空集合，因此在 indirect jump instruction 之后不会 fetch，直到该指令的 pseudocode 写入 `pc`，然后用该值获取下一条指令。在开始下一轮 exhaustive search 前，对每个 indirect jump（按 code location 分组），收集它在上一轮搜索所有 executions 中写入 `pc` 的值集合，并把它用作该指令的 possible next fetch addresses。当不再检测到新的 fetch addresses 时，该过程终止。

**Initiate memory load operations** 处于 `Plain(Load mem(kind, address, size, load continuation))` state 的 instruction instance `i` 总是可以 initiate 对应的 memory load operations。

Action：

1. 构造适当的 memory load operations `mlos`：
   - 若 `address` 按 `size` 对齐，则 `mlos` 是一个从 `address` 开始、大小为 `size` bytes 的 memory load operation；
   - 否则，`mlos` 是 `size` 个 memory load operations 的集合，每个大小为 one byte，地址为 `address ... address + size - 1`。
2. 把 `i` 的 `mem loads` 设置为 `mlos`；
3. 把 `i` 的 state 更新为 `Pending mem loads(load continuation)`。

Section 14.1 说 misaligned memory accesses 可以按任意粒度分解。这里把它们分解为 one-byte accesses，因为该粒度涵盖所有其他粒度。

**Satisfy memory load operation by forwarding from unpropagated stores** 对处于 `Pending mem loads(load continuation)` state 的 non-AMO load instruction instance `i`，以及 `i.mem loads` 中有 unsatisfied slices 的 memory load operation `mlo`，可以通过从 program-order-before `i` 的 store instruction instances 中尚未 propagated 的 memory store operations 转发，部分或完全满足该 memory load operation，如果：

1. 所有 program-order-previous 且设置了 `.sr` 和 `.pw` 的 fence instructions 都已 finished；
2. 对每个 program-order-previous fence instruction `f`，若设置了 `.sr` 和 `.pr`，且未设置 `.pw`，并且 `f` 尚未 finished，则所有 program-order-before `f` 的 load instructions 都已 entirely satisfied；
3. 对每个尚未 finished 的 program-order-previous `fence.tso` instruction `f`，所有 program-order-before `f` 的 load instructions 都已 entirely satisfied；
4. 若 `i` 是 load-acquire-RCsc，则所有 program-order-previous store-releases-RCsc 都已 finished；
5. 若 `i` 是 load-acquire-release，则所有 program-order-previous instructions 都已 finished；
6. 所有尚未 finished 的 program-order-previous load-acquire instructions 都已 entirely satisfied；
7. 所有 program-order-previous store-acquire-release instructions 都已 finished。

令 `msoss` 为所有 memory store operation slices 的集合；这些 slices 来自 non-`sc` store instruction instances，且这些 store instruction instances program-order-before `i`、已经计算出要存储的值、与 `mlo` 的 unsatisfied slices 重叠，并且没有被介入的 store operations 或被介入 load 读取的 store operations 取代。最后这个条件要求，对 `msoss` 中来自 instruction `i'` 的每个 memory store operation slice `msos`：

- 不存在 program-order-between `i` 和 `i'`、且其 memory store operation 与 `msos` 重叠的 store instruction；
- 不存在 program-order-between `i` 和 `i'`、且从另一个 hart 的重叠 memory store operation slice satisfied 的 load instruction。

Action：

1. 更新 `i.mem loads`，以表示 `mlo` 已由 `msoss` satisfied；
2. restart 由于这次操作而违反 coherence 的任何 speculative instructions。也就是说，对每个尚未 finished、且为 `i` 的 program-order-successor 的 instruction `i'`，以及 `i'` 中由 `msoss'` satisfied 的每个 memory load operation `mlo'`，若存在 `msoss'` 中的 memory store operation slice `msos'`，并且存在来自 `msoss` 中不同 memory store operation 的重叠 memory store operation slice，且 `msos'` 不是来自 `i` 的 program-order-successor 的指令，则 restart `i'` 及其 restart-dependents。

其中，instruction `j` 的 restart-dependents 为：

- 对 `j` 的 register write 有 data-flow dependency 的 program-order-successors；
- 有 memory load operation 从 `j` 的 memory store operation 读取（通过 forwarding）的 program-order-successors；
- 若 `j` 是 load-acquire，则为 `j` 的所有 program-order-successors；
- 若 `j` 是 load，则对每个设置了 `.sr` 和 `.pr`、且未设置 `.pw`、并且是 `j` 的 program-order-successor 的 fence `f`，包括所有作为 `f` 的 program-order-successors 的 load instructions；
- 若 `j` 是 load，则对每个作为 `j` 的 program-order-successor 的 `fence.tso` `f`，包括所有作为 `f` 的 program-order-successors 的 load instructions；
- 递归地，包括上述所有 instruction instances 的所有 restart-dependents。

把 memory store operations forward 到一个 memory load 时，可能只满足该 load 的某些 slices，留下其他 slices 尚未 satisfied。

在执行上述 transition 时尚不可用的 program-order-previous store operation，一旦变得可用，可能使 `msoss` 暂时不可靠（违反 coherence）。该 store 会阻止该 load finished（见 Finish instruction），并在该 store operation propagated 时导致它 restart（见 Propagate store operation）。

上述 transition 条件的一个结果是：store-release-RCsc memory store operations 不能 forward 到 load-acquire-RCsc instructions。`msoss` 不包含来自 finished stores 的 memory store operations（因为它们必然是 propagated memory store operations），而上述条件要求当 load 是 acquire-RCsc 时，所有 program-order-previous store-releases-RCsc 都已 finished。

**Satisfy memory load operation from memory** 对 non-AMO load instruction 的 instruction instance `i`，或在 “Satisfy, commit and propagate operations of an AMO” transition 上下文中的 AMO instruction，只要 Satisfy memory load operation by forwarding from unpropagated stores 的所有条件都满足，`i.mem loads` 中任意有 unsatisfied slices 的 memory load operation `mlo` 都可以从 memory satisfied。Action：令 `msoss` 为来自 memory、覆盖 `mlo` unsatisfied slices 的 memory store operation slices，并应用 Satisfy memory load operation by forwarding from unpropagated stores 的 action。

注意，Satisfy memory load operation by forwarding from unpropagated stores 可能会留下 memory load operation 的一些 slices 尚未 satisfied；这些 slices 必须通过再次执行该 transition，或执行 Satisfy memory load operation from memory 来满足。另一方面，Satisfy memory load operation from memory 总会满足该 memory load operation 的所有 unsatisfied slices。

**Complete load operations** 处于 `Pending mem loads(load continuation)` state 的 load instruction instance `i`，若 `i.mem loads` 的所有 memory load operations 都已 entirely satisfied（即没有 unsatisfied slices），则可以 completed（不要与 finished 混淆）。Action：把 `i` 的 state 更新为 `Plain(load continuation(mem value))`，其中 `mem value` 由满足 `i.mem loads` 的所有 memory store operation slices 组装而成。

**Early sc fail** 处于 `Plain(Early sc fail(res continuation))` state 的 `sc` instruction instance `i` 总是可以被使其 fail。Action：把 `i` 的 state 更新为 `Plain(res continuation(false))`。

**Paired sc** 处于 `Plain(Early sc fail(res continuation))` state 的 `sc` instruction instance `i`，若 `i` 与一个 `lr` 配对，则可以继续其可能成功的执行。Action：把 `i` 的 state 更新为 `Plain(res continuation(true))`。

**Initiate memory store operation footprints** 处于 `Plain(Store ea(kind, address, size, next state))` state 的 instruction instance `i` 总是可以宣布其 pending memory store operation footprint。Action：

1. 构造适当的 memory store operations `msos`（尚不包含 store value）：
   - 若 `address` 按 `size` 对齐，则 `msos` 是一个从 `address` 开始、大小为 `size` bytes 的 memory store operation；
   - 否则，`msos` 是 `size` 个 memory store operations 的集合，每个大小为 one byte，地址为 `address ... address + size - 1`。
2. 把 `i.mem stores` 设置为 `msos`；
3. 把 `i` 的 state 更新为 `Plain(next state)`。

注意，执行上述 transition 后，memory store operations 还没有其 values。把该 transition 与下面的 transition 分开很重要，因为这允许其他 program-order-successor store instructions 观察该指令的 memory footprint；如果它们不重叠，则可以尽早乱序 propagate（即在 data register value 可用之前）。

**Instantiate memory store operation values** 处于 `Plain(Store memv(mem value, store continuation))` state 的 instruction instance `i` 总是可以实例化 memory store operations `i.mem stores` 的 values。Action：

1. 在 memory store operations `i.mem stores` 之间拆分 `mem value`；
2. 把 `i` 的 state 更新为 `Pending mem stores(store continuation)`。

**Commit store instruction** 对尚未 committed 的 instruction instance `i`，如果它是 non-`sc` store instruction，或是在 “Commit and propagate store operation of an sc” transition 上下文中的 `sc` instruction，并且处于 `Pending mem stores(store continuation)` state，则当满足以下条件时可以 committed（不要与 propagated 混淆）：

1. `i` 具有 fully determined data；
2. 所有 program-order-previous conditional branch 和 indirect jump instructions 都已 finished；
3. 所有 program-order-previous 且设置了 `.sw` 的 fence instructions 都已 finished；
4. 所有 program-order-previous `fence.tso` instructions 都已 finished；
5. 所有 program-order-previous load-acquire instructions 都已 finished；
6. 所有 program-order-previous store-acquire-release instructions 都已 finished；
7. 若 `i` 是 store-release，则所有 program-order-previous instructions 都已 finished；
8. 所有 program-order-previous memory access instructions 都具有 fully determined memory footprint；
9. 所有 program-order-previous store instructions，失败的 `sc` 除外，都已 initiated，因此具有非空 `mem stores`；
10. 所有 program-order-previous load instructions 都已 initiated，因此具有非空 `mem loads`。

Action：记录 `i` 已 committed。

注意，若条件 8 满足，则条件 9 和 10 也满足，或会在执行一些 eager transitions 后满足。因此，要求它们不会加强模型。通过要求它们，模型保证 previous memory access instructions 已经执行足够 transitions，使它们的 memory operations 对 Propagate store operation 的条件检查可见；Propagate store operation 是该指令接下来会执行的 transition，这会让该条件更简单。

**Propagate store operation** 对处于 `Pending mem stores(store continuation)` state 的 committed instruction instance `i`，以及 `i.mem stores` 中尚未 propagated 的 memory store operation `mso`，如果满足以下条件，则 `mso` 可以 propagated：

1. program-order-previous store instructions 中所有与 `mso` 重叠的 memory store operations 都已经 propagated；
2. program-order-previous load instructions 中所有与 `mso` 重叠的 memory load operations 都已经 satisfied，并且这些 load instructions 是 non-restartable（见下方定义）；
3. 所有通过 forwarding `mso` 而 satisfied 的 memory load operations 都已 entirely satisfied。

其中，尚未 finished 的 instruction instance `j` 是 non-restartable，如果：

1. 不存在 store instruction `s` 和 `s` 的 unpropagated memory store operation `mso`，使得把 “Propagate store operation” transition 的 action 应用于 `mso` 会导致 `j` restart；
2. 不存在尚未 finished 的 load instruction `l` 和 `l` 的 memory load operation `mlo`，使得把 “Satisfy memory load operation by forwarding from unpropagated stores”/“Satisfy memory load operation from memory” transition 的 action 应用于 `mlo`（即使 `mlo` 已经 satisfied）会导致 `j` restart。

Action：

1. 用 `mso` 更新 shared memory state；
2. 更新 `i.mem stores`，表示 `mso` 已 propagated；
3. restart 由于这次操作而违反 coherence 的任何 speculative instructions。也就是说，对每个尚未 finished、且 program-order-after `i` 的 instruction `i'`，以及 `i'` 中由 `msoss'` satisfied 的每个 memory load operation `mlo'`，若存在 `msoss'` 中的 memory store operation slice `msos'`，它与 `mso` 重叠且不是来自 `mso`，并且 `msos'` 不是来自 `i` 的 program-order-successor，则 restart `i'` 及其 restart-dependents（见 Satisfy memory load operation by forwarding from unpropagated stores）。

**Commit and propagate store operation of an sc** 对 hart `h` 中尚未 committed、处于 `Pending mem stores(store continuation)` state 的 `sc` instruction instance `i`，若它有一个 paired `lr` `i'`，且 `i'` 已由一些 store slices `msoss` satisfied，则在满足以下条件时可以同时 committed 和 propagated：

1. `i'` 已 finished；
2. 每个 forwarded 到 `i'` 的 memory store operation 都已 propagated；
3. Commit store instruction 的条件满足；
4. Propagate store operation 的条件满足（注意，`sc` instruction 只能有一个 memory store operation）；
5. 对 `msoss` 中的每个 store slice `msos`，自 `msos` propagated 到 memory 以来，shared memory 中没有来自并非 `h` 的 hart 的 store 覆盖过 `msos`。

Action：

1. 应用 Commit store instruction 的 actions；
2. 应用 Propagate store operation 的 action。

**Late sc fail** 处于 `Pending mem stores(store continuation)` state、且尚未 propagated 其 memory store operation 的 `sc` instruction instance `i`，总是可以被使其 fail。Action：

1. 清空 `i.mem stores`；
2. 把 `i` 的 state 更新为 `Plain(store continuation(false))`。

为提高效率，`rmem` 工具仅在无法执行 Commit and propagate store operation of an sc transition 时允许该 transition。这不影响 allowed final states 的集合；但在交互式探索时，如果 `sc` 应失败，应使用 Early sc fail transition，而不是等待该 transition。

**Complete store operations** 处于 `Pending mem stores(store continuation)` state 的 store instruction instance `i`，若 `i.mem stores` 中所有 memory store operations 都已 propagated，则总是可以 completed（不要与 finished 混淆）。Action：把 `i` 的 state 更新为 `Plain(store continuation(true))`。

**Satisfy, commit and propagate operations of an AMO** 处于 `Pending mem loads(load continuation)` state 的 AMO instruction instance `i`，如果可以在没有介入 transitions 的情况下执行以下 transition 序列，则可以执行其 memory access：

1. Satisfy memory load operation from memory
2. Complete load operations
3. Pseudocode internal step（零次或多次）
4. Instantiate memory store operation values
5. Commit store instruction
6. Propagate store operation
7. Complete store operations

此外，在这些 transitions 之后，Finish instruction 的条件必须成立，但例外是无需要求 `i` 处于 `Plain(Done)` state。Action：按顺序执行上述 transition 序列（不包括 Finish instruction），中间没有任何介入 transitions。

注意，program-order-previous stores 不能 forward 到 AMO 的 load。这只是因为上述 transition 序列不包含 forwarding transition。但即使包含，该序列在尝试执行 Propagate store operation transition 时也会失败，因为该 transition 要求所有具有重叠 memory footprints 的 program-order-previous store operations 都已 propagated，而 forwarding 要求 store operation 尚未 propagated。

此外，AMO 的 store 也不能 forward 到 program-order-successor load。在执行上述 transition 之前，AMO 的 store operation 还没有其 value，因此不能 forward；在执行上述 transition 之后，该 store operation 已 propagated，因此也不能 forward。

**Commit fence** 处于 `Plain(Fence(kind, next state))` state 的 fence instruction instance `i`，若满足以下条件，则可以 committed：

1. 若 `i` 是 normal fence 且设置了 `.pr`，则所有 program-order-previous load instructions 都已 finished；
2. 若 `i` 是 normal fence 且设置了 `.pw`，则所有 program-order-previous store instructions 都已 finished；
3. 若 `i` 是 `fence.tso`，则所有 program-order-previous load 和 store instructions 都已 finished。

Action：

1. 记录 `i` 已 committed；
2. 把 `i` 的 state 更新为 `Plain(next state)`。

**Register read** 处于 `Plain(Read reg(reg name, read cont))` state 的 instruction instance `i`，若它需要读取的每个 instruction instance 都已经执行了预期的 `reg name` register write，则可以执行对 `reg name` 的 register read。

令 `read sources` 为：对 `reg name` 的每个 bit，program order 中最近且能够写入该 bit 的 instruction instance 对该 bit 的 write（若存在）。若不存在这样的 instruction，则 source 是来自 `initial register state` 的 initial register value。令 `reg value` 为从 `read sources` 组装出的值。Action：

1. 把 `reg name`、`read sources` 和 `reg value` 加入 `i.reg reads`；
2. 把 `i` 的 state 更新为 `Plain(read cont(reg value))`。

**Register write** 处于 `Plain(Write reg(reg name, reg value, next state))` state 的 instruction instance `i` 总是可以执行 `reg name` register write。Action：

1. 把 `reg name`、`deps` 和 `reg value` 加入 `i.reg writes`；
2. 把 `i` 的 state 更新为 `Plain(next state)`。

其中 `deps` 是一个 pair：第一部分是来自 `i.reg reads` 的所有 `read sources` 的集合；第二部分是一个 flag，当且仅当 `i` 是已经 entirely satisfied 的 load instruction instance 时为 true。

**Pseudocode internal step** 处于 `Plain(Internal(next state))` state 的 instruction instance `i` 总是可以执行该 pseudocode-internal step。Action：把 `i` 的 state 更新为 `Plain(next state)`。

**Finish instruction** 处于 `Plain(Done)` state 且尚未 finished 的 instruction instance `i`，若满足以下条件，则可以 finished：

1. 若 `i` 是 load instruction：
   1. 所有 program-order-previous load-acquire instructions 都已 finished；
   2. 所有 program-order-previous 且设置了 `.sr` 的 fence instructions 都已 finished；
   3. 对每个尚未 finished 的 program-order-previous `fence.tso` instruction `f`，所有 program-order-before `f` 的 load instructions 都已 finished；
   4. 保证 `i` 的 memory load operations 读取的值不会导致 coherence violations。也就是说，对任意 program-order-previous instruction instance `i'`，令 `cfp` 为以下两部分的 combined footprint：来自 program-order-between `i` 和 `i'` 的 store instructions 的 propagated memory store operations，以及来自 program-order-between `i` 和 `i'`（包括 `i'`）的 store instructions、且 forwarded 到 `i` 的 fixed memory store operations；再令 `cfp` 为 `i` 的 memory footprint 中该 combined footprint 的 complement。若 `cfp` 非空：
      1. `i'` 具有 fully determined memory footprint；
      2. `i'` 没有与 `cfp` 重叠的 unpropagated memory store operations；
      3. 若 `i'` 是 memory footprint 与 `cfp` 重叠的 load，则 `i'` 中所有与 `cfp` 重叠的 memory load operations 都已 satisfied，且 `i'` 是 non-restartable（如何判定 instruction 是否 non-restartable，见 Propagate store operation transition）。

   这里，如果 store instruction 具有 fully determined data，则称一个 memory store operation 是 fixed。

2. `i` 具有 fully determined data；
3. 若 `i` 不是 fence，则所有 program-order-previous conditional branch 和 indirect jump instructions 都已 finished。

Action：

1. 若 `i` 是 conditional branch 或 indirect jump instruction，则丢弃所有 untaken paths of execution，也就是从 instruction tree 中移除所有无法通过该 branch/jump 所采用路径到达的 instruction instances；
2. 记录该 instruction 已 finished，即把 `finished` 设置为 true。

### B.3.6 Limitations

- 该模型覆盖 user-level RV64I 和 RV64A。特别地，它不支持 misaligned atomics extension `Zam` 或 total store ordering extension `Ztso`。把模型适配到 RV32I/A 以及 G、Q 和 C extensions 应当很直接，但作者未尝试过。这主要涉及为这些指令编写 Sail code；对 concurrency model 即使需要修改，也应很少。
- 该模型只覆盖 normal memory accesses，不处理 I/O accesses。
- 该模型不覆盖 TLB-related effects。
- 该模型假定 instruction memory 固定。特别地，Fetch instruction transition 不会生成 memory load operations，shared memory 也不参与该 transition。相反，模型依赖一个外部 oracle：给定一个 memory location 时，该 oracle 提供 opcode。
- 该模型不覆盖 exceptions、traps 和 interrupts。
