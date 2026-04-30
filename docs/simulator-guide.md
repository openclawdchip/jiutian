# 模拟器指南

九天 v0.1 模拟器是功能模型，用于验证 APU-IR、Agent ISA、SPM、Cluster SRAM、DMA、barrier、capability 和任务边界。

## 当前支持能力

- 多任务 round-robin 调度。
- SPM 与 Cluster SRAM 读写。
- host memory capability 检查。
- DMA copy 与 DMA wait。
- barrier 阻塞、释放与 deadlock 检测。
- flush、invalidate、fence trace。
- cycle budget 检查。
- JSON trace 输出。

## 运行命令

```powershell
python simulator\jiutian_sim.py simulator\examples\copy_add.json
python simulator\jiutian_sim.py simulator\examples\cluster_barrier.json --trace
```

## 设计边界

当前模型不是周期精确模型。DMA 可以先按同步完成处理；异步 DMA、队列深度、NoC 延迟和能耗 proxy 属于后续扩展。

## 正确性标准

一个示例至少应验证：

- 输出内存结果正确。
- 未发生非预期 trap。
- trace 中包含关键调度和数据搬运事件。
