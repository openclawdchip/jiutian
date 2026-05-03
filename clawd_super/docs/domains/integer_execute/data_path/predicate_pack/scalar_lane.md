# Scalar Lane

## 角色

这一层负责 PALU 的标量操作和顶层分发。它把 predicate 统计、计数、增减和终止标志统一到一组标量行为里。

## 输入

- `op`：标量或 test 类操作。
- `opn` / `opm`：标量源。
- `pg`：谓词源。
- `imm`：立即数。

## 输出

- `result`
- `nzcv`
- `response`
- `pmu`

## 处理流程

1. 按操作分类选择标量、test 或 perm/break/while 路径。
2. 生成 active count 或 predicate 统计。
3. 应用饱和、符号和乘常数规则。
4. 打包 response 与 PMU 事件。

## 行为模型接口

- `palu_scalar`
- `palu_test`
- `palu_top_execute`
