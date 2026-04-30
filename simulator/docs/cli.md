# 模拟器 CLI

## 命令格式

```powershell
python simulator\jiutian_sim.py <input.json> [--trace]
```

## 参数

- `<input.json>`：APU-IR JSON 文件。
- `--trace`：输出完整 trace。

## 输入

输入文件应包含：

- `version`
- `name`
- `config`
- `memory`
- `barriers`
- `tasks`

可选包含：

- `host_init`
- `dump_words`

## 输出

默认输出最终 host memory 摘要。开启 `--trace` 后，同时输出调度、指令、内存、DMA、barrier 和异常事件。

## 退出码

- `0`：运行完成。
- 非 `0`：输入解析失败或模拟器内部错误。
