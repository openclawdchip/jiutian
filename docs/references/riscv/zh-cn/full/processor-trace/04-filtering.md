# Chapter 4 Filtering

本章内容仅为 informative。

Filtering 提供一种机制，用于控制 encoder 是否应产生 trace。例如，可能希望在以下情况下 trace：

- instruction address 位于特定 range 内；
- 从一个 instruction address 开始，并持续到第二个 instruction address；
- 针对一个或多个指定 privilege levels；
- 针对特定 context 或 context range；
- 针对指定 exception causes 或具有特定 `tval` values 的 exception 和/或 interrupt handlers；
- 基于施加到 `impdef` 或 `trigger` signals 的 values；
- 持续一段固定时间；
- 等等。

具体如何完成是 implementation specific。

一种建议实现提供：

- 对 `iaddress`、`context` 和 `tval` inputs 提供一组 arithmetic options（`<`、`>`、`=`、`!=` 等）的 comparators；
- 对 `priv` 和 `cause` inputs 提供 multiple choice selection；
- 对 `interrupt` 和 `impdef` inputs 提供 masked matching；
- 当 `trigger[0]` asserted 时 enable tracing，并持续 tracing 直到 `trigger[0]` asserted，见 3.2.4。
