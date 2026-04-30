# Chapter 7 Parameters and Discovery

本文档定义了一组 parameters，用于描述 encoder 的多个方面，例如 buses 的 widths、optional features 是否存在，以及 resources 的 size，如 Table 7.1 所列。

取决于 implementation，有些 parameters 可能本质上固定，另一些可能通过某种方式传入 design。

## Table 7.1 Parameters to the encoder

| Parameter name | Range | Description |
| --- | --- | --- |
| `arch_p` |  | encoder compliant 的 architecture specification version，initial version 为 0。 |
| `bpred_size_p` |  | branch predictor 中 entries 数为 `2^bpred_size_p`。minimum entries 为 2，因此 value 0 表示没有实现 branch predictor。 |
| `cache_size_p` |  | jump target cache 中 entries 数为 `2^cache_size_p`。minimum entries 为 2，因此 value 0 表示没有实现 jump target cache。 |
| `call_counter_size_p` |  | nested call counter 中 bits 数为 `2^call_counter_size_p`。minimum entries 为 2，因此 value 0 表示没有实现 implicit return call counter。 |
| `ctype_width_p` |  | `ctype` bus 的 width。 |
| `context_width_p` |  | `context` bus 的 width。 |
| `ecause_width_p` |  | exception cause bus 的 width。 |
| `ecause_choice_p` |  | 使用 multiple choice 匹配 exception cause 的 bits 数。 |
| `f0s_width_p` |  | format 0 `te_inst` packets 中 `subformat` field 的 width，见 5.8.1。 |
| `filter_context_p` | 0 or 1 | 为 1 时支持 filtering on context。 |
| `filter_excint_p` |  | 非零时支持 filtering on exception cause 或 interrupt。支持的 nested exceptions 数为 `2^filter_excint_p`。 |
| `filter_privilege_p` | 0 or 1 | 为 1 时支持 filtering on privilege。 |
| `filter_tval_p` | 0 or 1 | 为 1 且 `filter_excint_p` 非零时支持 filtering on trap value。 |
| `iaddress_lsb_p` |  | 要 trace 的 instruction address bus 的 LSB。支持 compressed instructions 时为 1，否则为 2。 |
| `iaddress_width_p` |  | instruction address bus 的 width。它与 DXLEN 相同。 |
| `iretire_width_p` |  | `iretire` bus 的 width。 |
| `ilastsize_width_p` |  | `ilastsize` bus 的 width。 |
| `itype_width_p` |  | `itype` bus 的 width。 |
| `nocontext_p` | 0 or 1 | 为 1 时从 `te_inst` packets 排除 context。 |
| `privilege_width_p` |  | privilege bus 的 width。 |
| `retires_p` |  | 每 block 可 retired 的 maximum instructions 数。 |
| `return_stack_size_p` |  | return address stack 中 entries 数为 `2^return_stack_size_p`。minimum entries 为 2，因此 value 0 表示没有实现 implicit return stack。 |
| `sijump_p` | 0 or 1 | `sijump` 用于标识 sequentially inferable jumps。 |
| `taken_branches_p` |  | `iretire`、`itype` 等被 replicated 的次数。 |
| `impdef_width_p` |  | implementation-defined input bus 的 width。 |

## 7.1 Discovery of encoder parameters

为了正确运行，decoder 必须能在 runtime 判定 encoder 的某些 parameters，形式为 discoverable attributes。这些 parameters 必须可由 decoder discover，或者固定为 default value。换言之，如果 encoder 没有让某个 parameter discoverable，它就必须只实现该 parameter 的 default value，而 decoder 也会使用该 default value。Table 7.2 列出了 required discoverable attributes。

为了访问 discoverable attributes，某个 external entity，例如 debugger 或 supervisory hart，必须向 encoder 请求它。encoder 将以一种或多种 format 提供 discovery information。首选 format 是经 trace infrastructure 发送的 packet。另一种 format 是允许 external entity 从 encoder 维护的某些 register 或 memory mapped space 读取 values。7.2 给出如何完成这一点的示例。

### Table 7.2 Required attributes

| Name | Default | Parameter mapping |
| --- | --- | --- |
| `arch` | 0 | `arch_p` |
| `bpred_size` | 0 | `bpred_size_p` |
| `cache_size` | 0 | `cache_size_p` |
| `call_counter_size` | 0 | `call_counter_size_p` |
| `context_width` | 0 | `context_width_p - 1` |
| `ecause_width` | 3 | `ecause_width_p - 1` |
| `f0s_width` | 0 | `f0s_width_p` |
| `iaddress_lsb` | 0 | `iaddress_lsb_p - 1` |
| `iaddress_width` | 31 | `iaddress_width_p - 1` |
| `nocontext` | 0 | `nocontext` |
| `privilege_width` | 2 | `privilege_width_p - 1` |
| `return_stack_size` | 0 | `return_stack_size_p` |
| `sijump` | 0 | `sijump_p` |

为便于使用，进一步建议把 encoder 的所有 parameters 都映射到 discoverable attributes，即使 decoder 不直接要求这些 parameters。尤其是与 filtering capabilities 相关的 attributes。Table 7.3 列出与 Chapter 4 中 filtering recommendations 关联的 attributes，Table 7.4 列出与本文档中其他 parameters 相关的 attributes。

### Table 7.3 Optional filtering attributes

| Name | Default | Parameter mapping |
| --- | --- | --- |
| `comparators` | 0 | `comparators_p - 1` |
| `filters` | 0 | `filters_p - 1` |
| `ecause_choice` | 5 | `ecause_choice_p` |
| `filter_context` | 1 | `filter_context_p` |
| `filter_excint` | 1 | `filter_excint_p` |
| `filter_privilege` | 1 | `filter_privilege_p` |
| `filter_tval` | 1 | `filter_tval_p` |

