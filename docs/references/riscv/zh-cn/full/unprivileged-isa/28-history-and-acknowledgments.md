# Chapter 28 History and Acknowledgments

## 28.1 "Why Develop a new ISA?" Rationale from Berkeley Group

我们开发 RISC-V，是为了支持自己在研究和教育中的需求。在这些场景中，我们团队特别关注研究思想的真实硬件实现（自本规范第一版以来，我们已经完成了十一次不同的 RISC-V silicon fabrications），也关注为学生提供可在课堂中探索的真实实现（RISC-V processor RTL designs 已经用于 Berkeley 多门本科和研究生课程）。在当前研究中，我们尤其关注向 specialized 和 heterogeneous accelerators 的转变；这种转变由传统 transistor scaling 终结后带来的功耗约束所驱动。我们希望有一个高度灵活且可扩展的 base ISA，围绕它构建我们的研究工作。

我们反复被问到一个问题：“为什么要开发一个新的 ISA？” 使用现有商业 ISA 最明显的好处，是可以在研究和教学中利用庞大且获得广泛支持的软件生态，包括开发工具和已移植的应用。其他好处还包括已有大量文档和教程示例。然而，我们在研究和教学中使用商业指令集的经验表明，这些好处在实践中较小，不能抵消其缺点：

- Commercial ISAs 是 proprietary 的。除作为开放 IEEE 标准的 SPARC V8 [2] 之外，大多数商业 ISA 的所有者都会谨慎保护其 intellectual property，并不欢迎自由可用的竞争性实现。对于只使用软件模拟器的学术研究和教学，这个问题较小；但对于希望共享真实 RTL 实现的团队，这是一个主要顾虑。对于不想信任少数商业 ISA 实现来源、却又被禁止创建自己的 clean room implementations 的实体，这也是一个主要顾虑。我们不能保证所有 RISC-V 实现都不会侵犯第三方专利，但我们可以保证，我们不会试图起诉 RISC-V implementor。
- Commercial ISAs 只在某些市场领域流行。写作时最明显的例子是，ARM 架构在 server 空间中支持并不好，而 Intel x86 架构（或事实上几乎任何其他架构）在 mobile 空间中支持并不好，虽然 Intel 和 ARM 都在尝试进入对方的市场分段。另一个例子是 ARC 和 Tensilica，它们提供 extensible cores，但专注于 embedded 空间。这种市场分割削弱了支持某个特定商业 ISA 的收益，因为实践中软件生态只存在于某些领域，而其他领域仍必须自行构建。
- Commercial ISAs 会兴衰更替。过去的研究基础设施曾围绕如今不再流行的商业 ISA（SPARC、MIPS）构建，甚至围绕已经不再生产的 ISA（Alpha）构建。这些 ISA 失去了活跃软件生态的收益，并且围绕 ISA 和支持工具残留的 intellectual property 问题，会干扰有兴趣的第三方继续支持该 ISA。开放 ISA 也可能失去流行度，但任何有兴趣的一方都可以继续使用和发展其生态。
- 流行商业 ISA 很复杂。主导商业 ISA（x86 和 ARM）在硬件中实现到能够支持常见软件栈和操作系统的程度都非常复杂。更糟糕的是，几乎所有复杂度都来自糟糕的、或至少已经过时的 ISA 设计决策，而不是来自真正提高效率的特性。
- Commercial ISAs 本身不足以启动应用。即使我们花力气实现一个商业 ISA，这也不足以运行该 ISA 的现有应用。大多数应用需要完整 ABI（application binary interface）才能运行，而不仅需要 user-level ISA。大多数 ABI 依赖 libraries，而 libraries 又依赖操作系统支持。要运行现有操作系统，需要实现 OS 预期的 supervisor-level ISA 和 device interfaces。这些内容通常远不如 user-level ISA 规定清楚，并且实现复杂得多。
- 流行商业 ISA 并非为 extensibility 而设计。主导商业 ISA 并不是特别面向 extensibility 设计的，因此随着指令集增长，它们增加了相当多的指令编码复杂度。Tensilica（被 Cadence 收购）和 ARC（被 Synopsys 收购）等公司围绕 extensibility 构建了 ISA 和 toolchains，但它们专注于 embedded applications，而不是 general-purpose computing systems。
- 修改过的商业 ISA 就是新的 ISA。我们的主要目标之一是支持 architecture research，包括重大 ISA extensions。即使是小扩展，也会削弱使用标准 ISA 的收益，因为编译器必须被修改，应用也必须从源代码重新构建才能使用该扩展。引入新 architectural state 的更大扩展还需要修改操作系统。最终，修改过的商业 ISA 变成一个新的 ISA，但仍携带 base ISA 的所有历史包袱。

