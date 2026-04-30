# 第 2 章 System Overview

图 2.1 展示 External Debug Support 的主要组件。虚线框显示的 block 是可选的。

用户与 Debug Host（例如 laptop）交互，Debug Host 上运行 debugger（例如 gdb）。debugger 与 Debug Translator（例如 OpenOCD，其中可能包括硬件驱动）通信，以便和 Debug Transport Hardware（例如 Olimex USB-JTAG adapter）通信。Debug Transport Hardware 将 Debug Host 连接到 platform 的 Debug Transport Module（DTM）。DTM 使用 Debug Module Interface（DMI）提供对 Debug Module（DM）的访问。

DM 允许 debugger halt 平台中的任何 hart。Abstract command 提供对 GPR 的访问。额外寄存器可以通过 abstract command 访问，或通过把程序写入可选的 Program Buffer 访问。

Program Buffer 允许 debugger 在 hart 上执行任意指令。此机制可用于访问 memory。可选的 system bus access block 允许在不使用 RISC-V hart 执行访问的情况下进行 memory access。

每个 RISC-V hart 都可以实现 Trigger Module。当 trigger 条件满足时，hart 将 halt 并通知 debug module 它们已经 halted。

图 2.1：RISC-V Debug System Overview。图中从 Debug Host、Debug Translator、Debug Transport Hardware 到 DTM、DMI、DM，再到 hart、Program Buffer、System Bus Access 和 Trigger Module，展示了外部调试路径与可选组件之间的关系。
