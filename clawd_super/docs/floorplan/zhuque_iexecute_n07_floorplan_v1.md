# Zhuque IExecute N07 Floorplan v1

本文记录朱雀整数执行数据通路第一版物理草图的生成依据。

## 输出

- `docs/assets/floorplan/zhuque_iexecute_n07_floorplan_v1.svg`
- `docs/assets/floorplan/zhuque_iexecute_n07_floorplan_v1.png`
- `docs/assets/floorplan/zhuque_iexecute_n07_floorplan_v2.png`
- `docs/assets/floorplan/zhuque_iexecute_n07_floorplan_v1.json`

## 几何锚点

- 标准单元 site：`0.057 x 0.240 um`
- `INV D1`：`0.04104 um2`
- `NAND2 D1`：`0.05472 um2`
- `XOR2 D1`：`0.15048 um2`
- `MUX2 D1`：`0.15048 um2`
- `FA1 D1`：`0.27360 um2`
- `LHQ D1`：`0.19152 um2`
- `DFQ D1`：`0.27360 um2`
- 1PRF 16K leaf 面积：`1417.590 um2`，cycle：`0.249 ns`

## 时延锚点

- `INV D1 FO4`：`7.252 ps`
- `DFF CP->Q`：`25.870 ps`
- `M5 local`：`15.500 ps`
- `M10 local spine`：`4.421 ps`
- `M12 core spine`：`0.855 ps`

## 分区尺寸

| 分区 | 尺寸 um | 放置面积 um2 | 估算路径 ps | 4GHz slack ps |
|---|---:|---:|---:|---:|
| `operand` | `496.944 x 9.773` | `4856.674` | `128.378` | `121.622` |
| `fast` | `233.472 x 3.174` | `741.018` | `122.630` | `127.370` |
| `compare` | `175.104 x 2.109` | `369.257` | `144.634` | `105.366` |
| `shift` | `175.104 x 6.005` | `1051.445` | `153.386` | `96.614` |
| `mul` | `175.104 x 56.444` | `9883.581` | `191.894` | `58.106` |
| `div` | `116.736 x 16.556` | `1932.656` | `168.138` | `81.862` |
| `special` | `116.736 x 37.057` | `4325.944` | `177.390` | `72.610` |
| `result` | `496.944 x 4.782` | `2376.599` | `174.390` | `75.610` |

## 说明

图中标准单元逻辑区采用显式 cell-count 模型和 N07 LEF 单元面积计算，再加入放置利用率与局部布线通道系数。PRF 北侧边界采用 QRT 面积锚点，并按 `64` 个纵向 bit slice 对齐。每条数据 lane 均显示 bit 0、bit 31/32 分界和 bit 63，便于后续保持 slice-based 实现。该图用于 floorplan 驱动的前端数据通路设计，不替代综合、布局布线和 STA 报告。
