# Shuffle Lane

## 角色

这一层负责认证链路的 nibble 置换。它提供正向和逆向两套 shuffle，供 PAC 轮函数和 tweak 更新共同使用。

## 输入

- `value`：64 位数据。

## 输出

- `shuffled`
- `inverse_shuffled`

## 处理流程

1. 把 64 位值分解成 16 个 nibble。
2. 按固定映射重新排列 nibble 顺序。
3. 对需要反馈的 nibble 再做局部 bit 变换。
4. 输出正向和逆向结果。

## 行为模型接口

- `cell_shuffle`
- `cell_invshuffle`
- `tweak_shuffle`
- `tweak_invshuffle`
