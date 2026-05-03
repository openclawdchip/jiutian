# Platform Control And Debug

## 1. 角色

platform control and debug 负责朱雀的非功能主线控制，包括中断、调试、追踪、时钟复位、功耗控制和平台服务入口。

## 2. 范围

- interrupt control
- debug entry and halt control
- trace and tarmac-style observation
- clock/reset control
- service control register block
- watchdog / safety hook

## 3. 边界

这个域不负责执行主数据路径，但它会影响所有域的 enable、flush、halt 和可观测性。

## 4. 输入输出

| 输入 | 说明 |
|---|---|
| external interrupt/service events | 来自 SoC 和外设 |
| internal fault / trace events | 来自 core、cluster、cache |

| 输出 | 说明 |
|---|---|
| interrupt injection | 发往 core |
| halt/debug request | 发往 ifetch、commit、execute |
| reset / gate control | 发往全局模块 |
| trace stream | 输出给观测链路 |

## 5. Floorplan 视角

### 5.1 物理目标

platform control and debug 不是放在核心中央的一堆管理逻辑，而是一条围绕 core、tile 和 cluster 外围延展的 service spine。它的目标是提供控制、观测和维护能力，同时不侵入高频执行热区。

### 5.2 推荐分区

- interrupt 注入口靠近 commit/redirect 脊柱，缩短精确进入和重定向返回。
- debug halt、single-step、resume 控制贴近前端与退休控制的边界，而不是深入执行簇内部。
- trace 聚合器和性能计数采样点沿外围汇集，再送入独立观测链路。
- clock/reset、watchdog 和 service CSR 位于 core 或 tile 边界，承担分层广播与接入。

### 5.3 时序约束

- trace、PMU、service readback 和诊断观察口不得回灌主执行热路径。
- reset、halt 和 quiesce 广播需要明确分级，不假定单点直接扇出到全芯片。
- 服务类寄存器访问和主 request/response 通路物理分离。

### 5.4 对后续模型的约束

- 行为模型需要体现 interrupt/debug 的注入边界、分层广播和外围采样。
- RTL 应把 intctrl、debug、trace、clock/reset、service csr 作为相互解耦的外围控制簇。

## 6. 行为模型落点

行为模型应覆盖：

- interrupt pending / ack
- debug halt / resume
- reset broadcast
- trace event 收集
- 可观测状态寄存器抽象

## 7. RTL 落点

RTL 可拆为：

- intctrl
- debug control
- trace control
- clk_rst
- service csr
- platform control top

## 8. 二级文档

- `platform_control_debug/README.md`
- `platform_control_debug/interrupt_debug_and_trace.md`
- `platform_control_debug/reset_clock_and_service_control.md`

## 9. 模块文档

- `platform_control_debug/README.md`
- `platform_control_debug/INDEX.md`
- `platform_control_debug/data_path/README.md`
- `platform_control_debug/control_path/README.md`
- `platform_control_debug/top_mixed/README.md`
