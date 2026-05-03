# 朱雀 Floorplan 导向设计

## 1. 目的

这份文档定义朱雀从物理实现角度反推微架构组织的原则。它不替代功能规格，而是约束功能规格最终必须长成什么样，才能支撑 `4.0 GHz`、`16` 路译码和放大的后端并发目标。

配套草图见 `zhuque-floorplan-sketch-v1.md`，用于固定 `core` 与 `tile` 两级的第一版平面分区。

## 2. 总原则

朱雀的物理规划先于局部逻辑整齐性。所有关键模块都遵守下面五条原则：

- 关键闭环最短化：`redirect -> next PC -> predictor -> fetch`、`wakeup -> select -> execute`、`writeback -> retire/reclaim` 这几条环必须优先缩短。
- 宽结构必须切片：`16` 路译码、`16` 路 rename、超宽结果选择、超宽缓存访问都不能做成单体块。
- 大容量结构必须分 bank：`L1I`、`L1D`、`PRF`、issue queue、ROB、`L2` 都按物理 bank 和本地端口组织。
- 慢控制和热数据分开：训练、替换、PMU、debug、异常统计、管理类服务不允许进入最高频热路径。
- 远距离全局线一律切拍：跨 core 中央区域、跨 tile、跨 fabric 的宽总线必须在结构上预留流水边界。

## 3. 数据通路先行规则

朱雀 floorplan 先摆数据通路，再摆控制通路。

第一轮 floorplan 只关注数据从入口到出口的物理路径：

```text
fetch -> decode -> rename -> issue -> execute -> writeback -> commit
```

以及并行的访存路径：

```text
issue -> AGU -> DTLB / L1D -> load return -> writeback
```

控制通路在第二轮覆盖到这些数据通路上。控制状态机、异常、replay、flush、debug 和功耗逻辑必须围绕已有数据路径布置，不能反过来把数据路径拉长。

每一段数据路径都必须同时记录：

- physical region
- slice / bank / cluster 边界
- standard-cell area
- SRAM / PRF macro area
- local logic delay
- wire delay
- latch / register boundary
- `4.0GHz` slack

## 4. Slice 条带规则

朱雀宽数据通路采用纵向 slice 条带。`64-bit` 数据路径以 `64` 个 bit slice 为默认物理单位，每个 slice 从上游寄存点纵向贯穿到下游寄存点。

slice 条带在 floorplan 中必须可见：

```text
bit63 | bit62 | ... | bit2 | bit1 | bit0
  |      |             |      |      |
  v      v             v      v      v
 PRF -> bypass -> ALU -> result -> writeback
```

每个 slice 的局部路径优先用短线闭合。跨 slice 的 carry、compare、zero-reduce、predicate-reduce 和 ECC 逻辑采用分层树，不允许形成横穿整个执行区的单周期大网。

## 5. Latch 相位规则

朱雀高频热路径预留 latch-based 时序结构。floorplan 需要标注相位边界，使局部长短路径可以通过时间借用平衡。

latch 相位只在局部条带或局部 cluster 内使用：

- ALU bit slice 内部
- bypass 到 execute 的局部段
- execute 到局部 result merge 的局部段
- L1D bank 内部 tag/data 前后段

跨 cluster、跨 cache bank、跨 core 和跨 tile 的路径不依赖隐式时间借用，必须使用显式 pipeline stage。

## 6. Core 物理分区

朱雀核心的推荐平面分区如下：

```text
north
  predictor / redirect / itlb / l1i banks

north-middle
  predecode / decode slices / uop buffer

center
  rename slices / issue slices / local scoreboards / integer PRF banks

west-center
  branch / compare / simple ALU / shift / integer result merge

east-center
  vector issue receive / VRF banks / vector integer / permute / vector MAC / vector FP

south-west
  AGU / DTLB / load-store queues / L1D banks / fill / replay

south-center
  ROB slices / retire select / redirect builder / reclaim path

south-east and edge
  L2 request egress / control-service entry / debug sideband
```

这个分区的核心思想是：

- 前端靠北，缩短 `redirect -> fetch` 闭环。
- decode/rename/issue 形成中部主干，减少超宽元数据横向跨越。
- integer 和 branch 靠近前端回跳脊柱。
- LSU 贴近 `L1D` 与 tile 级 `L2` 方向。
- vector 集群独立成区，避免 VRF 与标量 PRF 相互挤压。
- commit 位于中后段中央，兼顾前端 redirect、rename reclaim 和 LSU store commit。

## 7. 前端

### 7.1 物理结论

- `192B/cycle` 取指不能使用单条超宽单体总线，必须切成并行 fetch slice，推荐 `3 x 64B` 或 `4` 个并行子片。
- `L1I 256KB` 不能按单体单拍命中组织，必须是 banked 结构，并允许至少 `2` 级访问流水。
- 预测器必须做快慢分层。最短环里只放下一拍必须用到的方向、短目标和返回预测。
- `16` 路译码不能做成一个集中大译码器，推荐 `4 x 4` decode slice。

