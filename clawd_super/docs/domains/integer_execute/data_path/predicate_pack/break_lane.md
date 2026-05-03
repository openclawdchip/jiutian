# Break Lane

## 角色

这一层负责 break / next 类谓词控制。它用 governing predicate 限定扫描范围，并在找到第一个 break 点后生成停止或合并后的谓词结果。

## 输入

- `pg`：governing predicate。
- `ps1` / `ps2`：前后段谓词。
- `op`：break 变体。

## 输出

- `result`：break 后的谓词。
- `first_active`：第一个 active lane。
- `last_active`：最后一个 active lane。

## 处理流程

1. 找到 governing predicate 中的有效 lane。
2. 从低 lane 向高 lane 扫描第一个 break 位置。
3. 按 A/B 变体决定是否包含 break lane。
4. 对 merge 变体叠加另一段谓词。

## 边界

- governing predicate 为空时结果为空。
- 没有 break 点时保留所有有效 lane。

## 行为模型接口

- `break_predicate`
- `first_active_onehot`
- `last_active_onehot`
