# While Lane

## 角色

这一层负责 while / whilerw / whilewr 类谓词生成。它把标量比较、元素跨度和热码展开规则组合成可直接用于循环控制的谓词掩码。

## 输入

- `opn` / `opm`：标量比较源。
- `op`：while 变体。
- `esize`：元素粒度。
- `pred_width`：谓词宽度。

## 输出

- `mask`：生成的谓词位图。
- `lanes`：可覆盖的 lane 数。

## 处理流程

1. 根据 `esize` 确定元素跨度。
2. 对 `opn` 和 `opm` 做有符号或无符号比较。
3. 生成连续有效 lane。
4. 对 WR/RW 变体按差值形成热码段。

## 边界

- 差值为 0 时通常饱和成全真或全空，取决于变体。
- 结果始终截断到谓词宽度。

## 行为模型接口

- `while_mask`
- `while_compare_mask`
- `while_pass2_mask`
