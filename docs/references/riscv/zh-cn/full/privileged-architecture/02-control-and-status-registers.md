# 第 2 章 Control and Status Registers (CSRs)

源范围：PDF 第 17-26 页；Chapter 2 Control and Status Registers (CSRs)。

> 说明：本文件为严格全文机器初译后术语保护稿；CSR 名、寄存器名、指令名、异常名、字段名按原文保留。

<!-- Source PDF page 17 -->


## 第2章
控制和状态寄存器 (CSRs)
SYSTEM 主操作码用于对 RISC-V ISA 中的所有特权指令进行编码。这些
可以分为两个主要类：原子读-修改-写控制类和状态类
寄存器（CSRs），以及所有其他特权指令。除了描述的用户级状态之外
在本手册的第一卷中，实现可能包含附加的 CSRs，可供某些人访问
使用用户级别手册中描述的 CSR 指令的权限级别的子集。在
本章，我们映射出CSR地址空间。以下章节描述了其功能
CSRs中的每一条根据特权级别，以及其他特权指令
通常与特定特权级别密切相关。请注意，虽然 CSRs 和
指令与一个特权级别相关联，它们也可以在所有更高的特权下访问
水平。


### 2.1 CSR 地址映射约定
标准 RISC-V ISA 为最多 4,096 个 CSR 预留了 12 位编码空间 (csr[11:0])。
按照惯例，CSR 地址（csr[11:8]）的高 4 位用于对读取和读取进行编码。
根据表 

### 2.1 所示的权限级别，CSRs 的写可访问性。前两位
(csr[11:10]) 指示寄存器是读/写（00、01 或 10）还是只读（11）。下一个
两位 (csr[9:8]) 编码可以访问 CSR 的最低特权级别。
CSR 地址约定使用 CSR 地址的高位来编码默认访问
特权。这简化了硬件中的错误检查并提供了更大的CSR空间，但是
确实限制了 CSRs 到地址空间的映射。
实现可能允许较高特权级别捕获较低特权级别允许的 CSR 访问，以允许拦截这些访问。这个改变应该是
对于权限较低的软件是透明的。
尝试访问不存在的 CSR 会引发非法指令异常。尝试访问
CSR 没有适当的权限级别或写入只读寄存器也会引发非法指令
例外情况。 A 读/写寄存器可能还包含一些只读位，在这种情况下
对只读位的写入将被忽略。
5

<!-- Source PDF page 18 -->
表 

### 2.1 还指出了在标准用途和自定义用途之间分配 CSR 地址的约定。
为自定义用途保留的 CSR 地址将不会被未来的标准扩展重新定义。
机器模式标准读写 CSRs 0x7A0–0x7BF 保留供调试系统使用。
其中CSRs，0x7A0–0x7AF可在机器模式下访问，而0x7B0–0x7BF仅可见
到调试模式。实现应该在机器模式访问上引发非法指令异常
到后一组寄存器。
有效的虚拟化要求尽可能多的指令在虚拟化环境中本地运行，而任何特权访问都会陷入虚拟机监视器[1]。 CSRs
在某些较低权限级别只读的文件将被隐藏到单独的 CSR 地址中，如果它们
以更高的权限级别进行读写。这可以避免捕获允许的低权限访问，同时仍然导致非法访问的陷阱。目前，柜台是唯一有阴影的
企业社会责任。


### 2.2 CSR 上市
表2.2~2.5列出了当前已分配CSR地址的CSRs。定时器、计数器和浮点 CSRs 是标准用户级 CSRs，以及附加的用户陷阱
由 N 扩展添加的寄存器。其他寄存器由特权代码使用，如上所述
在接下来的章节中。请注意，并非所有实现都需要所有寄存器。

