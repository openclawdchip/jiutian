# 朱雀底层部件层

## 1. 定位

`foundation` 是朱雀的底层部件层。

它位于标准单元、SRAM/PRF 宏单元、互连金属层之上，位于各设计域之下。上层 `ifetch`、`decode`、`rename`、`issue`、`execute`、`loadstore`、`commit`、`level2` 和 `cluster` 都通过这一层搭建。

朱雀不直接从功能域里散写底层结构。所有反复出现的寄存、队列、bank、仲裁、匹配、旁路、计数、跨域、协议和 SRAM 封装都先沉到 `foundation`。

## 2. 输入约束

底层部件层由三类输入共同约束：

- 整数、前端、访存、提交、互连等主干数据通路需求分布
- `C:\chipwiki\wiki\synthesis\n07-logic-and-interconnect-ppa-envelope-v1.md` 的标准单元和互连 PPA 锚点
- `C:\chipwiki\wiki\synthesis\n07-sram-ppa-envelope-v1.md` 的 SRAM / PRF 宏单元 PPA 锚点

底层需求用来判断需要哪些部件族。`N07` PPA 账本用来判断这些部件族应该如何切片、bank、切拍和约束。

## 3. 底层需求归纳

主干功能需求按出现强度归纳为：

| 需求族 | 朱雀底层部件方向 |
|---|---|
| state / register / reset | 寄存器、pipeline register、reset cell、状态表 |
| clock / reset / sync / bridge | 时钟复位、CDC、跨域桥、同步器 |
| decode / opcode / instruction | 译码表、字段抽取、uop 打包、立即数形成 |
| ALU / shift / mul / div / compare | 整数算术 primitive 和多周期算术单元 |
| cache / TLB / way / set / miss | cache bank、tag array、TLB bank、miss tracker |
| fabric / req / resp / packet | 片上协议适配、包化、信用和流控 |
| load / store / AGU / forward | 地址生成、load/store 队列、转发和 hazard 检查 |
| SRAM / RAM / array / bank | N07 SRAM/PRF 宏封装、bank wrapper、读写调度 |
| vector / lane / mask / MAC | vector lane、mask、permute、MAC primitive |
| FIFO / queue / head / tail | 队列、环形指针、valid bitmap、entry storage |
| CAM / match / tag / lookup | tag match、CAM-like lookup、age match、hazard match |
| issue / wakeup / scoreboard | ready 形成、wakeup、select、scoreboard |
| commit / retire / flush / replay | 提交、回收、flush、replay、recover primitive |
| trace / debug / counter | 事件计数、trace packet、debug sideband |

这些需求决定朱雀先搭底层部件，再搭功能域。

## 4. 物理约束

底层部件层统一采用以下 `N07` 硬约束：

| 约束项 | 当前锚点 |
|---|---:|
| `INV D1` 面积 | `0.04104 um^2` |
| `NAND2 D1` 面积 | `0.05472 um^2` |
| `DFF D1` 面积 | `0.2736 um^2` |
| `INV D1 FO4` | `7.252 ps` |
| `DFF CP->Q` | `25.870 ps` |
| `4GHz` 周期 | `250 ps` |
| `L1CACHE 36Kbit` cycle | `0.245 ns` |
| `HSSPSRAM 36Kbit` cycle | `0.238 ns` |
| `1PRF 16Kbit` cycle | `0.249 ns` |
| `UHDSPSRAM 156Kbit` cycle | `0.562 ns` |

设计含义：

- 低层局部线和控制 mux 不能事后处理，必须进时序预算。
- `4GHz` 单周期数组只允许使用小叶子、多 bank、本地连线。
- `L2` / `L3` 级密集 SRAM 默认多周期。
- PRF 不做集中超宽单体，必须分簇、分 bank、分阶段。
- 全局广播默认不可接受，改为局部广播、分层汇聚和切拍。

## 5. 部件分层

朱雀 foundation 分四层：

| 层级 | 作用 |
|---|---|
| physical primitive | 标准单元、DFF、门级组合、复位、同步、低层金属约束 |
| storage primitive | SRAM/PRF wrapper、bank、tag array、payload array、valid bitmap |
| flow primitive | ready/valid、credit、FIFO、queue、arbiter、selector、skid、replay token |
| compute primitive | adder、shifter、compare、multiply、divide step、CRC、mask、permute |

上层功能域不能越过这些 primitive 自己定义重复底层结构。

## 6. 当前文档

- `demand_map.md`
  - 朱雀底层需求地图
- `n07_primitive_binding.md`
  - N07 标准单元、SRAM/PRF 宏单元和互连层到朱雀 primitive 的绑定
- `primitive_catalog.md`
  - 朱雀底层 primitive 清单
- `build_up_sequence.md`
  - 从 foundation 往上搭建各设计域的顺序
- `iexecute_primitives/`
  - 朱雀整数执行数据通路基础构件，绑定 N07 标准单元、线网、slice 和 latch 规则

## 7. 对上层的约束

每个 L2/L3 模块文档都要引用 foundation primitive。

模块文档必须说明：

- 使用哪些 storage primitive
- 使用哪些 flow primitive
- 使用哪些 compute primitive
- 是否存在跨区线
- 是否需要切拍
- 是否需要多周期访问
- 是否依赖 N07 SRAM/PRF 宏
- 是否存在超过 `20` 到 `25` FO4 的组合风险
