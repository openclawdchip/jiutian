# 快速开始

本文档说明如何在本地运行九天 APU v0.1 的最小功能模型。

## 前置条件

- Python 3.10 或更新版本。
- Git。
- 能够在仓库根目录执行命令。
- 已获取完整仓库源码。

## 最小运行路径

```powershell
python simulator\jiutian_sim.py simulator\examples\copy_add.json
```

预期输出中应包含 `host_words`，并且地址 `8` 对应的结果为 `42`。

## 查看 Trace

```powershell
python simulator\jiutian_sim.py simulator\examples\copy_add.json --trace
```

trace 用于观察任务调度、DMA、SPM/Cluster SRAM 访问、barrier 和异常行为。

## 运行测试

```powershell
python -m unittest discover simulator
```

## 下一步

- 阅读 `docs/simulator-guide.md` 理解模拟器边界。
- 阅读 `specs/v0.1/implementation-coverage.md` 查看规格覆盖情况。
- 阅读 `docs/testcase-organization.md` 学习如何新增测试。
