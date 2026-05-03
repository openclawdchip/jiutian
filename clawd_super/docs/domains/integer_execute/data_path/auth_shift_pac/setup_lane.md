# Setup Lane

## 角色

这一层负责认证链路的控制判定。它选择当前 EL、TBI/TBID、key 使能和 PAC 起点，并把这些控制汇总到 setup 信息里。

## 输入

- `pstate_el`
- `s1_trans_reg_el1`
- `enables`
- `tcr`
- `hcr_el2_e2h`

## 输出

- `enabled`
- `tbi`
- `selbitpos`
- `bottom_pac_bit`
- `key_name`

## 处理流程

1. 解码当前 privilege 状态。
2. 选择 data/instr 和 A/B key 路径。
3. 判定 TBI/TBID 以及 PAC 字段边界。
4. 生成 setup 观测字段。

## 行为模型接口

- `auth_enable`
- `auth_tbi`
- `auth_setup_info`
- `auth_enable_info`
- `auth_tbi_info`
