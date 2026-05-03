# Shift Lane

## 角色

这一层负责逻辑移位和算术移位。它是所有带移位语义指令的通用数据通路，同时也要提供移位移出位给 carry/flag 路径使用。

## 输入

- `value`：待移位值。
- `amount`：移位位数。
- `op`：`lsl` / `lsr` / `asr`。
- `width`：数据宽度。
- `old_flags`：旧标志，用于 `rrx` 和 flag-uop 路径。
- `old_carry`：旧 C 位，用于零移位保留。

## 输出

- `result`：移位结果。
- `flags`：抽象 NZCV。
- `carry_out`：移出位。

## 状态

- 纯组合逻辑，但 `old_flags` 是真实输入状态。
- `rrx` 和 flag-uop 依赖旧 C 位，因此不能只看结果值。

## 处理流程

1. 将移位量归一化到目标位宽。
2. 根据操作类型执行左移、逻辑右移或算术右移。
3. 当移位量为 0 时保留旧 C。
4. 生成结果和 carry-out 观察值。

## 边界

- 移位量大于等于位宽时，逻辑移位清零，算术右移按符号位补齐。
- `rrx` 始终按 1 位旋转。
- `shift_rmif_flags` 只用于 flag-uop 观察。

## 行为模型接口

- `lsl`
- `lsr`
- `asr`
- `shift_carry_out`
- `shift_with_flags`
- `shift_rmif_flags`
