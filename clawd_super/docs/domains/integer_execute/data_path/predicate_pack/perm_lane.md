# Perm Lane

## 角色

这一层负责 predicate 的重排、交织和反交织。它服务 zip、uzp、trn、rev 和 unpack 类路径。

## 输入

- `ps1` / `ps2`：谓词源。
- `op`：重排操作。
- `esize`：元素跨度。
- `hl`：低半或高半选择。

## 输出

- `result`：重排后的谓词。

## 处理流程

1. 将谓词切成固定步长的元素。
2. 按操作类型选择交错、拆分或反转规则。
3. 根据高低半变体选择输出窗口。
4. 重新打包成谓词位图。

## 行为模型接口

- `palu_interleave`
- `palu_perm_exact`
