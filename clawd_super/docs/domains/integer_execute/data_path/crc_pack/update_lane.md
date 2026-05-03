# Update Lane

## 角色

这一层负责 CRC 更新主路径。它把 accumulator、data、size 和多项式选择合并成一条可执行的 CRC 结果通路。

## 输入

- `accumulator`：当前 CRC 状态。
- `data`：待更新数据。
- `size`：参与更新的字节数。
- `polynomial`：CRC32 或 CRC32C。

## 输出

- `result`：更新后的 CRC。
- `aligned`：对齐后的中间量。

## 处理流程

1. 按 size 解码有效字节数。
2. 对输入数据和 accumulator 做对齐。
3. 选择 reflected 或 raw 更新方向。
4. 输出最终 CRC 状态。

## 边界

- size 只能取 1/2/4/8 字节。
- accumulator 前递仅影响来源，不改变更新数学。

## 行为模型接口

- `crc32_update`
- `crc32c_update`
- `iexecute_crc`