我们的立场是，ISA 或许是计算系统中最重要的接口；如此重要的接口没有理由是 proprietary 的。主导商业 ISA 基于 30 多年前就已经广为人知的 instruction-set concepts。软件开发者应该能够面向开放标准硬件目标，商业处理器设计者则应在实现质量上竞争。

我们远不是第一个考虑适合硬件实现的开放 ISA 设计的人。我们也考虑过其他已有开放 ISA 设计，其中最接近我们目标的是 OpenRISC architecture [12]。我们出于若干技术原因决定不采用 OpenRISC ISA：

- OpenRISC 有 condition codes 和 branch delay slots，这会使更高性能实现复杂化。
- OpenRISC 使用固定 32 位编码和 16 位 immediates，这会排除更密集指令编码，并限制 ISA 后续扩展空间。
- OpenRISC 不支持 IEEE 754 floating-point standard 的 2008 修订版。
- 当我们开始时，OpenRISC 64 位设计尚未完成。

从一张白纸开始，我们能够设计一个满足所有目标的 ISA；当然，这花费的努力远超我们最初计划。我们现在已经投入大量工作来构建 RISC-V ISA 基础设施，包括文档、compiler tool chains、operating system ports、reference ISA simulators、FPGA implementations、高效 ASIC implementations、architecture test suites 和 teaching materials。自本手册上一版以来，RISC-V ISA 在 academia 和 industry 中都获得了相当多采用，我们也创建了 non-profit RISC-V Foundation 来保护和推广该标准。RISC-V Foundation 网站 `https://riscv.org` 包含 Foundation membership 和使用 RISC-V 的各种 open-source projects 的最新信息。

## 28.2 History from Revision 1.0 of ISA manual

RISC-V ISA 和 instruction-set manual 建立在若干早期项目之上。supervisor-level machine 的若干方面以及手册整体格式，可以追溯到 UC Berkeley 和 ICSI 于 1992 年开始的 T0（Torrent-0）vector microprocessor project。T0 是基于 MIPS-II ISA 的 vector processor，Krste Asanovic 是主要 architect 和 RTL designer，Brian Kingsbury 和 Bertrand Irrisou 是主要 VLSI implementors。ICSI 的 David Johnson 是 T0 ISA 设计（特别是 supervisor mode）和手册文本的主要贡献者。John Hauser 也对 T0 ISA 设计提供了大量反馈。

MIT 于 2000 年开始的 Scale（Software-Controlled Architecture for Low Energy）项目建立在 T0 项目基础设施之上，改进了 supervisor-level interface，并通过去除 branch delay slot 脱离了 MIPS scalar ISA。Ronny Krashinsky 和 Christopher Batten 是 MIT Scale Vector-Thread processor 的主要 architects，Mark Hampton 为 Scale 移植了基于 GCC 的 compiler infrastructure 和 tools。

T0 MIPS scalar processor specification（MIPS-6371）的轻度编辑版本，用于 2002 年秋季学期新版 MIT 6.371 Introduction to VLSI Systems 课程教学，讲师为 Chris Terman 和 Krste Asanovic。Chris Terman 贡献了该课程的大部分实验材料（没有 TA！）。6.371 课程演化为 MIT 的试验性 6.884 Complex Digital Design 课程，于 2005 年春季由 Arvind 和 Krste Asanovic 教授，后来成为常规春季课程 6.375。Scale 中基于 MIPS 的 scalar ISA 的精简版本被命名为 SMIPS，并用于 6.884/6.375。Christopher Batten 是这些课程早期版本的 TA，并围绕 SMIPS ISA 开发了大量文档和实验材料。这些 SMIPS 实验材料随后由 TA Yunsup Lee 为 UC Berkeley 2009 年秋季 CS250 VLSI Systems Design 课程改编和增强，该课程由 John Wawrzynek、Krste Asanovic 和 John Lazzaro 教授。

