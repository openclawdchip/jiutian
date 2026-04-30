# Chapter 8 Future Directions

当前重点是 compressed branch trace；不过，还有许多其他类型的 processor trace 会很有用（下面不按特定顺序列出）。在当前 scope 完成后，应考虑把这些作为未来可能添加的 features。

## 8.1 Data trace

trace encoder 将输出 packets，以便向 off-chip decoder 传达 loads 和 stores 相关信息。为了减少所需 bandwidth，报告 data values 将是 optional；当这样做有益时，address 和 data 都可以 differential 方式编码。这意味着输出 new value 与同一 transfer size 的 previous value 之间的 difference，而不考虑 transfer direction。

Unencoded values 将用于 synchronisation 以及其他时刻。

## 8.2 Fast profiling

在该 mode 中，encoder 将提供一种 non-intrusive 替代方案，用来替代 traditional profiling method；传统方法要求 processor 周期性 halted，以便采样 program counter。encoder 会在检测到 exception、call 或 return 时发出 packets，用于报告下一条 executed instruction，也就是 destination instruction。可选地，encoder 还可以报告 current instruction，也就是 source instruction。

## 8.3 Inter-instruction cycle counts

在该 mode 中，encoder 会通过报告连续 instruction retirements 之间的 cycles 数量，trace hart stall 的位置。

## 8.4 Transport

当前 charter 满足之后，应定义并 standardise transport mechanism。这将包括基于 Aurora 的 serdes、PCIe 和 Ethernet。
