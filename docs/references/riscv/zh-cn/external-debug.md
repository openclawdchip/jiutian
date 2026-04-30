# RISC-V External Debug 中文全文译文

源文档：`RISC-V_External Debug_Support_TD003_V0.13.pdf`

本文是 RISC-V External Debug Support 0.13 的中文译文稿，用于离线阅读、设计讨论和实现对齐。源 PDF 不属于本项目原创内容，版权、商标和许可归原发布方及贡献者所有。译文保留寄存器名、字段名、命令名、CSR 名、接口名和必要英文术语；若译文与源 PDF 存在差异，以源 PDF 为准。

## 1. 引言

External Debug 规范定义外部调试器如何在不依赖目标软件配合的情况下控制 RISC-V hart。调试器通过 Debug Transport Module（DTM）访问 Debug Module Interface（DMI），再由 Debug Module（DM）对一个或多个 hart 执行 halt、resume、reset、寄存器访问、program buffer 执行和 system bus access。

规范目标是让调试器能完成基本 bring-up、断点、单步、寄存器和内存检查、异常现场分析、多 hart 控制和安全认证。它不规定调试器 UI，也不规定所有实现必须支持全部可选能力；实现通过寄存器字段报告实际能力。

## 2. 系统概览

外部调试系统由三层组成：

| 组件 | 作用 |
|---|---|
| Debugger | 主机侧软件，例如 GDB server 或芯片 bring-up 工具 |
| DTM | 调试传输模块，把 JTAG 等物理传输转换为 DMI 访问 |
| DM | 调试模块，暴露 DMI 寄存器并控制 hart |
| Hart debug logic | hart 内部调试逻辑，进入 Debug Mode、执行 abstract command 或 program buffer |

调试器不直接访问 hart 内部信号，而是通过 DM 寄存器发命令、轮询状态并读取结果。DTM 只负责传输，不解释大部分调试语义。DM 是调试协议的中心，负责 hart 选择、错误报告、认证、复位控制和可选系统总线访问。

## 3. 术语和上下文

hart 是被调试的执行上下文。Debug Mode 是 hart 进入调试控制后的特殊模式。halted 表示 hart 已停止普通程序执行并受 DM 控制。running 表示 hart 正常执行程序。unavailable 表示 hart 当前不可访问，例如被复位、断电或不存在。resume 表示 hart 从 Debug Mode 返回普通执行。abstract command 是 DM 提供的高级命令格式，program buffer 是让 halted hart 执行短指令序列的缓冲区。

## 4. Debug Module（DM）

DM 必须提供一组 DMI 寄存器。调试器通过这些寄存器选择 hart、请求 halt/resume、发起 abstract command、读取状态、访问 program buffer 和可选 system bus。DM 可以服务一个 hart，也可以服务多个 hart。

### 4.1 DMI

DMI 是 DTM 与 DM 之间的寄存器访问接口。每次 DMI 操作包含地址、数据和操作类型。DTM 可以返回 busy 或 error，调试器必须按 `dtmcs` 报告的空闲周期和错误状态重试或清除。DMI 访问本身不等同于 hart 内存访问；它只是访问 DM 寄存器。

### 4.2 复位控制

DM 有两类复位相关控制：调试模块自身复位和 hart/system 复位。`dmcontrol.dmactive` 控制 DM 是否激活。清零 `dmactive` 会复位 DM 内部状态，通常也清除认证状态和错误状态。`ndmreset` 请求非调试模块部分复位，具体影响范围由系统实现定义。`hartreset` 可用于复位选中 hart（若实现支持）。

调试器通常先置 `dmactive=1`，等待 `dmstatus.version` 和状态字段有效，再进行认证和 hart 选择。

## 5. Hart 选择

DM 通过 `hartsel` 选择目标 hart。实现报告 `hartsello`/`hartselhi` 字段宽度和 hart 存在状态。调试器可逐个写入 hart 编号，通过 `dmstatus.anynonexistent`、`anyunavail`、`anyhalted` 等字段判断该 hart 是否存在、可用和处于何种状态。

### 5.1 单 hart 选择

单 hart 调试流程通常是：

1. 写 `dmcontrol.hartsel` 选择 hart。
2. 读 `dmstatus` 检查 `anynonexistent` 和 `anyunavail`。
3. 设置 `haltreq` 请求 halt。
4. 轮询 `allhalted` 或 `anyhalted`。
5. 清除 `haltreq`，执行寄存器或内存访问。

### 5.2 多 hart 选择