### 7.2 布局要求

- `redirect mux`、fast BTB、next-PC 选择器必须彼此紧邻。
- `ITLB` 贴着 `L1I tag` 一侧摆放，避免地址翻译跨整个前端。
- decode slice 直接挂在各自 fetch slice 后，不做大规模集中拼接后再译码。
- `uop buffer` 位于 decode 与 rename 之间，作为节拍隔离带。

### 7.3 对功能规格的反推

- 前端规格必须允许 banked `L1I`、分片 fetch、分片 decode。
- predictor training、replacement、统计信息单独走慢路径。
- `RVC` 边界识别应尽量靠近 fetch align / predecode，而不是进入统一大译码器后再处理。

## 8. Decode And Uop

### 8.1 物理结论

- `16 inst/cycle` decode 推荐分成 `4 x 4` slice，每个 slice 自带长度识别、RVC 展开和局部 immediate 形成。
- 非法指令、trap 元数据和复杂系统类后处理不能压在 decode 最短路径中。
- uop 打包要与 rename slice 的入口对齐，避免宽总线在 decode 与 rename 之间重新洗牌。

### 8.2 布局要求

- 每个 decode slice 只服务本地 fetch slice 输出。
- 全局共享的 opcode 分类表和稀有系统指令逻辑放在 slice 后段或旁路慢路径。
- trap/illegal 聚合器靠近 rename/commit 方向，而不是压在前端最北侧。

### 8.3 对功能规格的反推

- decode 规格应允许“局部译码、集中少量元数据合并”的两层结构。
- uop contract 要显式支持 slice 本地生成，再在下游拼成统一格式。

## 9. Rename

### 9.1 物理结论

- rename 不能是一个单体大块，推荐按输入宽度做多 slice 分摊。
- integer、FP、vector 三类 map/free-list/checkpoint 物理上要分开。
- rename 与对应 PRF bank 必须有明确邻接关系，否则 `16` 路分配和旁路标签广播线长失控。

### 9.2 布局要求

- integer rename 更靠近 integer issue 与 integer PRF。
- vector rename 更靠近 vector issue 与 VRF 边缘。
- checkpoint 存储靠近 branch/commit spine，缩短恢复通路。
- reclaim 返回口靠近 commit，避免释放 PRF 编号跨整个后端折返。

### 9.3 对功能规格的反推

- rename 规格应允许分域 free-list 和分域回收。
- checkpoint 不应假定集中单体表结构。
- 恢复流程必须能适配 slice 化 rename，而不是默认全局单拍回滚。

## 10. Issue

### 10.1 物理结论

- issue queue 必须按执行域就地分布，不能做一个全局超大队列。
- wakeup 和 select 不能在一个超宽组合云里完成，至少要拆成两段：本地 ready 形成和本地选择。
- 最常用的 bypass/forwarding 应尽量局部闭合，不依赖跨全核广播。

### 10.2 布局要求

- integer queue 紧贴 integer execute cluster。
- memory queue 紧贴 AGU / LSU 前端。
- vector queue 紧贴 vector cluster。
- branch queue 靠近 branch/compare 和 redirect spine。
- age/select 仲裁分区化，再在顶层汇总少量跨区冲突。

### 10.3 对功能规格的反推

- oldest-ready 规则应允许先局部选优，再全局裁决。
- queue 深度优先换成更多 bank，而不是单 bank 更深。
- replay/flush 不应要求整个 issue 域单点广播后同时组合收敛。

## 11. Integer Execute

### 11.1 物理结论

- simple ALU、compare、shift 这类低延迟单元必须放在最靠近 issue 和 redirect 的地方。
- 多周期 `div / special / auth / crc` 应布在整数簇边缘，不挤占热路径中心。
- 结果选择不能在单点统一收拢，优先局部合并后再写回。

### 11.2 布局要求

- branch / compare cluster 靠近前端 redirect spine。
- shift / bitfield 与 simple ALU 相邻，共享一部分低延迟结果路由。
- divider 放在外围，允许更长局部连线和更松的时钟边界。
- auth / crc 这类稀有路径与普通 ALU 分区，避免控制表和状态观察污染主线。

### 11.3 对功能规格的反推

- integer execute 规格要默认“低延迟簇 + 多周期外围簇”的组织。
- result merge 应允许按簇局部打包，而不是所有执行输入同时进一个中心 mux。

## 12. Vector Execute

### 12.1 物理结论

- vector 区必须围绕 `VRF` 做布局，而不是围绕控制逻辑做布局。
- permute 网络和 VRF 的距离决定频率上限，必须贴近 VRF 边缘。
- vector MAC cluster 更适合围绕部分积/归约树本地组织，不能把所有 lane 结果拉回统一中心再压缩。

### 12.2 布局要求