<!-- Source PDF page 19 -->
CSR 地址十六进制使用和可访问性
[11:10] [9:8] [7:4]
用户 CSRs
00 00 XXXX 0x000-0x0FF 标准读/写
01 00 XXXX 0x400-0x4FF 标准读/写
10 00 XXXX 0x800-0x8FF 自定义读/写
11 00 0XXX 0xC00-0xC7F 标准只读
11 00 10XX 0xC80-0xCBF 标准只读
11 00 11XX 0xCC0-0xCFF 自定义只读
主管 CSRs
00 01 XXXX 0x100-0x1FF 标准读/写
01 01 0XXX 0x500-0x57F 标准读/写
01 01 10XX 0x580-0x5BF 标准读/写
01 01 11XX 0x5C0-0x5FF 自定义读/写
10 01 0XXX 0x900-0x97F 标准读/写
10 01 10XX 0x980-0x9BF 标准读/写
10 01 11XX 0x9C0-0x9FF 自定义读/写
11 01 0XXX 0xD00-0xD7F 标准只读
11 01 10XX 0xD80-0xDBF 标准只读
11 01 11XX 0xDC0-0xDFF 自定义只读
管理程序 CSRs
00 10 XXXX 0x200-0x2FF 标准读/写
01 10 0XXX 0x600-0x67F 标准读/写
01 10 10XX 0x680-0x6BF 标准读/写
01 10 11XX 0x6C0-0x6FF 自定义读/写
10 10 0XXX 0xA00-0xA7F 标准读/写
10 10 10XX 0xA80-0xABF 标准读/写
10 10 11XX 0xAC0-0xAFF 自定义读/写
11 10 0XXX 0xE00-0xE7F 标准只读
11 10 10XX 0xE80-0xEBF 标准只读
11 10 11XX 0xEC0-0xEFF 自定义只读
机器CSRs
00 11 XXXX 0x300-0x3FF 标准读/写
01 11 0XXX 0x700-0x77F 标准读/写
01 11 100X 0x780-0x79F 标准读/写
01 11 1010 0x7A0-0x7AF 标准读/写调试 CSRs
01 11 1011 0x7B0-0x7BF 仅调试模式 CSRs
01 11 11XX 0x7C0-0x7FF 自定义读/写
10 11 0XXX 0xB00-0xB7F 标准读/写
10 11 10XX 0xB80-0xBBF 标准读/写
10 11 11XX 0xBC0-0xBFF 自定义读/写
11 11 0XXX 0xF00-0xF7F 标准只读
11 11 10XX 0xF80-0xFBF 标准只读
11 11 11XX 0xFC0-0xFFF 自定义只读
表 2.1：RISC-V CSR 地址范围的分配。

<!-- Source PDF page 20 -->
号码 权限名称 说明
用户陷阱设置
0x000 URW ustatus 用户状态寄存器。
0x004 URW uie 用户中断允许寄存器。
0x005 URW utvec 用户陷阱处理程序基地址。
用户陷阱处理
0x040 URW uscratch 用户陷阱处理程序的暂存寄存器。
0x041 URW uepc 用户异常程序计数器。
0x042 URW ucause 用户陷阱原因。
0x043 URW utval 用户地址或指令错误。
0x044 URW uip 用户中断待处理。
用户浮点 CSRs
0x001 URW fflags 浮点应计异常。
0x002 URW 来自浮点动态舍入模式。
0x003 URW fcsr 浮点控制和状态寄存器（frm + fflags）。
用户计数器/定时器
0xC00 URO cycle RDCYCLE 指令的周期计数器。
0xC01 URO time RDTIME 指令的定时器。
0xC02 URO instret RDINSTRET 指令的指令退休计数器。
0xC03 URO hpmcounter3 性能监控计数器。
0xC04 URO hpmcounter4 性能监控计数器。
...
0xC1F URO hpmcounter31 性能监控计数器。
0xC80 URO Cycleh 仅 cycle、RV32I 的高 32 位。
0xC81 URO timeh 仅 time、RV32I 的高 32 位。
0xC82 URO instreth instret、RV32I 的高 32 位。
0xC83 URO hpmcounter3h 仅 hpmcounter3、RV32I 的高 32 位。
0xC84 URO hpmcounter4h hpmcounter4 的高 32 位，仅限 RV32I。
...
0xC9F URO hpmcounter31h 仅 hpmcounter31、RV32I 的高 32 位。
表 2.2：当前分配的 RISC-V 用户级 CSR 地址。

