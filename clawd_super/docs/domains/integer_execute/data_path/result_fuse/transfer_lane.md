# Transfer Lane

## 角色

这一层负责本地结果与跨簇 transfer 结果之间的接管关系。它定义了结果何时由本地 pipe 直接写回，何时由远端转移结果填充。

## 输入

- `local_valid` / `local_data`：本地结果。
- `transfer_valid` / `transfer_data`：远端候选结果。
- `transfer_priority`：远端优先级。

## 输出

- `data`：最终输出结果。
- `valid`：输出有效位。
- `source`：实际被选中的来源。

## 处理流程

1. 本地有效时优先使用本地结果。
2. 本地无效时按 transfer 优先级选择远端结果。
3. 多个 transfer 同时有效时保留诊断信息。
4. 输出冲突、屏蔽和缺源观测字段。

## 行为模型接口

- `select_with_transfer_priority`
- `pass2_transfer_e1_next`
