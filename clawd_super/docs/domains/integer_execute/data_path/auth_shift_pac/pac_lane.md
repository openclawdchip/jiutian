# Pac Lane

## 角色

这一层负责 PAC 字段边界、mask 生成和 origin pointer 恢复。它把地址空间、TBI、底部 PAC 位置和 strip/addpac 路径统一到同一组规则里。

## 输入

- `ptr`：待处理地址。
- `bottom_pac_bit`：PAC 字段下边界。
- `tbi_res`：顶字节是否保留。
- `pstate_el` / `tcr` / `hcr_el2_e2h`：地址空间控制。

## 输出

- `pac_field_mask`
- `bottom_pac_bit`
- `origin_ptr`
- `origin_ptr_strip`

## 处理流程

1. 根据地址空间和控制位选择 PAC 字段区域。
2. 生成 PAC mask。
3. 从输入指针中恢复原始地址位。
4. 给 addpac/strip/auth 路径复用同一套边界规则。

## 边界

- TBI 有效时顶字节保留。
- strip 模式优先按固定观察位处理。

## 行为模型接口

- `pac_mask`
- `auth_pac_field_mask`
- `auth_bottom_pac_bit`
- `auth_setup_origin_pointer`
