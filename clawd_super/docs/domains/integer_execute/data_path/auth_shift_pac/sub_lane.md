# Sub Lane

## 角色

这一层负责认证数据通路中的非线性代换与逆代换。它按 nibble 粒度工作，是认证链路里最基础的变换层。

## 输入

- `value`：64 位待变换数据。

## 输出

- `substituted`：代换后的数据。
- `inverse_substituted`：逆代换后的数据。

## 处理流程

1. 将输入切成 16 个 nibble。
2. 每个 nibble 独立经过固定 S-box。
3. 按同样的 nibble 边界重组结果。
4. 输出供后续置换或混合层继续处理。

## 边界

- 每个 nibble 独立处理，不跨 nibble 借位。
- 结果始终截断到 64 位。

## 行为模型接口

- `auth_substitute`
- `auth_inverse_substitute`
