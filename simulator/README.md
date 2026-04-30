# 模拟器

本目录将包含九天 APU v0.1 目标的功能模拟器。

初始模拟器目标：

- 建模一个 Agent 集群。
- 执行最小指令集。
- 跟踪 SPM 与 Cluster SRAM 访问。
- 抽象建模 DMA 延迟。
- 输出内存搬运、Barrier 和任务调度 trace。

模拟器是本项目的第一个可执行产物。

## 当前实现

`jiutian_sim.py` 是 v0.1 功能模拟器，支持：

- `li`、`add`、`sub`、`jmp`、`beqz`、`halt`、`trap`
- `load`、`store`
- `dma_copy`、`dma_wait`
- `barrier`
- `flush`、`invalidate`、`fence`
- host capability 检查
- SPM / Cluster SRAM 边界检查
- JSON trace 输出

## 运行示例

```powershell
python simulator\jiutian_sim.py simulator\examples\copy_add.json
```

输出中 `host_words["8"]` 应为 `42`。

查看完整 trace：

```powershell
python simulator\jiutian_sim.py simulator\examples\copy_add.json --trace
```

运行包含 Cluster SRAM 与 Barrier 的示例：

```powershell
python simulator\jiutian_sim.py simulator\examples\cluster_barrier.json --trace
```

运行测试：

```powershell
python -m unittest discover simulator
```

## 设计边界

当前模拟器是顺序功能模型，不是周期精确模型。`barrier` 目前记录同步语义，
但不实现真正的并发阻塞调度。下一阶段会加入 round-robin 多任务执行器。