- VRF 采用 banked 条带组织，integer vector / permute / MAC / FP 围绕其分区。
- predicate/mask cluster 靠近 vector issue 入口与结果回写入口。
- 向量回写聚合分层完成：先簇内合并，再进入 VRF 写入口。

### 12.3 对功能规格的反推

- vector 规格必须允许多个写回聚合点。
- permute、mask、MAC、FP 应视作不同物理簇，而不是统一“vector ALU”。

## 13. LoadStore And MMU

### 13.1 物理结论

- LSU 必须贴着 `L1D` 和 `DTLB`，否则地址到 cache 的关键路径过长。
- store address、store data、load queue、replay queue 不能离 `L1D` 太远。
- fill buffer、miss queue、L2 egress 最好位于 core 边界，靠 tile 级 `L2` 方向。

### 13.2 布局要求

- AGU 靠近 issue 输出口。
- `DTLB` 和 `L1D tag/data` 形成一侧物理群。
- store queue 贴近 `L1D`，缩短 forwarding 和 commit 授权路径。
- replay/control/diagnostic 逻辑放在 LSU 外围，不压 tag/data hot pipe。

### 13.3 对功能规格的反推

- LSU 规格应允许地址生成、翻译、cache access 明确分级。
- forwarding 和 replay 必须是常规事务，不假定走单一慢异常网络。
- `L1D 256KB` 需要 banked、多端口抽象，而不是单体数组抽象。

## 14. Commit And Retire

### 14.1 物理结论

- `ROB 1024` 不能做成单体大环，必须分段或分 bank。
- redirect builder 必须靠近前端返回脊柱。
- reclaim 端口要靠近 rename，store commit 端口要靠近 LSU。

### 14.2 布局要求

- retire select、oldest exception merge、redirect 形成中央控制 spine。
- ROB 数据体与状态体可以分开放置，避免所有位宽一起走最短路径。
- PRF reclaim 输出朝 rename 方向。
- store commit 输出朝 LSU 方向。

### 14.3 对功能规格的反推

- commit 规格应允许 segmented ROB。
- exception merge 和 retire accounting 不能默认“单块单拍遍历全部窗口”。
- redirect 与 reclaim 是两条物理目标不同的路径，文档中应单独定义。

## 15. Level2 Cache

### 15.1 物理结论

- `16MB / tile, 64 banks` 的 `L2` 必须分布式 bank 化，不能视为中心单块缓存。
- bank pipe、MSHR、replacement、prefetch 需要明确分层，避免所有控制都压在 tag 命中路径上。
- `L2` 更适合围绕 tile 外围或核心群四周组织，而不是塞在单一中心岛。

### 15.2 布局要求

- 每个 core 最好面对一个本地方向更近的 bank group。
- data return 通路提前切拍，不能从远端 bank 无拍回到 core。
- MSHR 和 replacement 状态可相对集中，但必须脱开 hot tag/data pipe。

### 15.3 对功能规格的反推

- `L2` 规格要显式支持 bank group 和多拍响应。
- prefetch 与 demand request 要物理分离，不共享最短仲裁环。

## 16. Cluster Fabric

### 16.1 物理结论

- fabric 端点必须布在 tile 边缘，朝向跨 tile 链路。
- request/response 主链路与 service/debug 管理链路应物理分开。
- directory / slice / bridge 以“局部拥有权 + 就近出口”为中心布局。

### 16.2 布局要求

- L2 miss egress 与 fabric ingress 相邻。
- shared service 不进入主数据面中央。
- 长链路必须周期化，重复器和 pipeline stage 在架构上可见。

### 16.3 对功能规格的反推

- fabric 协议层必须天然支持分段切拍。
- bridge 规格只做协议转换与 buffering，不夹带大块功能逻辑。

## 17. Platform Control And Debug

### 17.1 物理结论

- debug、trace、service、低功耗控制不能压在主执行热区。
- 这类逻辑应该沿 core 或 tile 外围形成 service spine。

### 17.2 对功能规格的反推

- service 请求与主数据请求分开。
- trace/PMU 采样使用旁路观察口，不回灌热路径。

## 18. 直接影响规格的结论

从 floorplan 角度，朱雀后续所有文档都应默认以下组织，作为固定组织规则：

- 前端采用 `banked fetch + sliced decode`。
- `L1I` 与 `L1D` 都采用多 bank、多拍访问。
- rename、issue、PRF、ROB 全部采用 slice / bank 组织。
- integer、vector、LSU 三大执行域物理分区，结果局部合并。
- `L2` 和 fabric 默认采用分布式、切拍、边缘端点式结构。

## 19. 后续文档推进顺序

后续从 floorplan 角度继续细化模块时，优先顺序如下：

1. `frontend_ifetch`
2. `decode_and_uop`
3. `rename`
4. `issue`
5. `loadstore_and_mmu`
6. `integer_execute`
7. `vector_execute`
8. `commit_and_retire`
9. `level2_cache`
10. `cluster_fabric`
