# RISC-V 特权架构中文全文译文

源文档：`The_RISC-V_Instruction Set_Manual_Volume_II_Privileged_Architecture_TD005_V20190608.pdf`

本文是 RISC-V 特权架构规范的中文译文稿，用于离线阅读、设计讨论和实现对齐。源 PDF 不属于本项目原创内容，版权、商标和许可归原发布方及贡献者所有。译文保留 CSR 名、寄存器名、异常名、指令名、字段名和必要英文术语；若译文与源 PDF 存在差异，以源 PDF 为准。

## 术语约定

| 原术语 | 译名 | 说明 |
|---|---|---|
| privileged architecture | 特权架构 | 特权级、CSR、陷入、中断、保护和地址转换规范 |
| privilege level | 特权级 | U/S/M 等执行级别 |
| Machine mode | Machine 模式/机器模式 | 最高特权级，负责根控制与平台管理 |
| Supervisor mode | Supervisor 模式/监管者模式 | 操作系统内核常用特权级 |
| User mode | User 模式/用户模式 | 应用程序常用非特权级 |
| Debug mode | Debug 模式 | 调试规范定义的特殊执行模式 |
| trap | 陷入 | 异常或中断导致的控制转移 |
| exception | 异常 | 指令同步产生的事件 |
| interrupt | 中断 | 异步事件 |
| CSR | 控制与状态寄存器 | 特权状态、配置、陷入信息和计数器寄存器 |
| WARL | 写任意、读合法 | 写入任意值，读回合法值 |
| WPRI | 保留写忽略、读忽略 | 软件应保持保留字段不变，读值不依赖 |
| WLRL | 只写合法值、读合法值 | 只保证合法写入后读回合法值 |
| PMA | 物理内存属性 | 物理区域的访问类型、原子性、缓存性和幂等性 |
| PMP | 物理内存保护 | Machine 模式配置的物理访问控制 |
| PTE | 页表项 | 虚拟地址转换中的页表描述符 |
| ASID | 地址空间标识符 | TLB/地址转换缓存区分地址空间的标签 |

## 1. 引言

特权架构定义非特权 ISA 之上的系统控制能力。它描述处理器如何在不同特权级之间运行，如何通过 CSR 暴露和修改控制状态，如何处理中断、异常、环境调用和返回，如何配置物理内存属性与物理内存保护，以及如何通过页表完成虚拟地址到物理地址的转换。

RISC-V 的特权模型是模块化的。最小系统可以只实现 Machine 模式；运行通用操作系统的系统通常实现 User、Supervisor 和 Machine 模式；调试系统还可进入 Debug 模式。较高特权级通常可以访问较低特权级的资源，并负责为较低特权级提供执行环境。

### 1.1 特权软件栈术语

RISC-V 软件栈通常分层：应用运行在 User 模式，操作系统内核运行在 Supervisor 模式，固件或平台根控制运行在 Machine 模式。Machine 模式负责复位入口、低级中断控制、物理内存保护、平台计时器和对 Supervisor 的服务。Supervisor 模式负责进程、虚拟内存、系统调用和设备驱动。User 模式通过 `ECALL` 请求上层环境服务。

### 1.2 特权级

规范定义的主要特权级如下：

| 编码 | 名称 | 典型用途 |
|---|---|---|
| 0 | User/Application | 应用程序和普通非特权代码 |
| 1 | Supervisor | 操作系统内核、虚拟内存和设备管理 |
| 2 | Reserved | 保留 |
| 3 | Machine | 平台根控制、固件、最高特权处理 |

实现可以只支持 M，也可以支持 M+U 或 M+S+U。较低特权级试图执行更高特权指令或访问不允许的 CSR 时，会产生 illegal-instruction exception。特权级切换通常由 trap 入口和 `xRET` 返回指令完成。

### 1.3 Debug 模式

Debug 模式由外部调试规范定义，不属于普通 U/S/M 特权级之一。进入 Debug 模式后，调试器可检查和控制 hart 状态。特权架构只在若干状态字段中为调试模式留出交互点；具体调试寄存器和外部接口由调试规范定义。