Maven（Malleable Array of Vector-thread ENgines）项目是第二代 vector-thread architecture。其设计由 Christopher Batten 领导，当时他从 2007 年夏季开始作为 Exchange Scholar 在 UC Berkeley。来自 Hitachi 的 visiting industrial fellow Hidetaka Aoki 对早期 Maven ISA 和 microarchitecture 设计提供了大量反馈。Maven 基础设施基于 Scale 基础设施，但 Maven ISA 进一步脱离 Scale 中定义的 MIPS ISA 变体，采用统一的 floating-point 和 integer register file。Maven 被设计为支持对 alternative data-parallel accelerators 的实验。Yunsup Lee 是各种 Maven vector units 的主要实现者，Rimas Avizienis 是各种 Maven scalar units 的主要实现者。Yunsup Lee 和 Christopher Batten 移植 GCC 以配合新的 Maven ISA。Christopher Celio 提供了 Maven 的传统 vector instruction set（“Flood”）变体的初始定义。

基于所有这些早期项目的经验，RISC-V ISA 定义于 2010 年夏季开始，Andrew Waterman、Yunsup Lee、Krste Asanovic 和 David Patterson 是主要 designers。RISC-V 32 位指令子集的初始版本用于 UC Berkeley 2010 年秋季 CS250 VLSI Systems Design 课程，Yunsup Lee 担任 TA。RISC-V 与早期受 MIPS 启发的设计彻底分离。John Hauser 对 floating-point ISA 定义作出贡献，包括 sign-injection instructions 和一种允许内部重编码 floating-point values 的寄存器编码方案。

## 28.3 History from Revision 2.0 of ISA manual

多个 RISC-V processors 的实现已经完成，包括若干 silicon fabrications，如表 28.1 所示。

表 28.1：Fabricated RISC-V testchips。

| Name | Tapeout Date | Process | ISA |
|---|---|---|---|
| Raven-1 | May 29, 2011 | ST 28nm FDSOI | `RV64G1_Xhwacha1` |
| EOS14 | April 1, 2012 | IBM 45nm SOI | `RV64G1p1_Xhwacha2` |
| EOS16 | August 17, 2012 | IBM 45nm SOI | `RV64G1p1_Xhwacha2` |
| Raven-2 | August 22, 2012 | ST 28nm FDSOI | `RV64G1p1_Xhwacha2` |
| EOS18 | February 6, 2013 | IBM 45nm SOI | `RV64G1p1_Xhwacha2` |
| EOS20 | July 3, 2013 | IBM 45nm SOI | `RV64G1p99_Xhwacha2` |
| Raven-3 | September 26, 2013 | ST 28nm SOI | `RV64G1p99_Xhwacha2` |
| EOS22 | March 7, 2014 | IBM 45nm SOI | `RV64G1p9999_Xhwacha3` |

最早 fabricat​​ed 的 RISC-V processors 用 Verilog 编写，并于 2011 年作为 Raven-1 testchip，在 ST 的预生产 28 nm FDSOI 工艺中制造。在 Krste Asanovic 指导下，Yunsup Lee 和 Andrew Waterman 开发了两个 cores，并一起 fabricated：1）一个带 error-detecting flip-flops 的 RV64 scalar core；2）一个附带 64-bit floating-point vector unit 的 RV64 core。第一个 microarchitecture 非正式地称为 “TrainWreck”，因为完成设计的时间很短，且 design libraries 还不成熟。