规范允许实现 hart array mask/window，以便一次选择多个 hart。`hawindowsel` 选择 hart 数组窗口，`hawindow` 中的 bit 表示对应 hart 是否被选择。多 hart 状态通过 `allhalted`、`anyhalted`、`allrunning`、`anyrunning`、`allresumeack` 等字段汇总。调试器在多 hart 操作后应使用 all/any 字段确认所有目标是否到达期望状态。

## 6. 运行控制：halt、resume 和 reset

`dmcontrol.haltreq` 请求选中 hart 进入 Debug Mode。hart 可能在当前指令边界、异常边界或实现定义安全点响应。`dmstatus.anyhalted/allhalted` 表示 hart 已 halted。请求被接受后，调试器应清除 `haltreq`，避免 hart resume 后再次被 halt。

`dmcontrol.resumereq` 请求 halted hart 离开 Debug Mode。hart 完成 resume 后设置 resume acknowledge，`dmstatus.anyresumeack/allresumeack` 可用于确认。调试器通常在看到 ack 后清除 `resumereq`。

`dmcontrol.ackhavereset` 用于确认 hart reset 事件。`dmstatus.anyhavereset/allhavereset` 表示 hart 自上次确认以来经历过 reset。调试器应在连接时处理该状态，避免使用复位前缓存的寄存器值。

## 7. Abstract Command

Abstract command 允许调试器用统一方式访问 hart 寄存器或执行简短动作，而不必手写完整 program buffer。命令写入 `command` 寄存器，参数和结果通过 `data*` 寄存器传递，状态由 `abstractcs` 报告。

### 7.1 `abstractcs`

| 字段 | 含义 |
|---|---|
| `datacount` | 实现的 `data` 寄存器数量 |
| `progbufsize` | program buffer word 数量 |
| `busy` | DM 正在执行 abstract command |
| `cmderr` | abstract command 错误码 |

当 `busy=1` 时，调试器不应写 `command`、`abstractcs.cmderr`、`data*` 或 `progbuf*` 中会影响当前命令的字段。`cmderr` 非零时，调试器必须写 1 清除错误后再发新命令。

常见 `cmderr` 含义：

| 值 | 含义 |
|---|---|
| 0 | 无错误 |
| 1 | busy，命令或寄存器访问时机错误 |
| 2 | 不支持该命令 |
| 3 | 命令执行期间异常 |
| 4 | hart 不可用或未 halted 等状态错误 |
| 5 | 总线错误或访问失败 |
| 7 | 其他错误 |

### 7.2 Access Register command

Access Register 是核心 abstract command。它可读写 GPR、FPR、CSR 或其他寄存器。命令字段通常包含：

| 字段 | 含义 |
|---|---|
| `cmdtype` | 命令类型，Access Register 使用对应编码 |
| `aarsize` | 访问宽度，例如 32/64/128 位 |
| `aarpostincrement` | 访问后自动递增寄存器编号 |
| `postexec` | 访问后执行 program buffer |
| `transfer` | 是否在 `data0` 与目标寄存器之间传输 |
| `write` | 1 表示写寄存器，0 表示读寄存器 |
| `regno` | 目标寄存器编号 |

读寄存器时，DM 把目标寄存器值放入 `data0` 等寄存器；写寄存器时，调试器先写 `data0`，再发命令。若访问宽度不支持、目标寄存器不存在、hart 未 halted 或执行异常，`cmderr` 报错。

### 7.3 Quick Access

Quick Access 允许 DM 暂停 running hart，执行 program buffer，然后自动 resume。它适合非常短的调试动作，但实现复杂且可选。若 hart 无法安全快速进入 Debug Mode，命令会失败。调试器应把它作为优化路径，而不是基本功能依赖。

## 8. Program Buffer

Program buffer 是 DM 中一组指令 word，halted hart 可在 Debug Mode 下执行它们。调试器可用它实现复杂寄存器访问、内存访问、CSR 访问或目标相关操作。`progbufsize` 报告实现提供的 word 数量；为 0 时不可用。

典型用法：

1. 写入 `progbuf0..N` 指令。
2. 根据需要写 `data*` 作为输入。
3. 发 Access Register command，并设置 `postexec=1`。
4. hart 执行 program buffer。
5. 从 `data*` 或寄存器读取结果。

program buffer 执行期间若发生异常，DM 应设置 `cmderr=exception`。调试器需要保证 program buffer 不破坏用户状态，或显式保存/恢复临时寄存器。实现可以在 program buffer 末尾隐式执行返回 Debug Mode 的动作，也可以要求调试器放置合适结束指令，取决于规范和实现约束。