## 2. 控制与状态寄存器（CSR）

CSR 通过非特权 ISA 的 `Zicsr` 指令访问。CSR 地址为 12 位，地址空间按特权级和读写属性组织。CSR 可能是只读、读写、WARL、WLRL 或含有副作用的寄存器。访问不存在、权限不足或当前实现不支持的 CSR 会产生 illegal-instruction exception。

### 2.1 CSR 地址映射约定

CSR 地址高位编码寄存器权限和所属特权级。地址 `0x000` 到 `0x0ff` 常用于 User 级标准 CSR，`0x100` 到 `0x1ff` 用于 Supervisor 级，`0x300` 到 `0x3ff` 用于 Machine 级。只读 CSR 通常放在高地址段。规范还为调试、性能计数器和自定义 CSR 预留空间。

### 2.2 主要 CSR 清单

| 类别 | CSR |
|---|---|
| Machine 信息 | `misa`、`mvendorid`、`marchid`、`mimpid`、`mhartid` |
| Machine trap/setup | `mstatus`、`mtvec`、`medeleg`、`mideleg`、`mie`、`mip` |
| Machine trap handling | `mscratch`、`mepc`、`mcause`、`mtval` |
| Machine 计时/计数 | `mtime`、`mtimecmp`、`mcycle`、`minstret`、`mhpmcounter*`、`mcountinhibit` |
| Machine 保护 | `pmpcfg*`、`pmpaddr*` |
| Supervisor trap/setup | `sstatus`、`stvec`、`sie`、`sip`、`scounteren` |
| Supervisor trap handling | `sscratch`、`sepc`、`scause`、`stval` |
| Supervisor 地址转换 | `satp` |

### 2.3 CSR 字段规范

WPRI 字段保留给未来标准使用。软件写 CSR 时应保留这些字段原值，读 CSR 时不应依赖其值。WARL 字段允许软件写入任意位型，但硬件读回某个合法值；软件可通过写入候选值并读回来发现支持范围。WLRL 字段要求软件只写合法值，硬件只保证合法写入后的读值有定义。

### 2.4 CSR 宽度调制

CSR 宽度通常随 XLEN 改变。若 XLEN 变化，部分 CSR 字段会被截断、扩展或重新解释。特权软件在修改 XLEN 或跨模式切换时，需要按规范处理状态宽度，避免把较宽模式下的非法值暴露给较窄模式。

## 3. Machine 级 ISA，版本 1.11

Machine 模式是所有 RISC-V 特权实现的根模式。复位后 hart 通常进入 M 模式，由固件初始化平台、设置 trap 向量、配置 PMP、启动计时器和中断，并决定是否进入 S/U 模式。

### 3.1 Machine 信息 CSR

`misa` 描述当前 hart 支持的基础 ISA 宽度和扩展集合。`MXL` 字段编码 XLEN，扩展位标识 `I`、`M`、`A`、`F`、`D`、`C` 等标准扩展。若实现允许写 `misa`，软件可启用或禁用某些扩展；写入非法组合时读回值必须保持合法。

`mvendorid`、`marchid`、`mimpid` 分别描述实现供应方、架构 ID 和实现版本。`mhartid` 给出当前 hart 在平台中的唯一编号。平台软件不应假设 hart ID 连续或从 0 开始，除非平台规范另有保证。

### 3.2 `mstatus` 机器状态寄存器

`mstatus` 是 Machine 模式最重要的状态 CSR，包含全局中断使能、前一特权级、前一中断使能、扩展上下文状态、内存访问控制和字长控制等字段。

