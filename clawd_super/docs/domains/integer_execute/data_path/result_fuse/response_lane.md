# Response Lane

## 角色

这一层负责 response / status / vmove 数据封装。它把不同子路径的低位信息统一打包成可传输格式。

## 输入

- `sel`：响应源选择。
- `responses`：响应字典。
- `srca` / `srcb`：vmove 数据源。
- `selectors`：word 选择器。

## 输出

- `data`
- `valid`
- `source`
- `fcvt_selected`

## 处理流程

1. 按来源选择 response payload。
2. 将 valid bit 与 payload 打包。
3. 处理 vmove 的 word 级组合。
4. 输出统一的 response/搬移格式。

## 行为模型接口

- `pass2_response_select`
- `pass2_predicate_data_select`
- `pass2_vmove_data`
- `pass2_vmove_sve_data`
- `pass2_palu1_response`