### Table 7.4 Other recommended attributes

| Name | Default | Description |
| --- | --- | --- |
| `ctype_width` | 1 | `ctype_width_p - 1` |
| `ilastsize_width` | 0 | `ilastsize_width_p - 1` |
| `itype_width` | 4 | `itype_width_p - 1` |
| `iretire_width` | 2 | `iretire_width_p - 1` |
| `retires` | 0 | `retires_p - 1` |
| `taken_branches` | 0 | `taken_branches_p - 1` |
| `impdef_width` | 0 | `impdef_width_p - 1` |

## 7.2 Example ipxact description

本节给出以 `ipxact` form 表示 discovery information 的示例。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ipxact:component
xmlns:ipxact="http://www.accellera.org/XMLSchema/IPXACT/1685-2014"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://www.accellera.org/XMLSchema/IPXACT/1685-2014
http://www.accellera.org/XMLSchema/IPXACT/1685-2014/index.xsd">
<ipxact:vendor>UltraSoC</ipxact:vendor>
<ipxact:library>TraceEncoder</ipxact:library>
<ipxact:name>TraceEncoder</ipxact:name>
<ipxact:version>0.8</ipxact:version>
<ipxact:memoryMaps>
<ipxact:memoryMap>
<ipxact:name>Trace Encoder Register Map</ipxact:name>
<ipxact:addressBlock>
<ipxact:name>>Trace Encoder Register Address Block</ipxact:name>
<ipxact:baseAddress>0</ipxact:baseAddress>
<ipxact:range>128</ipxact:range>
<ipxact:width>64</ipxact:width>
<ipxact:register>
<ipxact:name>discovery_info_0</ipxact:name>
<ipxact:addressOffset>'h0</ipxact:addressOffset>
<ipxact:size>64</ipxact:size>
<ipxact:access>read-only</ipxact:access>
<ipxact:field><ipxact:name>version</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>0</ipxact:bitOffset><ipxact:bitWidth>4</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>minor_revision</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>4</ipxact:bitOffset><ipxact:bitWidth>4</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>arch</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>8</ipxact:bitOffset><ipxact:bitWidth>4</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>bpred_size</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>12</ipxact:bitOffset><ipxact:bitWidth>4</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>cache_size</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>16</ipxact:bitOffset><ipxact:bitWidth>4</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>call_counter_size</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>20</ipxact:bitOffset><ipxact:bitWidth>3</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>comparators</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>23</ipxact:bitOffset><ipxact:bitWidth>3</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>context_type_width</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>26</ipxact:bitOffset><ipxact:bitWidth>5</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>context_width</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>31</ipxact:bitOffset><ipxact:bitWidth>5</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>ecause_choice</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>36</ipxact:bitOffset><ipxact:bitWidth>3</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>ecause_width</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>39</ipxact:bitOffset><ipxact:bitWidth>4</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>filters</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>43</ipxact:bitOffset><ipxact:bitWidth>4</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>filter_context</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>47</ipxact:bitOffset><ipxact:bitWidth>1</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>filter_excint</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>48</ipxact:bitOffset><ipxact:bitWidth>4</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>filter_privilege</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>52</ipxact:bitOffset><ipxact:bitWidth>1</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>filter_tval</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>53</ipxact:bitOffset><ipxact:bitWidth>1</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>filter_impdef</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>54</ipxact:bitOffset><ipxact:bitWidth>1</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>f0s_width</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>55</ipxact:bitOffset><ipxact:bitWidth>2</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>iaddress_lsb</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>57</ipxact:bitOffset><ipxact:bitWidth>2</ipxact:bitWidth></ipxact:field>
</ipxact:register>
<ipxact:register>
<ipxact:name>discovery_info_1</ipxact:name>
<ipxact:addressOffset>'h4</ipxact:addressOffset>
<ipxact:size>64</ipxact:size>
<ipxact:access>read-only</ipxact:access>
<ipxact:field><ipxact:name>iaddress_width</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>0</ipxact:bitOffset><ipxact:bitWidth>7</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>ilastsize_width</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>7</ipxact:bitOffset><ipxact:bitWidth>7</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>itype_width</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>14</ipxact:bitOffset><ipxact:bitWidth>7</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>iretire_width</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>21</ipxact:bitOffset><ipxact:bitWidth>7</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>nocontext</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>28</ipxact:bitOffset><ipxact:bitWidth>1</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>privilege_width</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>29</ipxact:bitOffset><ipxact:bitWidth>2</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>retires</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>31</ipxact:bitOffset><ipxact:bitWidth>3</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>return_stack_size</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>34</ipxact:bitOffset><ipxact:bitWidth>4</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>sijump</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>38</ipxact:bitOffset><ipxact:bitWidth>1</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>taken_branches</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>39</ipxact:bitOffset><ipxact:bitWidth>4</ipxact:bitWidth></ipxact:field>
<ipxact:field><ipxact:name>impdef_width</ipxact:name><ipxact:description>text</ipxact:description><ipxact:bitOffset>43</ipxact:bitOffset><ipxact:bitWidth>5</ipxact:bitWidth></ipxact:field>
</ipxact:register>
</ipxact:addressBlock>
<ipxact:addressUnitBits>8</ipxact:addressUnitBits>
</ipxact:memoryMap>
</ipxact:memoryMaps>
</ipxact:component>
```
