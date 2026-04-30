# RISC-V 开放规范参考

本目录保存九天 APU 设计过程中需要参考的 RISC-V 开放规范文档镜像。

这些文档不是九天项目原创内容，版权、商标和许可证归各自发布方所有。九天项目仅将其作为开放规范参考资料保存，便于离线阅读、交叉检查和规格对齐。

## 文档清单

| 文件 | 用途 |
|---|---|
| `The_RISC-V_Instruction_Set_Manual_Volume_I_Unprivileged_ISA_TD004_20191213.pdf` | RISC-V 非特权 ISA 基础参考 |
| `The_RISC-V_Instruction Set_Manual_Volume_II_Privileged_Architecture_TD005_V20190608.pdf` | RISC-V 特权架构参考 |
| `RISC-V_Vector_ISA-extensions_V1.0.pdf` | RISC-V Vector 扩展参考 |
| `RISC-V_Bit-Manipulation_ISA-extensions_TD013_V1.0.0-38-g865e7a7.pdf` | RISC-V Bit-Manipulation 扩展参考 |
| `RISC-V_External Debug_Support_TD003_V0.13.pdf` | RISC-V 外部调试参考 |
| `RISC-V_Processor_Trace_TD010_V1.0.pdf` | RISC-V Processor Trace 参考 |

## 在九天中的使用原则

- 控制面优先保持 RISC-V 兼容性。
- Agent 执行面可以定义九天专用语义，但应明确与 RISC-V 语义的边界。
- 调试、trace、异常和特权行为应尽量复用开放规范中成熟的概念。
- 任何从开放规范中借鉴的行为都应在九天 specs 中重新表述为九天自己的可实现语义。

## 不放入本目录的内容

- 厂商私有数据手册。
- 非开放授权文档。
- 与九天设计无关的外设资料。
- 无法确认来源或授权状态的文件。