| 字段 | 含义 |
|---|---|
| `MIE` | Machine 模式全局中断使能 |
| `MPIE` | 进入 M trap 前的 `MIE` 保存值 |
| `MPP` | 进入 M trap 前的特权级 |
| `SIE`/`SPIE` | Supervisor 中断使能及其保存值 |
| `SPP` | 进入 S trap 前的特权级 |
| `FS` | 浮点上下文状态 |
| `XS` | 其他扩展上下文状态 |
| `SD` | 汇总 dirty 状态 |
| `MPRV` | 让加载/存储按 `MPP` 指定特权级执行权限检查 |
| `SUM` | S 模式是否允许访问 U 页 |
| `MXR` | 是否允许从可执行页读数据 |
| `TVM` | 是否拦截 S 模式虚拟内存管理操作 |
| `TW` | 是否拦截 S/U 模式 `WFI` |
| `TSR` | 是否拦截 S 模式 `SRET` |

进入 trap 时，硬件把当前中断使能保存到对应 `xPIE`，清除当前全局中断使能，并记录来源特权级到 `xPP`。执行 `MRET` 或 `SRET` 时，硬件恢复中断使能和特权级，并把 `xPIE` 置为 1，把 `xPP` 设为最低支持特权级，以减少错误返回的风险。

`FS` 和 `XS` 用于延迟保存扩展状态。状态可为 Off、Initial、Clean 或 Dirty。若状态为 Off，访问对应扩展会触发 illegal-instruction exception；Dirty 表明上下文切换时需要保存该扩展状态。`SD` 汇总 FS/XS/VS 等状态是否为 Dirty。

### 3.3 Trap 向量和委派

`mtvec` 保存 Machine trap 入口基址和模式。Direct 模式下所有 M trap 跳到同一基址。Vectored 模式下，中断可跳到 `BASE + 4 * cause`，异常仍跳到基址。`BASE` 必须满足实现要求的对齐。

`medeleg` 和 `mideleg` 控制异常和中断是否委派给较低特权级处理。若某异常位在 `medeleg` 中置 1，并且异常发生在可委派的较低模式，则 trap 进入 S 模式而不是 M 模式。`mideleg` 对中断类似。委派后，对应的 `sepc`、`scause`、`stval`、`sstatus` 会被更新，Machine 的 trap CSR 不被本次 trap 覆盖。

### 3.4 中断寄存器 `mie` 和 `mip`

`mie` 是中断使能寄存器，`mip` 是中断挂起寄存器。常见 Machine/Supervisor/User 软件、计时器和外部中断字段如下：

| 字段 | 含义 |
|---|---|
| `MSIP`/`SSIP`/`USIP` | 软件中断挂起 |
| `MTIP`/`STIP`/`UTIP` | 计时器中断挂起 |
| `MEIP`/`SEIP`/`UEIP` | 外部中断挂起 |
| `MSIE`/`SSIE`/`USIE` | 软件中断使能 |
| `MTIE`/`STIE`/`UTIE` | 计时器中断使能 |
| `MEIE`/`SEIE`/`UEIE` | 外部中断使能 |

一个中断能被当前 hart 接收，通常需要挂起位、对应使能位、当前特权级的全局中断使能以及委派规则共同满足。较高特权级中断可以打断较低特权级；同级中断受全局使能控制。

### 3.5 计时器 `mtime` 和 `mtimecmp`

`mtime` 是平台提供的单调递增机器计时器，`mtimecmp` 是比较寄存器。当 `mtime >= mtimecmp` 时，对应 hart 的 `MTIP` 置位，若 `MTIE` 和 `MIE` 允许，则产生 Machine timer interrupt。`mtime` 和 `mtimecmp` 通常位于内存映射平台寄存器，而不是普通 CSR；具体地址由平台定义。

S 模式计时器通常由 M 模式通过委派或软件模拟提供。M 模式可以在 Machine timer interrupt 中设置下一次 `mtimecmp`，并向 S 模式注入 `STIP` 或维护虚拟计时器。

### 3.6 硬件性能监控和计数器控制

`mcycle`、`minstret` 和 `mhpmcounter*` 记录周期、退休指令和实现定义事件。`mcounteren` 和 `scounteren` 控制较低特权级能否读取计数器。`mcountinhibit` 可停止某些计数器递增，以降低功耗或避免统计污染。计数器是否存在、宽度和事件选择由实现和平台定义。

