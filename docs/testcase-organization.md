# 测试用例组织

测试用例用于验证规格、模拟器和未来 RTL 的行为一致性。

## 目录结构

```text
simulator/examples/       # 可读示例
simulator/test_simulator.py
benchmarks/               # benchmark 定义
```

## 命名规则

- 示例使用描述性名称，例如 `copy_add.json`。
- 多任务同步示例应包含同步机制名称，例如 `cluster_barrier.json`。
- 负向测试应在名称中包含错误类型。

## 最小测试要求

每个测试应说明：

- 输入 memory。
- 任务数量。
- 使用的指令。
- 预期输出。
- 是否预期 trap。

## 新增测试流程

1. 新增 APU-IR JSON。
2. 在单元测试中声明预期输出。
3. 如涉及新语义，同步更新规格覆盖矩阵。