随后，在 Krste Asanovic 指导下，Andrew Waterman、Rimas Avizienis 和 Yunsup Lee 开发了一个干净的 in-order decoupled RV64 core microarchitecture，并延续铁路主题，将其 codename 为 “Rocket”，取自 George Stephenson 成功的蒸汽机车设计。Rocket 用 Chisel 编写，这是 UC Berkeley 开发的新硬件设计语言。Rocket 中使用的 IEEE floating-point units 由 John Hauser、Andrew Waterman 和 Brian Richards 开发。此后 Rocket 被进一步改进和发展，并在 28 nm FDSOI 中又 fabricated 两次（Raven-2、Raven-3），在 IBM 45 nm SOI technology 中为一个 photonics project fabricated 五次（EOS14、EOS16、EOS18、EOS20、EOS22）。相关工作仍在进行，以把 Rocket 设计作为 parameterized RISC-V processor generator 提供。

EOS14-EOS22 chips 包含早期版本的 Hwacha，这是一个 64-bit IEEE floating-point vector unit，由 Yunsup Lee、Andrew Waterman、Huy Vo、Albert Ou、Quan Nguyen 和 Stephen Twigg 开发，Krste Asanovic 指导。EOS16-EOS22 chips 包含双 cores 和由 Henry Cook、Andrew Waterman 开发、Krste Asanovic 指导的 cache-coherence protocol。EOS14 silicon 已成功运行在 1.25 GHz。EOS16 silicon 遭遇 IBM pad libraries 中的 bug。EOS18 和 EOS20 已成功运行在 1.35 GHz。

Raven testchips 的贡献者包括 Yunsup Lee、Andrew Waterman、Rimas Avizienis、Brian Zimmer、Jaehwa Kwak、Ruzica Jevtic、Milovan Blagojevic、Alberto Puggelli、Steven Bailey、Ben Keller、Pi-Feng Chiu、Brian Richards、Borivoje Nikolic 和 Krste Asanovic。

EOS testchips 的贡献者包括 Yunsup Lee、Rimas Avizienis、Andrew Waterman、Henry Cook、Huy Vo、Daiwei Li、Chen Sun、Albert Ou、Quan Nguyen、Stephen Twigg、Vladimir Stojanovic 和 Krste Asanovic。

Andrew Waterman 和 Yunsup Lee 开发了 C++ ISA simulator “Spike”，它在开发中用作 golden model；其名称来自庆祝美国横贯大陆铁路完工所用的 golden spike。Spike 已作为 BSD open-source project 提供。

Andrew Waterman 完成了一篇 Master's thesis，其中包含 RISC-V compressed instruction set 的初步设计 [22]。

多个 RISC-V 的 FPGA implementations 已经完成，主要作为 Par Lab project research retreats 的 integrated demos 的一部分。最大的 FPGA 设计有 3 个 cache-coherent RV64IMA processors，运行一个研究操作系统。FPGA implementations 的贡献者包括 Andrew Waterman、Yunsup Lee、Rimas Avizienis 和 Krste Asanovic。

RISC-V processors 已用于 UC Berkeley 的多门课程。Rocket 在 2011 年秋季 CS250 课程中作为 class projects 的基础使用，Brian Zimmer 担任 TA。2012 年春季本科 CS152 课程中，Christopher Celio 使用 Chisel 编写了一套教学用 RV32 processors，命名为 “Sodor”，取自 “Thomas the Tank Engine” 和朋友们居住的岛屿。该套件包括 microcoded core、unpipelined core，以及 2、3、5-stage pipelined cores，并以 BSD license 公开提供。该套件随后更新，并再次用于 2013 年春季 CS152，Yunsup Lee 担任 TA；以及 2014 年春季 CS152，Eric Love 担任 TA。Christopher Celio 还开发了一个称为 BOOM（Berkeley Out-of-Order Machine）的 out-of-order RV64 design，并带有 pipeline visualizations，该设计用于 CS152 课程。CS152 课程还使用了 Andrew Waterman 和 Henry Cook 开发的 cache-coherent versions of the Rocket core。

