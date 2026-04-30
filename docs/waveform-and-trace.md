# Trace 与波形

v0.1 阶段优先使用 trace 描述行为。RTL 阶段再补充波形约定。trace 是九天早期验证的核心，因为它能把 Agent task 的调度、数据搬运、同步和异常变成可读事件。

## 1. Trace 的作用

Trace 用来回答：

- task 是否按预期启动？
- round-robin 调度是否正确？
- DMA 是否从正确源搬到正确目的？
- barrier 是否阻塞和释放？
- SPM/Cluster SRAM 数据是否按预期流动？
- capability 违规是否被捕获？
- deadlock 是否被检测？

## 2. 当前使用方式

运行示例并输出 trace：

```powershell
python simulator\jiutian_sim.py simulator\examples\cluster_barrier.json --trace
```

输出中会出现：

```text
consumer barrier stage0 arrived=1/2
producer barrier stage0 arrived=2/2
barrier stage0 release consumer,producer
```

这表示 consumer 先到 barrier 并等待，producer 到达后释放双方。

## 3. 当前 Trace 内容

当前 trace 是字符串列表，包含：

- task start。
- 指令执行。
- DMA copy。
- DMA wait。
- flush。
- invalidate。
- fence。
- barrier arrive。
- barrier release。
- task completed。
- trap。
- scheduler trap。

## 4. 推荐结构化事件

后续 trace 应升级为 JSON event：

```json
{
  "schema": "jiutian.trace.v0.1",
  "seq": 8,
  "cycle": 8,
  "task": "producer",
  "cluster": 0,
  "core": 0,
  "pc": 6,
  "event": "barrier_arrive",
  "detail": {
    "barrier": "stage0",
    "arrived": 2,
    "participants": 2
  }
}
```

## 5. Trace 事件与调试动作

| 场景 | 应观察事件 |
|---|---|
| task 启动 | `task_start` |
| 普通指令执行 | `instruction` |
| SPM 读取 | `memory_load` |
| SPM 写入 | `memory_store` |
| DMA 搬运 | `dma_copy` |
| 同步等待 | `barrier_arrive` |
| 同步释放 | `barrier_release` |
| 显式可见性 | `flush` / `invalidate` / `fence` |
| 正常结束 | `halt` |
| 异常 | `trap` |
| 死锁 | `deadlock` |

## 6. Trace Summary

后续工具应能从 trace 生成 summary：

- 总 task 数。
- 完成 task 数。
- trap task 数。
- 指令数。
- DMA 次数。
- DMA 总字节数。
- barrier 次数。
- deadlock 次数。
- 每个 task 的等待次数。

这些 summary 可以作为 benchmark 初期指标。

## 7. 波形规划

RTL 阶段应提供波形观测点：

- task dispatch valid/ready。
- Agent core pc。
- SPM read/write。
- Cluster SRAM read/write。
- DMA request/response。
- barrier arrive/release。
- trap valid。
- interrupt pending。
- trace event valid。

波形信号命名应稳定，并与 trace event 能够对应。

## 8. Trace 与波形的关系

trace 是行为级记录，适合软件和架构评审。波形是信号级记录，适合 RTL bring-up。

推荐调试流程：

1. 先用 trace 判断行为是否符合规格。
2. 如果 trace 不符合预期，再用波形定位信号级原因。
3. 如果波形正确而 trace 错误，检查 trace 采集逻辑。
4. 如果 trace 正确而输出错误，检查 memory dump 或测试断言。

## 9. 文件输出规划

后续建议：

```text
reports/
  simulator/
    copy_add.trace.json
    copy_add.summary.json
  rtl/
    cluster_barrier.vcd
```

生成结果不应提交到源码仓库，除非作为小型 golden reference。
