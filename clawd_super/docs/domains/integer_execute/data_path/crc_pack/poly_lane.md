# Poly Lane

## 角色

这一层负责 CRC 多项式更新本体。它直接表达 reflected 和 raw 两种数据流下的位级反馈关系。

## 输入

- `crc`：当前 CRC 状态。
- `data`：待处理比特流。
- `bit_count`：参与更新的 bit 数。
- `poly`：反馈多项式。

## 输出

- `updated_crc`

## 处理流程

1. 逐 bit 读取输入数据。
2. 根据数据流方向选择反馈方式。
3. 每一步按当前 CRC 低位或高位决定是否异或多项式。
4. 返回更新后的 32-bit 状态。

## 边界

- reflected 和 raw 只是在比特流方向与反馈位上不同。
- 不包含初始 xor 或 final xor。

## 行为模型接口

- `_crc_reflected_update`
- `_crc_raw_update`