2013 年夏季，RoCC（Rocket Custom Coprocessor）interface 被定义出来，用于简化向 Rocket core 添加 custom accelerators。Rocket 和 RoCC interface 在 Jonathan Bachrach 教授的 2013 年秋季 CS250 VLSI 课程中被广泛使用，多个学生 accelerator projects 构建在 RoCC interface 之上。Hwacha vector unit 已被重写为 RoCC coprocessor。

2013 年春季，两名 Berkeley 本科生 Quan Nguyen 和 Albert Ou 成功把 Linux 移植到 RISC-V 上运行。

Colin Schmidt 于 2014 年 1 月成功完成 RISC-V 2.0 的 LLVM backend。

Bluespec 的 Darius Rad 于 2014 年 3 月为 GCC port 贡献了 soft-float ABI support。

John Hauser 贡献了 floating-point classification instructions 的定义。

我们知道还有若干其他 RISC-V core implementations，包括 Tommy Thorn 用 Verilog 编写的一个实现，以及 Rishiyur Nikhil 用 Bluespec 编写的一个实现。

### Acknowledgments

感谢 Christopher F. Batten、Preston Briggs、Christopher Celio、David Chisnall、Stefan Freudenberger、John Hauser、Ben Keller、Rishiyur Nikhil、Michael Taylor、Tommy Thorn 和 Robert Watson 对 ISA version 2.0 draft specification 提供评论。

## 28.4 History from Revision 2.1

自 2014 年 5 月冻结的 version 2.0 推出以来，RISC-V ISA 的采用速度非常快，活动之多已无法在这样一个简短历史章节中记录。也许最重要的单一事件是 non-profit RISC-V Foundation 于 2015 年 8 月成立。Foundation 现在将接管官方 RISC-V ISA standard 的 stewardship，官方网站 `riscv.org` 是获取 RISC-V standard 新闻和更新的最佳地点。

### Acknowledgments

感谢 Scott Beamer、Allen J. Baum、Christopher Celio、David Chisnall、Paul Clayton、Palmer Dabbelt、Jan Gray、Michael Hamburg 和 John Hauser 对 version 2.0 specification 提供评论。

## 28.5 History from Revision 2.2

### Acknowledgments

感谢 Jacob Bachmeyer、Alex Bradbury、David Horner、Stefan O'Rear 和 Joseph Myers 对 version 2.1 specification 提供评论。

## 28.6 History for Revision 2.3

RISC-V 的采用继续以极快速度推进。

John Hauser 和 Andrew Waterman 基于 Paolo Bonzini 的提案贡献了 hypervisor ISA extension。

Daniel Lustig、Arvind、Krste Asanovic、Shaked Flur、Paul Loewenstein、Yatin Manerkar、Luc Maranget、Margaret Martonosi、Vijayanand Nagarajan、Rishiyur Nikhil、Jonas Oberhauser、Christopher Pulte、Jose Renau、Peter Sewell、Susmit Sarkar、Caroline Trippel、Muralidaran Vijayaraghavan、Andrew Waterman、Derek Williams、Andrew Wright 和 Sizhuo Zhang 贡献了 memory consistency model。

## 28.7 Funding

RISC-V architecture 和 implementations 的开发部分由以下 sponsors 资助。

- Par Lab：研究由 Microsoft（Award #024263）和 Intel（Award #024894）资助，并由 U.C. Discovery（Award #DIG07-10227）提供 matching funding。额外支持来自 Par Lab affiliates Nokia、NVIDIA、Oracle 和 Samsung。
- Project Isis：DoE Award DE-SC0003624。
- ASPIRE Lab：DARPA PERFECT program，Award HR0011-12-2-0016。DARPA POEM program Award HR0011-11-C-0100。Center for Future Architectures Research（C-FAR），由 Semiconductor Research Corporation 资助的 STARnet center。额外支持来自 ASPIRE industrial sponsor Intel，以及 ASPIRE affiliates Google、Hewlett Packard Enterprise、Huawei、Nokia、NVIDIA、Oracle 和 Samsung。

本文内容不一定反映美国政府的立场或政策，也不应推断为任何官方认可。