### 3.7 Trap 处理 CSR

`mscratch` 是 M trap 处理程序使用的临时寄存器，常用于保存栈指针或 hart 本地上下文指针。`mepc` 保存被 trap 打断或导致异常的指令地址。`mcause` 最高位标识中断或异常，其余位给出 cause 编号。`mtval` 提供 trap 附加信息，例如错误地址、非法指令位型或页故障地址；具体是否写入有效信息由异常类型和实现决定。

常见异常 cause 包括：

| Cause | 异常 |
|---|---|
| 0 | Instruction address misaligned |
| 1 | Instruction access fault |
| 2 | Illegal instruction |
| 3 | Breakpoint |
| 4 | Load address misaligned |
| 5 | Load access fault |
| 6 | Store/AMO address misaligned |
| 7 | Store/AMO access fault |
| 8 | Environment call from U-mode |
| 9 | Environment call from S-mode |
| 11 | Environment call from M-mode |
| 12 | Instruction page fault |
| 13 | Load page fault |
| 15 | Store/AMO page fault |

中断 cause 使用最高位区分，并用低位编码 software、timer 和 external interrupt。

### 3.8 Machine 模式特权指令

`ECALL` 在当前模式产生环境调用异常。U/S/M 模式发出的 `ECALL` 使用不同 cause，便于上层环境区分来源。`EBREAK` 产生 breakpoint exception，通常用于调试。

`MRET` 从 Machine trap 返回。它根据 `mstatus.MPP` 恢复目标特权级，把 `mepc` 载入 `pc`，并恢复中断使能。`SRET` 是 Supervisor 返回指令；在某些 `mstatus` 控制位设置下，M 模式可以禁止 S 模式执行 `SRET`。

`WFI` 表示等待中断。实现可以让 hart 进入低功耗状态，也可以把它当作 hint 继续执行。若中断变为可服务，hart 应继续执行。`mstatus.TW` 可以让较低模式执行 `WFI` 时被拦截。

### 3.9 复位和不可屏蔽中断

复位后 hart 进入实现定义的初始地址，通常处于 M 模式，关中断，部分 CSR 为实现定义值。复位代码必须初始化 trap 向量、栈、PMP、计时器和必要外设。

不可屏蔽中断用于严重平台事件。规范允许实现定义 NMI 行为；NMI 可能覆盖部分 trap 状态，因此处理程序应尽量短小，并把恢复和诊断交给平台机制。

## 4. 物理内存属性（PMA）

PMA 描述物理地址区域的固有属性。它不是由普通页表决定，而由平台和硬件实现定义。PMA 影响访问是否合法、是否可缓存、是否支持原子操作、是否幂等、是否具有 I/O 语义，以及访问错误如何报告。

### 4.1 主存、I/O 和空区域

主存区域通常支持读写执行、缓存、一致性和普通原子操作。I/O 区域可能只支持特定宽度访问，不一定幂等，也可能要求强排序。空区域或未实现区域的访问应产生访问错误。软件通过平台描述或固件接口了解物理内存地图。

### 4.2 访问类型和原子性 PMA

PMA 可限制读、写、执行、AMO 和 LR/SC。某些区域只支持自然对齐访问；某些区域不支持原子指令。若访问违反 PMA，硬件通常产生 access fault，而不是 page fault。页表权限先给出虚拟内存视角，PMA/PMP 再在物理地址层面施加约束。

### 4.3 内存排序、一致性、缓存性和幂等性

缓存性决定区域是否可被缓存；一致性决定多个 hart 对同一区域的访问如何相互可见；幂等性决定重复执行访问是否安全。设备寄存器往往非幂等，例如读操作可能清除状态。软件需要使用 `FENCE` 和平台规定的设备访问顺序保护 I/O。

## 5. 物理内存保护（PMP）

