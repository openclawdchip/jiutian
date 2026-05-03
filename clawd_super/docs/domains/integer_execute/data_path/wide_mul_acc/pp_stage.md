# Partial Product Stage

## 角色

这一层负责部分积选择与补码修正。它既要产出 66 位部分积，也要给出 carry-correction，保证负部分积在压缩树里数学上正确。

## 输入

- `sgnb`：符号解释开关。
- `neg`：负路径修正位。
- `bsel`：Booth 选择码。
- `src`：被乘数片段。

## 输出

- `partial_product`：66 位部分积。
- `carry_correction`：补码修正位。
- `mathematical_partial_product`：数学真值。

## 状态

- 纯组合逻辑。
- 不保留压缩树内部的 carry-save 层级。

## 处理流程

1. 根据 Booth 编码选择正/负和 1x/2x 路径。
2. 对正部分积直接拼接对齐位。
3. 对负部分积生成按位取反形态。
4. 输出 carry 修正位，交给压缩树补回 +1。

## 边界

- `bsel` 的非法组合按 OR 语义解释。
- `sgnb` 只影响乘数解释方式，不改变控制码本身。
- 负部分积的 `+1` 不在这里完成，而是在压缩树中补回。

## 行为模型接口

- `booth_select_partial_product`
- `booth_partial_product_truth`
