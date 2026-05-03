# Trace Lane

## 角色

这一层把除法的整条恢复路径串起来，给出从输入到商、余数、异常和快速路径的完整行为轨迹。它是后续行为模型的主入口之一。

## 输入

- `srca` / `srcb`：被除数和除数。
- `signed_div`：有符号除法模式。
- `valid` / `cancel` / `flush`：控制握手。

## 输出

- `quotient`
- `remainder`
- `fast_path`
- `steps`
- `behavior_state`

## 处理流程

1. 先判断控制状态是否允许本次计算。
2. 再处理除零和有符号溢出。
3. 若进入恢复路径，则逐 bit 记录部分余数和商位。
4. 最后输出完整结果与每步轨迹。

## 边界

- `flush` 优先于 `cancel`。
- 除零直接返回特例。
- 有符号最小值除以 `-1` 走独立特例。

## 行为模型接口

- `div_behavior_state`
- `divide_iteration_trace`
- `divide`