PMP 让 M 模式为 S/U 模式设置物理地址访问权限。它常用于在无 MMU 系统中隔离任务，也用于在有 MMU 系统中限制 S 模式不能访问某些物理区域。PMP 检查发生在物理地址阶段，可作用于取指、加载和存储/AMO。

### 5.1 PMP CSR

PMP 使用 `pmpcfg*` 和 `pmpaddr*` CSR。每个 PMP 条目包含地址匹配方式、读写执行权限和锁定位。

| 字段 | 含义 |
|---|---|
| `R` | 允许读 |
| `W` | 允许写 |
| `X` | 允许执行 |
| `A` | 地址匹配模式 |
| `L` | 锁定条目，限制后续修改并可影响 M 模式 |

地址匹配模式包括 OFF、TOR、NA4 和 NAPOT。OFF 表示条目无效。TOR 表示从上一条目地址到本条目地址的范围。NA4 表示自然对齐 4 字节区域。NAPOT 表示自然对齐 2 的幂大小区域，通过 `pmpaddr` 低位连续 1 编码大小。

### 5.2 PMP 匹配和权限

PMP 按条目编号从低到高匹配，第一条匹配条目决定权限。若访问跨越多个 PMP 区域，必须整体满足同一条目或相关权限要求，否则失败。S/U 模式没有匹配条目时，默认拒绝访问；M 模式默认允许访问，除非条目设置 `L` 并要求 M 模式也受约束。

`R=0,W=1` 是保留组合。执行权限 `X` 与读权限独立；可执行区域不必可读，反之亦然。页表转换得到物理地址后仍要经过 PMP 检查，因此 PMP 可以限制 S 模式页表映射的实际物理范围。

## 6. Supervisor 级 ISA，版本 1.11

Supervisor 模式面向操作系统内核。它提供 S 级 trap CSR、中断控制、虚拟内存根寄存器 `satp`、页表机制和内存管理栅栏 `SFENCE.VMA`。M 模式可通过委派让 S 模式直接处理来自 U 模式的系统调用、页故障、断点和部分中断。

### 6.1 `sstatus`

`sstatus` 是 `mstatus` 的 S 模式可见子集。重要字段包括 `SIE`、`SPIE`、`SPP`、`FS`、`XS`、`SUM`、`MXR`、`UBE` 和 `SD`。`SIE` 控制 S 模式全局中断；`SPP` 记录 S trap 前的特权级，通常为 U 或 S；`SUM` 允许 S 模式访问 U 页；`MXR` 允许从可执行页读取数据。

进入 S trap 时，硬件保存 `SIE` 到 `SPIE`，清除 `SIE`，并把来源特权级写入 `SPP`。`SRET` 使用 `sepc` 和 `SPP` 返回，并恢复 `SIE`。

### 6.2 S 级 trap CSR

`stvec` 是 S trap 向量基址和模式。`sscratch` 给 S trap 处理程序保存临时上下文。`sepc` 保存导致或被打断的指令地址。`scause` 保存异常或中断 cause。`stval` 保存附加 trap 信息，例如页故障虚拟地址或非法指令位型。

`sip` 和 `sie` 是 S 级中断挂起和使能 CSR。S 模式可见的中断通常包括 software、timer 和 external interrupt。哪些中断能被 S 模式直接处理由 `mideleg` 控制。

### 6.3 Supervisor 计数器访问

`scounteren` 控制 U 模式是否可以访问 `cycle`、`time`、`instret` 等计数器。若相应位未使能，U 模式读取会产生 illegal-instruction exception。M 模式的 `mcounteren` 又控制 S 模式是否可访问这些计数器。

### 6.4 `satp` 地址转换与保护寄存器

`satp` 保存虚拟内存模式、ASID 和根页表物理页号 PPN。RV32 的 `satp` 包含 `MODE`、`ASID` 和 `PPN`；RV64 的 `satp` 为更宽 ASID 和 PPN 提供空间。`MODE=0` 表示 Bare，即不启用分页；其他模式如 Sv32、Sv39、Sv48 启用基于页表的转换。

