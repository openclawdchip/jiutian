# 文件清单与 Manifest

本文档定义九天工程中文件清单的职责和维护方式。

## 目标

文件清单用于让模拟器、测试、benchmark 和未来 RTL 构建流程拥有稳定入口。

## Manifest 类型

- simulator manifest：声明示例、测试和输入 IR。
- benchmark manifest：声明 workload、baseline、规模和指标。
- rtl manifest：后续声明 RTL 源文件、include 路径和模块边界。
- docs manifest：声明文档导航与版本状态。

## 建议格式

```json
{
  "version": "0.1",
  "kind": "simulator",
  "entries": [
    {"name": "copy_add", "path": "simulator/examples/copy_add.json"}
  ]
}
```

## 维护规则

- manifest 只描述入口，不复制规格内容。
- 路径应相对仓库根目录。
- 删除或重命名文件时必须同步更新 manifest。
