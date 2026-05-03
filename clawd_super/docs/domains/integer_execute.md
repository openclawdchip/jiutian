# Integer Execute

## 1. 角色

integer execute 负责处理标量整数主线，包括 ALU、shift、compare、mul/div、位操作和系统辅助整数运算。

## 2. 子域

- ALU
- shift / bitfield
- compare / branch operand helper
- multiply / MAC-style integer helper
- divide / remainder
- special integer helper

## 3. 固定目标

| 单元 | 数量 |
|---|---:|
| Simple ALU | 8 |
| Branch / compare | 6 |
| Integer MUL | 6 |
| Integer DIV / remainder / special | 4 |
| Bitmanip / assist path | 6 |

## 4. 输入输出

| 输入 | 说明 |
|---|---|
| issue packet | 来自 issue 的已发射 uop |
| operand data | 已准备好的源操作数 |

| 输出 | 说明 |
|---|---|
| writeback result | 回写到 PRF |
| flags / compare result | 给分支和系统控制 |
| exception sideband | 特定情况下的错误或系统事件 |

## 5. 关键约束

- 简单整数路径优先保持低延迟
- mul/div 允许多周期
- 特殊整数路径不应污染主 ALU 接口

## 6. Floorplan 视角

### 6.1 物理目标

integer execute 的第一优先级是守住低延迟分支回跳与整数旁路闭环。朱雀把快整数、分支比较和慢数学路径明确分区，让最热的 `issue -> execute -> writeback / redirect` 环停留在最短局部区域。

### 6.2 推荐分区

- simple ALU、compare、condition flags 和 branch assist 位于同一低延迟整数簇。
- shift、rotate、bitfield 和常见 bitmanip 紧贴 simple ALU，复用一部分操作数选路和结果写回通道。
- `mul`、`div`、`crc`、`auth` 等多周期与稀有路径布在整数簇外缘，避免侵入中央短路径。
- 结果回写优先在簇内局部合并，再进入统一写回层。

### 6.3 时序约束

- 分支比较结果到 redirect builder 的返回路径必须短于普通多周期结果回写路径。
- 低延迟整数簇默认允许更强本地 bypass，慢路径默认多一级或多级边界后再并入主写回。
- 特殊整数路径的状态寄存和控制表不能穿插在 simple ALU 的关键组合深度里。

### 6.4 对后续模型的约束

- 行为模型需要显式区分低延迟簇、本地 bypass、多周期簇和局部结果合并。
- RTL 需要把 fast ALU、shift/bitfield、branch assist、mul、div、special merge 作为独立结构展开。

## 7. 行为模型落点

行为模型应覆盖：

- add/sub/logic/shift
- compare 与分支辅助
- mul/div 的数学语义
- 非法配置和边界输入

## 8. RTL 落点

RTL 先实现：

- alu
- shift
- multiplier helper
- divider helper
- integer execute top

## 9. 模块文档

- `integer_execute/README.md`
- `integer_execute/INDEX.md`
- `integer_execute/data_path/README.md`
- `integer_execute/data_path/operand_bypass_and_lane_select.md`
- `integer_execute/data_path/fast_alu_and_flags.md`
- `integer_execute/data_path/shift_rotate_and_bitfield.md`
- `integer_execute/data_path/compare_and_branch_assist.md`
- `integer_execute/data_path/multiply_mac_and_reduce.md`
- `integer_execute/data_path/divide_remainder_and_iterative_math.md`
- `integer_execute/data_path/crc_pointer_auth_and_special_transform.md`
- `integer_execute/data_path/result_merge_and_writeback.md`