切换地址空间时，操作系统通常写 `satp`，然后执行 `SFENCE.VMA` 使地址转换缓存与新页表一致。ASID 可减少 TLB 刷新范围，但软件必须正确管理 ASID 重用。

### 6.5 Supervisor 指令

`SRET` 从 S trap 返回，语义类似 `MRET` 但使用 `sstatus` 和 `sepc`。`SFENCE.VMA` 同步当前 hart 的地址转换缓存与内存中的页表更新。它可以按虚拟地址和 ASID 选择性刷新，也可以全局刷新。页表写入与 `SFENCE.VMA` 的顺序需要由内存模型和栅栏保证。

## 7. Trap、exception 和 interrupt 流程

当指令产生异常或中断被采纳时，硬件执行以下概念步骤：

1. 根据当前特权级、cause 和委派寄存器决定目标特权级。
2. 把被打断或出错指令地址写入目标 `xepc`。
3. 把 cause 写入目标 `xcause`，把附加信息写入 `xtval`。
4. 更新目标状态寄存器的 `xPIE`、`xIE` 和 `xPP` 字段。
5. 把 `pc` 设置为目标 `xtvec` 指定的入口。

异常通常精确报告到导致异常的指令。中断发生在指令边界。若 trap 被委派到 S 模式，M 模式的 trap 处理状态不被覆盖；若未委派，则进入 M 模式。trap 处理程序完成后使用 `MRET` 或 `SRET` 返回。

环境调用是常见同步 trap：U 模式 `ECALL` 通常进入 S 模式系统调用处理；S 模式 `ECALL` 常进入 M 模式固件服务；M 模式 `ECALL` 则由 M trap 处理。断点和页故障也通常委派给 S 模式，由操作系统处理调试、缺页和权限错误。

## 8. 虚拟内存概览

启用分页后，S/U 模式访问的虚拟地址通过页表转换为物理地址。页表由内存中的 PTE 组成，根页表由 `satp.PPN` 指定。地址转换会检查 PTE 的有效位、读写执行权限、用户位、全局位、访问位和脏位，并可能产生 page fault。

PTE 通用字段如下：

| 字段 | 含义 |
|---|---|
| `V` | PTE 有效 |
| `R` | 页可读 |
| `W` | 页可写 |
| `X` | 页可执行 |
| `U` | 用户页，可由 U 模式访问 |
| `G` | 全局映射，不受 ASID 限制 |
| `A` | 已访问 |
| `D` | 已写入/脏 |
| `RSW` | 留给 Supervisor 软件使用 |
| `PPN` | 物理页号 |

`V=0` 表示无效 PTE。`W=1,R=0` 是保留组合，会导致 page fault。叶 PTE 是具有 `R`、`W` 或 `X` 权限的 PTE；非叶 PTE 指向下一级页表。若叶 PTE 出现在较高层级，可形成大页，但物理页号低位必须满足对齐要求。

## 9. Sv32

Sv32 用于 32 位虚拟地址系统。虚拟地址分为两级 VPN 和页内偏移，每级 VPN 索引 1024 项页表。页大小为 4 KiB。地址转换从 `satp.PPN` 指定的根页表开始，读取一级 PTE；若不是叶 PTE，进入下一级；若是叶 PTE，组合 PPN 和页内偏移生成物理地址。

转换过程中会检查：

- PTE 是否有效，是否存在保留权限组合。
- 当前访问类型是否满足 `R/W/X`。
- 当前特权级是否允许访问 `U` 页。
- `SUM` 和 `MXR` 是否改变 S 模式访问或读可执行页的规则。
- `A` 和 `D` 位是否满足访问和写入要求。
- 大页映射的物理页号低位是否对齐。

任一检查失败会产生 instruction/load/store page fault。页表本身的内存访问还要受 PMA/PMP 约束。

## 10. Sv39

Sv39 用于 RV64，虚拟地址有效位为 39 位，并要求高位按 bit 38 符号扩展。地址分为三级 VPN 和 12 位页内偏移，每级 512 项 PTE。普通页为 4 KiB，也支持 2 MiB 和 1 GiB 大页。`satp` 中 `MODE=Sv39` 时，`PPN` 指向根页表。

