# Field Lane

## 角色

这一层负责位域抽取、插入和移动。它把 bitfield 类操作统一成一个可执行的组合行为，覆盖抽取、插入、wrap 和符号扩展。

## 输入

- `src`：源数据。
- `dst`：目标数据。
- `lsb`：字段起点。
- `width`：字段宽度。
- `immr` / `imms`：移动控制量。
- `signed_extract`：是否符号扩展。
- `insert`：是否保留目标旧值。

## 输出

- `result`：最终结果。
- `mask`：字段掩码。
- `rotated`：旋转后的中间值。
- `width`：有效字段宽度。

## 状态

- 纯组合逻辑。
- 需要同时观察目标旧值和旋转源值，才能覆盖 BFM/BFI/SBFM/UBFM。

## 处理流程

1. 生成字段掩码。
2. 对源做循环右移或直接抽取。
3. 需要时按字段最高位做符号扩展。
4. `insert=True` 时把结果写回目标掩码外的旧位。

## 边界

- 字段宽度为 0 时返回 0。
- 字段起点超出可见宽度时返回 0。
- wrap 形式和非 wrap 形式的结果窗口不同，不能混用。

## 行为模型接口

- `bitfield_insert`
- `bitfield_extract`
- `bitfield_move`
