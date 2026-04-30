# 配置与生成流程

九天 v0.1 采用“规格先行、模拟器验证、RTL 固化”的配置流程。

## 配置目标

配置系统用于描述目标实例的核心数量、SPM 容量、Cluster SRAM 容量、任务预算、trace 粒度和后续 RTL 参数。

## 配置输入

v0.1 的配置入口可以先放在 APU-IR 顶层 `config` 字段中：

```json
{
  "config": {
    "host_bytes": 64,
    "cluster_bytes": 1024,
    "spm_bytes": 1024
  }
}
```

## 可配置项

- host memory 大小。
- Cluster SRAM 大小。
- 每核 SPM 大小。
- 调度策略。
- trace 输出级别。
- DMA 延迟模型。

## 生成物

配置流程后续可生成：

- 模拟器配置快照。
- benchmark 运行配置。
- RTL 参数头文件。
- 文档化的配置报告。

## 覆盖规则

自动生成文件必须在文件头注明来源与生成命令。手写规格文档不得被配置工具覆盖。
