# Commit And Retire

## 1. 角色

commit and retire 负责维持精确架构状态。它观察执行完成、决定哪几条指令可以按顺序退休，并统一处理 trap、interrupt、debug entry、store commit 和 retired physical resource 回收。

## 2. 核心结构

- ROB
- retire window
- exception candidate merge
- oldest exception select
- redirect builder
- store commit path
- rename reclaim path

## 3. 固定目标

| 项目 | 定义 |
|---|---|
| Commit 宽度 | `16 uop/cycle` |
| ROB | `1024` entries |
| Exception merge width | `16/cycle` |
| PRF reclaim width | `16/cycle` |
| Store commit width | `6/cycle` |

## 4. 输入输出

| 输入 | 说明 |
|---|---|
| dispatch metadata | 来自 rename |
| writeback events | 来自 execute/loadstore/vector |
| interrupt/debug request | 来自平台控制 |

| 输出 | 说明 |
|---|---|
| retired packet | 架构提交结果 |
| redirect | 对前端和中段的重定向 |
| reclaimed prf | 返给 rename |
| committed stores | 授权 loadstore 生效 |

## 5. 关键行为

- 严格按 ROB 顺序退休
- older normal 指令先于 younger fault 指令退休
- trap 导致 younger entry 清空
- interrupt 在指令边界进入
- store 只在退休时提交

## 6. Floorplan 视角

### 6.1 物理目标

commit and retire 需要同时服务三个方向：向前端返回 redirect，向 rename 返回 reclaim，向 LSU 发出 store commit。它的 floorplan 目标是把 `ROB` 做成分段结构，再用中央控制脊柱组织最老异常、退休授权和回收广播。

### 6.2 推荐分区

- `ROB` 状态体与数据体分开组织，按段或按 bank 沿核心南侧铺开。
- retire select、oldest exception merge、redirect builder 位于中央控制脊柱。
- reclaim 输出朝 rename 方向展开，store commit 输出朝 LSU 方向展开。
- interrupt/debug 注入口靠近 redirect builder 和异常汇合点，减少多处重复裁决。

### 6.3 时序约束

- `1024` 项 `ROB` 不允许单体大环式扫描。
- 最老异常选择、退休窗口选择和 redirect 形成需要分层完成，不假定单拍全表遍历。
- reclaim、store commit、redirect 三条输出链路的目标物理方向不同，必须在架构上拆开定义。

### 6.4 对后续模型的约束

- 行为模型需要显式体现分段 `ROB`、集中异常汇合、分方向输出和 younger 清除边界。
- RTL 应把 rob storage、retire select、exception merge、redirect build、reclaim merge、store commit authorize 分层实现。

## 7. 行为模型落点

行为模型应覆盖：

- in-order retire
- precise exception
- interrupt/debug redirect
- old prf reclaim
- store commit
- retire accounting

## 8. RTL 落点

RTL 先实现：

- rob entry
- retire select
- exception merge
- redirect control
- reclaim control
- commit top

## 9. 二级文档

- `commit_and_retire/data_path/README.md`
- `commit_and_retire/control_path/README.md`
- `commit_and_retire/README.md`
- `commit_and_retire/rob_retire_and_redirect.md`
- `commit_and_retire/trap_debug_and_resource_reclaim.md`

## 10. 模块文档

- `commit_and_retire/README.md`
- `commit_and_retire/INDEX.md`
- `commit_and_retire/data_path/README.md`
- `commit_and_retire/control_path/README.md`
- `commit_and_retire/top_mixed/README.md`