## 9. System Bus Access（SBA）

System Bus Access 允许调试器通过 DM 直接访问系统总线，而不需要 hart 执行加载/存储。它适合 hart halted、unavailable 或尚未初始化时访问内存和外设。SBA 是可选能力，通过 `sbcs` 报告支持情况。

### 9.1 `sbcs`

| 字段 | 含义 |
|---|---|
| `sbaccess8/16/32/64/128` | 支持的访问宽度 |
| `sbaccess` | 当前访问宽度选择 |
| `sbreadonaddr` | 写地址后自动发起读 |
| `sbreadondata` | 读 `sbdata0` 后自动发起下一次读 |
| `sbautoincrement` | 每次访问后地址自增 |
| `sbbusy` | SBA 正忙 |
| `sbbusyerror` | busy 期间发生非法访问 |
| `sberror` | 总线访问错误码 |
| `asize` | system bus 地址宽度 |

地址通过 `sbaddress0..2` 写入，数据通过 `sbdata0..3` 读写。调试器必须等待 `sbbusy=0` 后再检查结果。若 `sberror` 非零，应按写 1 清除规则清除错误，并避免继续使用自动递增状态。

### 9.2 SBA 使用注意

SBA 访问绕过 hart 的普通取指/访存路径，不一定经过同样的缓存、MMU 或 PMP 检查；具体一致性由系统实现定义。调试器在修改正在运行 hart 可见的内存时，应考虑缓存同步和 hart halt 状态。访问设备寄存器时要注意副作用、访问宽度和顺序。

## 10. DM 安全与认证

外部调试可能暴露完整系统控制权，因此规范提供认证机制。`dmstatus.authenticated` 表示调试器是否已通过认证。`authbusy` 表示认证逻辑正忙。`authdata` 是认证交换数据寄存器，具体协议由实现定义。

未认证时，DM 可限制大部分寄存器访问、hart 控制和 SBA。清除 `dmactive`、系统复位或安全策略变化可能使认证失效。实现应避免在未认证状态泄露敏感 hart 状态。调试器应在连接后先检查认证状态，按平台协议完成认证，再执行 halt 或内存访问。

## 11. DM DMI 寄存器字段语义

### 11.1 `dmstatus`

`dmstatus` 是调试器判断系统状态的主寄存器。

| 字段 | 含义 |
|---|---|
| `version` | DM 规范版本；0 表示无兼容 DM |
| `authenticated` | 认证是否通过 |
| `authbusy` | 认证逻辑忙 |
| `hasresethaltreq` | 支持 reset 后 halt 请求 |
| `confstrptrvalid` | 配置字符串指针有效 |
| `allhavereset/anyhavereset` | 所有/任一选中 hart 经历 reset |
| `allresumeack/anyresumeack` | 所有/任一选中 hart 已确认 resume |
| `allnonexistent/anynonexistent` | 选中 hart 是否不存在 |
| `allunavail/anyunavail` | 选中 hart 是否不可用 |
| `allrunning/anyrunning` | 选中 hart 是否 running |
| `allhalted/anyhalted` | 选中 hart 是否 halted |

all 字段要求所有选中 hart 满足条件；any 字段表示至少一个满足。调试器在单 hart 模式下通常使用 any/all 都可，但多 hart 模式必须理解二者差异。

### 11.2 `dmcontrol`

`dmcontrol` 用于发起控制动作。

| 字段 | 含义 |
|---|---|
| `dmactive` | 激活 DM；清零复位 DM |
| `ndmreset` | 请求非 DM 系统复位 |
| `clrresethaltreq` / `setresethaltreq` | 清除/设置 reset 后 halt 请求 |
| `hartselhi/hartsello` | 选择 hart |
| `hasel` | 使用 hart array mask 选择 |
| `ackhavereset` | 确认 havereset 状态 |
| `hartreset` | 请求选中 hart reset |
| `resumereq` | 请求 resume |
| `haltreq` | 请求 halt |

许多控制位是请求型字段，调试器写入后需要轮询 `dmstatus` 确认效果，并在适当时清除请求。

### 11.3 `hartinfo`

`hartinfo` 描述选中 hart 的调试支持细节，例如 `dataaccess`、`datasize`、`dataaddr`。它告诉调试器 abstract data 寄存器是否映射到 hart 地址空间，以及 program buffer 或数据区域如何被 hart 访问。调试器可据此选择寄存器访问和内存访问策略。

