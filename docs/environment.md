# 环境要求

本文档定义九天 APU v0.1 的本地开发与验证环境。

## 支持平台

当前优先支持 Windows PowerShell 与常见类 Unix shell。所有命令应尽量保持跨平台。

## 必需依赖

- Python 3.10+
- Git
- 标准命令行环境

## 建议环境变量

```text
JIUTIAN_HOME=<仓库根目录>
```

该变量仅作为命令书写便利项，工具不应强依赖它存在。

## 检查命令

```powershell
python --version
python -m unittest discover simulator
```

## 可选依赖

后续 RTL、波形、性能分析和文档渲染工具应在对应文档中单独声明，不应成为运行 v0.1 模拟器的前置条件。
