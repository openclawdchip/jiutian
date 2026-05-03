# Logic Lane

## 角色

这一层负责谓词逻辑组合。它把 governing predicate 与两个源谓词组合成最终的逻辑结果。

## 输入

- `pg`：governing predicate。
- `ps1` / `ps2`：源谓词。
- `op`：逻辑操作类型。

## 输出

- `result`：逻辑后的谓词。

## 处理流程

1. 将输入截断到谓词位宽。
2. 按操作类型执行与、或、异或、选择或取反。
3. 用 governing predicate 限定有效 lane。
4. 输出可直接进入 break/while/test 的结果。

## 行为模型接口

- `packed_logical`
- `predicate_logical`
