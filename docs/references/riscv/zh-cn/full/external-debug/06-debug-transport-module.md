# 第 6 章 Debug Transport Module (DTM)

Debug Transport Module 通过一种或多种 transport（例如 JTAG 或 USB）提供对 DM 的访问。

单个平台中可以有多个 DTM。理想情况下，每个与外界通信的组件都包含一个 DTM，使平台能够通过它支持的每种 transport 进行调试。例如 USB 组件可以包含 DTM。这样可以直接允许任何平台通过 USB 调试。唯一要求是正在使用的 USB module 也能访问 Debug Module Interface。

不支持同时使用多个 DTM。用户需要确保这不会发生。

本规范在第 6.1 节定义 JTAG DTM。未来版本可能增加更多 DTM。

## 6.1 JTAG Debug Transport Module

该 Debug Transport Module 基于普通 JTAG Test Access Port（TAP）。JTAG TAP 允许访问任意 JTAG register：先用 JTAG instruction register（IR）选择一个 register，然后通过 JTAG data register（DR）访问它。

### 6.1.1 JTAG Background

JTAG 指 IEEE Std 1149.1-2013。它是一个标准，定义可包含在集成电路中的测试逻辑，用于测试集成电路之间的互连、测试集成电路本身，以及在组件正常操作期间观察或修改电路活动。本规范使用后一种功能。JTAG 标准定义 Test Access Port（TAP），可用来读写少量 custom register，这些 register 可用于与组件中的 debug hardware 通信。

### 6.1.2 JTAG DTM Registers

用作 DTM 的 JTAG TAP 必须具有至少 5 bit 的 IR。当 TAP reset 时，IR 必须默认值为 `00001`，选择 `IDCODE` instruction。JTAG register 及其编码完整列表见表 6.1。如果 IR 实际超过 5 bit，则表 6.1 中的编码应在最高有效 bit 侧用 0 扩展。debugger 可能使用的常规 JTAG register 只有 `BYPASS` 和 `IDCODE`，但本规范为许多其他标准 JTAG instruction 保留 IR 空间。未实现的 instruction 必须选择 `BYPASS` register。

表 6.1：JTAG DTM TAP Registers

| Address | Name | Description |
|---|---|---|
| `0x00` | `BYPASS` | JTAG recommends this encoding |
| `0x01` | `IDCODE` | JTAG recommends this encoding |
| `0x10` | DTM Control and Status | For Debugging |
| `0x11` | Debug Module Interface Access | For Debugging |
| `0x12` | Reserved (`BYPASS`) | Reserved for future RISC-V debugging |
| `0x13` | Reserved (`BYPASS`) | Reserved for future RISC-V debugging |
| `0x14` | Reserved (`BYPASS`) | Reserved for future RISC-V debugging |
| `0x15` | Reserved (`BYPASS`) | Reserved for future RISC-V standards |
| `0x16` | Reserved (`BYPASS`) | Reserved for future RISC-V standards |
| `0x17` | Reserved (`BYPASS`) | Reserved for future RISC-V standards |
| `0x1f` | `BYPASS` | JTAG requires this encoding |

### 6.1.3 `IDCODE` (at `0x01`)

TAP state machine reset 时，该 register 在 IR 中被选中。其定义与 IEEE Std 1149.1-2013 中的定义完全相同。整个寄存器只读。

字段：

| Field | Description | Access | Reset |
|---|---|---|---|
| `Version` | 标识该 part 的 release version。 | R | Preset |
| `PartNumber` | 标识该 part 的 designer part number。 | R | Preset |
| `ManufId` | 标识该 part 的 designer/manufacturer。bit 6:0 必须是 JEDEC Standard JEP106 分配的 designer/manufacturer Identification Code 的 bit 6:0。bit 10:7 包含同一 Identification Code 中 continuation character（`0x7f`）数量的 modulo-16 count。 | R | Preset |

### 6.1.4 DTM Control and Status (`dtmcs`, at `0x10`)

该寄存器大小在未来版本中将保持不变，使 debugger 总能确定 DTM 的 version。

字段：

| Field | Description | Access | Reset |
|---|---|---|---|
| `dmihardreset` | 向该 bit 写 1 对 DTM 执行 hard reset，使 DTM 忘记任何 outstanding DMI transaction。通常只有当 Debugger 有理由认为 outstanding DMI transaction 永远不会完成时才应使用，例如 reset condition 导致 inflight DMI transaction 被取消。 | W1 | 0 |
| `dmireset` | 向该 bit 写 1 清除 sticky error state，并允许 DTM retry 或 complete 前一个 transaction。 | W1 | 0 |
| `idle` | 给 debugger 的 hint：为了避免返回 `busy` code（`dmistat` 为 3），每次 DMI scan 后 debugger 应在 Run-Test/Idle 中花费的最小 cycle 数。debugger 仍必须在必要时检查 `dmistat`。0：完全不需要进入 Run-Test/Idle。1：进入 Run-Test/Idle 后立即离开。2：进入 Run-Test/Idle 并停留 1 cycle 后离开。依此类推。 | R | Preset |
| `dmistat` | 0：无错误。1：保留，按 2 解释。2：操作失败（导致 `op` 为 2）。3：在 DMI access 仍在进行时尝试操作（导致 `op` 为 3）。 | R | 0 |
| `abits` | `dmi` 中 address 的大小。 | R | Preset |
| `version` | 0：spec version 0.11 中描述的版本。1：spec version 0.13（以及 later?）中描述的版本，它把 DMI data width 减少到 32 bit。15：不由本规范任何可用版本描述的版本。 | R | 1 |

