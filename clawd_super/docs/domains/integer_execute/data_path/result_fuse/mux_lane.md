# Mux Lane

## 角色

这一层负责结果总线上的选择逻辑。它把多个候选结果按 one-hot 或优先级规则合成为最终写回数据。

## 输入

- `sources`：候选结果集合。
- `selects`：选择信号。
- `valid`：本地结果有效位。

## 输出

- `data`
- `valid`
- `source`
- `diagnostics`

## 处理流程

1. 选择低半和高半结果。
2. 在本地与 transfer 之间做接管判断。
3. 记录冲突、缺源和优先级赢家。
4. 输出 64-bit 写回结果。

## 行为模型接口

- `select_full`
- `select_half`
- `onehot_select`
- `result_channel`
