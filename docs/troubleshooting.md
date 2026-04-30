# 故障排查

## Python 无法运行

确认 Python 已安装并可在当前 shell 中访问：

```powershell
python --version
```

## JSON 解析失败

检查输入文件是否为合法 JSON，字段名是否使用双引号。

## capability violation

常见原因：

- 任务未声明对应 memory region。
- 访问地址越过 region 边界。
- 对只读区域执行写入。
- 对只写区域执行读取。

## SPM 或 Cluster SRAM 越界

检查 `config` 中的容量，以及 load/store/dma_copy 的地址和字节数。

## barrier deadlock

检查 barrier 的 `participants` 是否与实际到达任务数量一致。

## 输出不符合预期

使用 `--trace` 查看每条指令、DMA 和 barrier 事件，确认数据是否按预期流动。
