# Pow2 Lane

## 角色

这一层识别除数是否为 2 的幂，并在命中时给出快速路径所需的移位量与残余掩码。它是除法器的捷径判断，不负责完整迭代。

## 输入

- `value`：候选除数。
- `width`：参与判断的数据宽度。
- `sgn_i`：符号相关的预处理开关。

## 输出

- `power_of_two_divisor`：是否命中快速路径。
- `power_of_two_shift`：对应的移位量。
- `power_of_two_remainder_mask`：余数掩码。

## 处理流程

1. 对输入做宽度截断。
2. 按符号模式生成辅助观察值。
3. 判断是否只剩一个 bit 为 1。
4. 若命中，输出该 bit 的位置作为移位量。

## 行为模型接口

- `is_power_of_two`
- `lshift64`
- `rshift64`
