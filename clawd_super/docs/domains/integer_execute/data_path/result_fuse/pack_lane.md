# Pack Lane

## 角色

这一层负责把 4-bit payload 和 valid 位打包成统一 response。它是结果总线和谓词响应的公共封装层。

## 输入

- `valid`：结果有效位。
- `payload`：4-bit 状态或 flags。

## 输出

- `response`：5-bit 打包结果。
- `valid_requested`：调用侧请求的有效性。

## 处理流程

1. 截断 payload 到 4 位。
2. 将 valid 放入最高位。
3. 生成可直接传输的 response 编码。
4. 在缺源时保留诊断信息。

## 行为模型接口

- `pack_response`
- `select_and_pack_response`
- `pack_predicate_response`