<!-- Source PDF page 21 -->
号码 权限名称 说明
主管陷阱设置
0x100 SRW sstatus 监控器状态寄存器。
0x102 SRW sedeleg 主管异常委托寄存器。
0x103 SRW sideleg 管理程序中断委托寄存器。
0x104 SRW sie 监控程序中断使能寄存器。
0x105 SRW stvec 管理程序陷阱处理程序基地址。
0x106 SRW scounteren 监控计数器使能。
主管陷阱处理
0x140 SRW sscratch 管理程序陷阱处理程序的临时寄存器。
0x141 SRW sepc 管理程序异常程序计数器。
0x142 SRW scause 管理程序陷阱原因。
0x143 SRW stval 主管地址或指令错误。
0x144 SRW sip 监控程序中断待处理。
主管保护和翻译
0x180 SRW satp 主管地址转换和保护。
表 2.3：当前分配的 RISC-V 监管级 CSR 地址。

<!-- Source PDF page 22 -->
号码 权限名称 说明
机器信息寄存器
0xF11 MRO mvendorid 供应商 ID。
0xF12 MRO marchid 架构 ID。
0xF13 MRO mimpid 实施 ID。
0xF14 MRO mhartid 硬件线程 ID。
机器陷阱设置
0x300 MRW mstatus 机器状态寄存器。
0x301 MRW misa ISA 和扩展
0x302 MRW medeleg 机器异常委托寄存器。
0x303 MRW mideleg 机器中断委托寄存器。
0x304 MRW mie 机器中断使能寄存器。
0x305 MRW mtvec 机器陷阱处理程序基地址。
0x306 MRW mcounteren 机器计数器使能。
机器陷阱处理
0x340 MRW mscratch 机器陷阱处理程序的暂存寄存器。
0x341 MRW mepc 机器异常程序计数器。
0x342 MRW mcause 机器陷阱原因。
0x343 MRW mtval 机器地址或指令错误。
0x344 MRW mip 机器中断待处理。
机器内存保护
0x3A0 MRW pmpcfg0 物理内存保护配置。
0x3A1 MRW pmpcfg1 物理内存保护配置，仅限 RV32。
0x3A2 MRW pmpcfg2 物理内存保护配置。
0x3A3 MRW pmpcfg3 物理内存保护配置，仅限 RV32。
0x3B0 MRW pmpaddr0 物理内存保护地址寄存器。
0x3B1 MRW pmpaddr1 物理内存保护地址寄存器。
...
0x3BF MRW pmpaddr15 物理内存保护地址寄存器。
表 2.4：当前分配的 RISC-V 机器级 CSR 地址。

<!-- Source PDF page 23 -->
号码 权限名称 说明
机器计数器/定时器
0xB00 MRW mcycle 机器 cycle 计数器。
0xB02 MRW minstret 机器指令-退休计数器。
0xB03 MRW mhpmcounter3 机器性能监控计数器。
0xB04 MRW mhpmcounter4 机器性能监控计数器。
...
0xB1F MRW mhpmcounter31 机器性能监控计数器。
0xB80 MRW mcycleh 仅 mcycle、RV32I 的高 32 位。
0xB82 MRW minstreth 仅 minstret、RV32I 的高 32 位。
0xB83 MRW mhpmcounter3h 仅 mhpmcounter3、RV32I 的高 32 位。
0xB84 MRW mhpmcounter4h mhpmcounter4、RV32I 的高 32 位。
...
0xB9F MRW mhpmcounter31h 仅 mhpmcounter31、RV32I 的高 32 位。
机器计数器设置
0x320 MRW mcountinhibit 机器计数器禁止寄存器。
0x323 MRW mhpmevent3 机器性能监控事件选择器。
0x324 MRW mhpmevent4 机器性能监控事件选择器。
...
0x33F MRW mhpmevent31 机器性能监控事件选择器。
调试/跟踪寄存器（与调试模式共享）
0x7A0 MRW tselect 调试/跟踪触发寄存器选择。
0x7A1 MRW tdata1 第一个调试/跟踪触发数据寄存器。
0x7A2 MRW tdata2 第二个调试/跟踪触发数据寄存器。
0x7A3 MRW tdata3 第三个调试/跟踪触发数据寄存器。
调试模式寄存器
0x7B0 DRW dcsr 调试控制和状态寄存器。
0x7B1 DRW dpc 调试 PC。
0x7B2 DRW dscratch0 调试暂存寄存器 0。
0x7B3 DRW dscratch1 调试暂存寄存器 1。
表 2.5：当前分配的 RISC-V 机器级 CSR 地址。

