# Bit Shift Pack

## 1. 角色

这个模块负责整数位移、循环位移和位域拼接，是朱雀的位操作主线。

## 2. 职责边界

它只处理位流重排，不承担算术核、乘法或标签逻辑。

## 3. 核心对象

- `shift_lane`
- `rotate_lane`
- `field_insert`
- `field_extract`

## 4. 结构框图

```mermaid
flowchart LR
    IN["shift / bitfield request"] --> CORE["bit shift pack"]
    CORE --> OUT["shifted / rotated / merged result"]
```

## 5. L3 对应

- `bit_shift_pack/shift_lane.md`
- `bit_shift_pack/rotate_lane.md`
- `bit_shift_pack/field_lane.md`