### 6.1.5 Debug Module Interface Access (`dmi`, at `0x11`)

该 register 允许访问 Debug Module Interface（DMI）。

在 Update-DR 中，除非 `op` 中报告的当前 status 为 sticky，否则 DTM 开始 `op` 指定的 operation。

在 Capture-DR 中，DTM 用该 operation 的结果更新 `data`，并且如果当前 `op` 不是 sticky，则更新 `op`。

用法示例见第 B.1 节和表 B.1。

still-in-progress status 是 sticky 的，以适配把若干 scan batch 在一起的 debugger；这些 scan 必须全部执行，或在出现问题时立即停止。例如，一系列 scan 可能写入 Debug Program 并执行它。如果某个写失败但执行继续，则 Debug Program 可能 hang 或产生其他非预期副作用。

字段：

| Field | Description | Access | Reset |
|---|---|---|---|
| `address` | DMI access 使用的 address。在 Update-DR 中，该值用于通过 DMI 访问 DM。 | R/W | 0 |
| `data` | Update-DR 期间通过 DMI 发送给 DM 的 data，以及作为前一 operation 结果从 DM 返回的 data。 | R/W | 0 |
| `op` | debugger 写该字段时：0 忽略 `data` 和 `address`（nop），Update-DR 期间不通过 DMI 发送任何内容；该 operation 不应导致 busy 或 error response，下一次 Capture-DR 中报告的 address 和 data 未定义。1 从 `address` read。2 把 `data` write 到 `address`。3 保留。debugger 读该字段时：0 前一个 operation 成功完成。1 保留。2 前一个 operation failed；本次 access 扫入 `dmi` 的 data 将被忽略。该 status 是 sticky，可通过写 `dtmcs` 中 `dmireset` 清除。这表示 DM 本身响应 error。注意：没有规定 DM 会响应 error 的具体情况，且 DMI 不要求支持返回 error。3 在 DMI request 仍在进行时尝试 operation；本次 access 扫入 `dmi` 的 data 将被忽略。该 status 是 sticky，可通过写 `dtmcs` 中 `dmireset` 清除。如果 debugger 看到该 status，需要在 Update-DR 和 Capture-DR 之间给 target 更多 TCK edge。最简单方式是在 Run-Test/Idle 中增加额外 transition。（DTM、DM 并/或 component 可能在不同 clock domain，因此可能需要 synchronization。request 到达 DM、完成并把 response 同步回 TCK domain 可能需要相对固定数量的 TCK tick。） | R/W | 2 |

### 6.1.6 `BYPASS` (at `0x1f`)

1-bit register，没有效果。当 debugger 不想与该 TAP 通信时使用。整个寄存器只读，值为 0。

### 6.1.7 Recommended JTAG Connector

为了便于获取 debug hardware，本规范建议使用与 Atmel AVR JTAG Connector 兼容的 connector，如下所述。

connector 是 .05 英寸间距、镀金 male header，带 .016 英寸厚 hardened copper 或 beryllium bronze 方形针脚（SAMTEC FTSH-105 或等效产品）。female connector 兼容 20 微米 gold connector。

从上方观察 male header（针脚朝向眼睛），target 的 connector 如表 6.2。每个 pin 的功能见表 6.3。

表 6.2：JTAG Connector Diagram

| 左 | Pin | Pin | 右 |
|---|---:|---:|---|
| TCK | 1 | 2 | GND |
| TDO | 3 | 4 | VCC |
| TMS | 5 | 6 | (SRSTn) |
| (NC) | 7 | 8 | (TRSTn) |
| TDI | 9 | 10 | GND |

表 6.3：JTAG Connector Pinout

| Pin | Signal | Description |
|---|---|---|
| 1 | TCK | JTAG TCK signal，由 debug adapter 驱动。该 pin 在 male 和 female header 中都必须清楚标记。 |
| 5 | TMS | JTAG TMS signal，由 debug adapter 驱动。 |
| 9 | TDI | JTAG TDI signal，由 debug adapter 驱动。 |
| 3 | TDO | JTAG TDO signal，由 target 驱动。 |
| 8 | TRSTn | Test Reset（可选，只由某些 device 使用。用于 reset JTAG TAP Controller）。 |
| 4 | VCC | logic high 的 reference voltage。debug adapter 可以尝试从该 pin 拉取最多 20mA 为自身供电，但 target 没有义务提供该电源。 |
| 2, 10 | GND | target ground。 |
| 6 | SRSTn | active-low reset signal，由 debug adapter 驱动。assert reset 应 reset 任何 RISC-V core 以及 PCB 上的任何其他 peripheral。它不应 reset debug logic。虽然连接该 pin 是可选的，但建议连接，因为它允许 debugger 把 target device 保持在 reset state，这对调试某些场景可能必不可少。如果 target 未实现该 pin，则该 pin 不得连接。 |

target connector 可以带 shroud。在这种情况下，key slot 应位于 pin 5 旁边。female header 应有匹配的 key。

debug adapter 应加标签或标记其 isolation voltage threshold（即 unisolated、250V 等）。

除 GND 外，所有 debug adapter pin 都应限流到 20mA。