### 11.4 `haltsum`、`hawindowsel` 和 `hawindow`

`haltsum` 为大量 hart 提供分级 halted 摘要，便于调试器快速发现哪些 hart 已停止。`hawindowsel` 和 `hawindow` 提供 hart array mask 窗口，用于批量选择 hart。大规模多核系统中，调试器应结合这些寄存器避免逐 hart 轮询造成过高开销。

### 11.5 `abstractauto`

`abstractauto` 可设置访问 `data*` 或 `progbuf*` 时自动执行 `command`。它用于批量寄存器读写，提高 DMI 带宽效率。若自动执行导致错误，`cmderr` 会记录，调试器必须清除后再继续。使用自动执行时要格外避免 busy 期间写入相关寄存器。

### 11.6 `data*` 和 `progbuf*`

`data0..` 是 abstract command 的输入/输出数据寄存器。`progbuf0..` 保存 program buffer 指令。二者数量由 `abstractcs` 报告。访问宽度超过实现能力或 busy 期间非法访问会设置错误。

### 11.7 `authdata`

`authdata` 是认证协议交换寄存器。规范不固定挑战响应算法、密钥或生命周期。实现可将写入 `authdata` 解释为认证请求，并通过读取返回响应或状态。调试器必须按具体平台认证流程使用。

## 12. RISC-V Debug Mode

当 hart halted 时，它进入 Debug Mode。Debug Mode 不是普通特权级；它有自己的控制状态，并能访问普通执行状态。进入 Debug Mode 的原因可能是 `haltreq`、trigger、`EBREAK`、单步完成、reset halt 或异常调试事件。

### 12.1 `dcsr`

`dcsr` 是 Debug Control and Status Register。

| 字段 | 含义 |
|---|---|
| `xdebugver` | 外部调试支持版本 |
| `ebreakm/ebreaks/ebreaku` | 在 M/S/U 模式执行 `EBREAK` 是否进入 Debug Mode |
| `step` | 单步执行使能 |
| `prv` | resume 后目标特权级或当前调试视图特权级 |
| `cause` | 进入 Debug Mode 的原因 |
| `stoptime` | halted 时是否停止计时器 |
| `stopcount` | halted 时是否停止计数器 |

`cause` 常见值包括 ebreak、trigger、haltreq、step 和 resethaltreq。调试器可读取 `dcsr` 判断为何停止，并配置 `step` 实现单步。

### 12.2 `dpc` 和 `dscratch*`

`dpc` 保存 resume 后继续执行的 PC。调试器修改 `dpc` 可改变 resume 地址。`dscratch0` 和 `dscratch1` 是 Debug Mode 临时寄存器，供调试代码或 program buffer 使用。实现可能只提供一个或两个 scratch 寄存器。

### 12.3 `dret`

`dret` 从 Debug Mode 返回普通执行。它把 `pc` 设置为 `dpc`，并按 `dcsr.prv` 和调试状态恢复执行。`dret` 只能在 Debug Mode 中合法执行；普通模式执行应产生非法指令或按实现约束处理。

### 12.4 单步和 LR/SC

单步通过设置 `dcsr.step` 实现。hart resume 后执行一条指令或一个规定步进单位，然后重新进入 Debug Mode。LR/SC 序列在调试事件、单步或 halt 过程中可能失去 reservation；调试器不应假设单步跨越 LR/SC 后 SC 仍会成功。

## 13. Trigger Module

Trigger 用于在满足条件时进入 Debug Mode 或产生其他调试动作。触发条件可基于执行地址、加载/存储地址、数据、特权级或指令计数。trigger CSR 通常包括 `tselect`、`tdata1`、`tdata2`、`tdata3`，不同 trigger 类型复用这些寄存器。

### 13.1 Trigger 选择和数据寄存器

| CSR | 作用 |
|---|---|
| `tselect` | 选择当前访问的 trigger 编号 |
| `tdata1` | trigger 类型、控制字段和动作 |
| `tdata2` | 匹配值，例如地址或数据 |
| `tdata3` | 额外匹配/掩码/链式字段 |

调试器通过枚举 `tselect` 并读取 `tdata1.type` 发现 trigger 数量和类型。写入不支持的类型或字段时，WARL 规则使其读回合法值。

### 13.2 `mcontrol`

`mcontrol` 是常见地址/数据匹配 trigger 类型。字段可指定在执行、load、store 时匹配，选择 M/S/U 特权级，设置 match 模式和 action。action 可进入 Debug Mode 或产生 breakpoint exception，取决于实现支持和配置。

