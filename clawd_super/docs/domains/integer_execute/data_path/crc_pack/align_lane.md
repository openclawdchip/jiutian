# Align Lane

## 角色

这一层负责 CRC 输入对齐。它把 size 编码转换成字节数，并把 accumulator 与 data 摆放到便于后续多项式更新的观察窗口里。

## 输入

- `size`：CRC 数据大小。
- `accumulator`：当前 CRC 状态。
- `data`：待更新数据。

## 输出

- `byte_size`
- `aligned_acc`
- `alu_data`
- `crc_input`

## 处理流程

1. 把 size 解码成 1/2/4/8 字节。
2. 按字节数截断数据。
3. 对 accumulator 做位移对齐。
4. 生成 88-bit 观察窗口。

## 行为模型接口

- `crc_data_size_decode`
- `crc_align_inputs`