<!-- Source PDF page 24 -->


### 2.3 CSR 现场规格
以下定义和缩写用于指定字段内的行为
企业社会责任。
保留 写入保留值，读取忽略值 (WPRI)
一些完整的读/写字段被保留以供将来使用。软件应忽略读取的值
来自这些字段，并且在将值写入其他字段时应保留这些字段中保存的值
同一寄存器的字段。为了向前兼容，不提供这些的实现
字段必须将它们硬连接为零。这些字段在寄存器说明中标记为 WPRI。
为了简化软件模型，先前保留的任何向后兼容的未来定义
CSR 中的字段必须应对非原子读/修改/写序列的可能性
用于更新 CSR 中的其他字段。或者，原始 CSR 定义必须指定
子字段只能以原子方式更新，这可能需要两个指令清除位/集
一般来说，如果中间值不合法，则位序列可能会出现问题。
写入/只读合法值 (WLRL)
一些读/写 CSR 字段仅指定可能位编码的子集的行为，而其他字段则仅指定可能的位编码的子集的行为。
保留位编码。软件不应向此类字段写入除合法值以外的任何内容，
并且不应假设读取将返回合法值，除非最后一次写入具有合法值，
或者自从另一个操作（例如复位）将寄存器设置为合法后，寄存器还没有被写入
值。这些字段在寄存器说明中标记为 WLRL。
硬件实现只需要实现足够的状态位来区分
支持的值，但必须始终返回任何受支持的完整指定位编码
读取时的值。
允许但不要求实现在以下情况下引发非法指令异常：
指令尝试将不支持的值写入 WLRL 字段。实现可以
当最后一次写入非法时，在读取 WLRL 字段时返回任意位模式
值，但返回的值应该确定性地取决于非法写入的值和
写入之前字段的值。
写入任何值，读取有效值 (WARL)
一些读/写 CSR 字段仅为位编码的子集定义，但允许任何值
写入时保证每次读取时都返回合法值。假设写入 CSR
没有其他副作用，支持的值的范围可以通过尝试写入来确定
所需的设置，然后读取以查看该值是否保留。这些字段在中标记为 WARL
寄存器描述。
将不支持的值写入 WARL 字段时，实现不会引发异常。
当最后一次写入时，实现可以在读取 aWARL 字段时返回任何合法值

<!-- Source PDF page 25 -->
非法值，但返回的合法值应确定性地取决于非法写入
value 和写入之前字段的值。


### 2.4 CSR 宽度调制
如果 CSR 的宽度发生更改（例如，通过更改 MXLEN 或 UXLEN，如中所述
第 

### 3.1.6.2 节），除非另有说明，新宽度 CSR 的可写字段和位的值是
否则，从先前宽度 CSR 确定，就像通过以下算法一样：
1. 将前一个宽度的CSR 的值复制到相同宽度的临时寄存器中。
2. 对于前宽度 CSR 的只读位，在相同位置的位
临时寄存器被设置为零。
3. 临时寄存器的宽度更改为新宽度。如果新宽度 W 为
比之前的宽度窄，临时寄存器的最低有效 W 位是
保留并丢弃较高有效位。如果新宽度比
先前的宽度，临时寄存器被零扩展至更宽的宽度。
4. 新宽度CSR的每个可写字段取相同位置的位的值
临时登记册。
更改 CSR 的宽度不是对 CSR 的读取或写入，因此不会触发任何一侧
影响。