### 13.3 `icount`

`icount` trigger 按退休指令计数触发。它可用于“执行 N 条指令后停止”或实现更精细单步。计数是否包含异常、调试模式指令或压缩指令，需按字段定义和实现行为理解。

## 14. Debug Transport Module（DTM）

DTM 把外部物理调试协议转换为 DMI 访问。本规范重点描述 JTAG DTM。其他传输可定义等价寄存器访问语义。

### 14.1 JTAG DTM

JTAG DTM 使用 JTAG instruction register 选择数据寄存器，包括 `IDCODE`、`dtmcs`、`dmi` 和 `BYPASS`。调试器通过扫描 `dmi` 寄存器提交 DMI 操作，再读取响应。DTM 可要求操作之间插入 idle 周期，数量由 `dtmcs.idle` 报告。

### 14.2 `dtmcs`

| 字段 | 含义 |
|---|---|
| `version` | DTM 版本 |
| `abits` | DMI 地址位宽 |
| `dmistat` | DMI sticky error/busy 状态 |
| `idle` | 建议 DMI 访问间 idle 周期 |
| `dmireset` | 清除 DMI 错误状态 |
| `dmihardreset` | 更强 DMI/DM 复位请求 |

若 DMI 返回 busy 或 error，调试器应通过 `dtmcs` 清除状态，并降低访问速率或插入更多 idle。

### 14.3 `dmi`

`dmi` 数据寄存器包含 address、data 和 op。op 表示 nop、read 或 write。响应中 op 字段报告 success、failed 或 busy。调试器必须处理 sticky busy：一旦出现 busy，后续操作可能继续失败，直到执行 reset/清除序列。

## 15. 硬件实现建议

最小可用实现应支持：DM 激活、单 hart 选择、halt/resume、`dmstatus`/`dmcontrol`、基本 Access Register、足够的 `data` 寄存器，以及必要的 Debug Mode CSR。若没有 program buffer，调试器仍可通过 abstract register 访问完成基本调试；若没有 SBA，内存访问可通过 halted hart 执行 load/store 序列实现。

较完整实现可增加 program buffer、SBA、多 hart mask、trigger、reset halt、认证和 haltsum。实现应确保 DM 寄存器在 hart reset、system reset、DM reset 和认证状态变化时行为清晰，避免调试器读到半更新状态。跨时钟域 DMI、hart 和系统总线之间必须正确同步 busy、错误和完成信号。

## 16. 调试器实现流程

典型连接流程：

1. 通过 DTM 读取 `dtmcs`，确认 DMI 地址宽度和版本。
2. 写 `dmcontrol.dmactive=1`。
3. 读取 `dmstatus.version`，确认 DM 存在。
4. 若 `authenticated=0`，通过 `authdata` 完成认证。
5. 枚举 hart，过滤 nonexistent/unavailable。
6. 对目标 hart 写 `haltreq`，轮询 `allhalted`。
7. 读取 `dcsr`、`dpc`、GPR 和必要 CSR。
8. 设置 breakpoints/triggers 或执行单步。
9. 修改 `dpc` 或寄存器后写 `resumereq`，等待 `resumeack`。

内存访问策略按能力选择：优先 SBA（若一致性和权限合适），其次 program buffer load/store，再次 abstract command 的实现特定路径。错误处理要始终先检查 `cmderr`、`sberror` 和 DMI sticky error，清除后再继续。

## 17. 异常条件和鲁棒性

调试器必须处理以下条件：

- 选中 hart 不存在或不可用。
- hart 在命令期间 reset。
- abstract command 不支持或执行异常。
- program buffer 指令触发异常。
- SBA 总线访问错误或 busy 期间误访问。
- DMI 返回 busy/error。
- 认证失效或权限不足。
- 多 hart 操作中只有部分 hart halt/resume 成功。

实现应尽量通过状态字段报告错误，而不是让 DMI 长期无响应。调试器应使用超时、重试和状态清除逻辑，避免在 busy 状态下继续写破坏命令序列。

## 18. 翻译完成状态

本文件已从入口/摘要稿改为 External Debug 中文正文译文稿，覆盖 Debug Module、Debug Transport、DMI/JTAG、hart 选择与控制、halt/resume/reset、abstract command、program buffer、system bus access、debug registers、trigger、认证、安全、异常条件、寄存器字段语义、调试器流程和硬件实现注意事项。
