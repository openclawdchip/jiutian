# Wide Mul Acc

## 1. 角色

这个模块负责整数乘法和乘加主线，是朱雀的宽整数乘法归约核。

## 2. 职责边界

它只处理部分积、压缩和末级窗口，不承担除法或结果总线裁决。

## 3. 核心对象

- `booth_encode`
- `pp_select`
- `compress_tree`
- `final_window`

## 4. 结构框图

```mermaid
flowchart LR
    IN["mul / mac request"] --> CORE["wide mul acc"]
    CORE --> OUT["mul / mac result"]
```

## 5. L3 对应

- `wide_mul_acc/booth_stage.md`
- `wide_mul_acc/pp_stage.md`
- `wide_mul_acc/reduce_stage.md`
- `wide_mul_acc/window_stage.md`