若虚拟地址高位不满足符号扩展规则，访问产生 page fault。转换算法与 Sv32 类似，但层级为三级，PTE 宽度和 PPN 字段更大。操作系统必须保证大页 PPN 对齐，并在修改页表后执行合适的 `SFENCE.VMA`。

## 11. Sv48

Sv48 同样用于 RV64，虚拟地址有效位为 48 位，高位按 bit 47 符号扩展。它使用四级页表，支持 4 KiB、2 MiB、1 GiB 和 512 GiB 页面。Sv48 适合更大虚拟地址空间的系统。除层级数量和地址划分外，PTE 权限、A/D 位、ASID、`SFENCE.VMA` 和 page fault 规则与 Sv39 保持同一模型。

## 12. 地址转换、PMP 和异常的关系

一次 S/U 模式访存可能先经过虚拟地址转换，再经过 PMP/PMA 检查。页表权限失败产生 page fault；物理访问权限或属性失败产生 access fault。若页表遍历访问页表内存本身失败，也可能产生相应 page fault 或 access fault。取指、加载和存储/AMO 有不同异常类型。

`MPRV` 可让 M 模式数据访问按 `MPP` 指定的特权级和地址转换规则执行，便于 M 模式代表 S/U 模式拷贝数据。`SUM` 控制 S 模式能否访问 U 页，`MXR` 控制可执行页是否可读。这些字段只影响数据访问，不改变取指权限。

## 13. RISC-V 特权指令清单

| 指令 | 作用 |
|---|---|
| `ECALL` | 产生当前模式的环境调用异常 |
| `EBREAK` | 产生断点异常 |
| `MRET` | 从 Machine trap 返回 |
| `SRET` | 从 Supervisor trap 返回 |
| `WFI` | 等待中断，可作为低功耗 hint |
| `SFENCE.VMA` | 同步虚拟内存地址转换缓存 |
| CSR 指令 | 通过 `Zicsr` 读写特权 CSR |

这些指令的可执行权限取决于当前特权级和控制字段。低特权级执行不允许的特权指令会产生 illegal-instruction exception。

## 14. 实现与软件要点

实现特权架构时，应优先保证 trap 精确性、CSR WARL/WPRI/WLRL 行为、`mstatus`/`sstatus` 状态更新、委派路径、PMP 第一匹配规则、页表遍历异常和 `SFENCE.VMA` 同步语义。软件侧应清晰区分 page fault、access fault 和 address misaligned，避免把 PMP/PMA 错误误判为页表错误。

操作系统启动路径通常为：M 模式复位入口初始化平台，设置 `mtvec`、PMP、计时器和委派寄存器，准备 S 模式入口和 `satp`，通过 `MRET` 进入 S 模式；S 模式初始化页表、中断和进程上下文，再通过 `SRET` 进入 U 模式。U 模式通过 `ECALL` 进入 S 模式系统调用路径，异常和页故障由 S 模式处理，必要时通过 SBI 或平台接口请求 M 模式服务。

## 15. 历史

本版本特权架构整理了 Machine 和 Supervisor 模式的基本机制，定义 CSR 编址、trap 处理、PMP、PMA、计时器、中断和 Sv32/Sv39/Sv48 虚拟内存。后续 RISC-V 规范继续演进虚拟化、Supervisor 扩展、调试、平台中断控制器和更细粒度的系统能力。本译文聚焦该源 PDF 的特权架构主体内容。

## 翻译完成状态

本文件已从入口/摘要稿改为特权架构中文正文译文稿，覆盖特权级、CSR 地址与字段规则、`mstatus`/`sstatus`、trap/exception/interrupt 流程、Machine/Supervisor/User 模式关系、计时器和中断、环境调用与返回、PMA、PMP、`satp`、`SFENCE.VMA`、Sv32/Sv39/Sv48 页表与地址转换，以及特权指令清单。
