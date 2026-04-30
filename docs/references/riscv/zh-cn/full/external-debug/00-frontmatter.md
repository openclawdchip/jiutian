# RISC-V External Debug Support

版本 0.13

修订：`f7f3277d78d5b72dbba7d718d40892c469ca22ba`

作者：Tim Newsome `<tim@sifive.com>`

时间：Tue Nov 28 07:54:42 2017 -0800

## 前言

警告！这个草案规范在被接受为标准之前还会变化，因此按此草案规范实现的实现，很可能不会符合未来标准。

## 致谢

作者感谢以下人员付出的时间、反馈和想法：Bruce Ableidinger、Krste Asanovic、Mark Beal、Alex Bradbury、Zhong-Ho Chen、Monte Dalrymple、Vyacheslav Dyanchenco、Peter Egold、Richard Herveille、Po-wei Huang、Scott Johnson、Aram Nahidipour、Rishiyur Nikhil、Gajinder Panesar、Klaus Kruse Pedersen、Antony Pavlov、Ken Pettit、Wesley Terpstra、Megan Wachs、Stefan Wallentowitz、Ray Van De Walker、Andrew Waterman 和 Andy Wright。

## 目录

- 前言
- 1 Introduction
  - 1.1 Terminology
    - 1.1.1 Context
  - 1.2 About This Document
    - 1.2.1 Structure
    - 1.2.2 Register Definition Format
      - 1.2.2.1 Long Name (`shortname`, at `0x123`)
  - 1.3 Background
  - 1.4 Supported Features
- 2 System Overview
- 3 Debug Module (DM)
  - 3.1 Debug Module Interface (DMI)
  - 3.2 Reset Control
  - 3.3 Selecting Harts
    - 3.3.1 Selecting a Single Hart
    - 3.3.2 Selecting Multiple Harts
  - 3.4 Run Control
  - 3.5 Abstract Commands
    - 3.5.1 Abstract Command Listing
      - 3.5.1.1 Access Register
      - 3.5.1.2 Quick Access
  - 3.6 Program Buffer
  - 3.7 Overview of States
  - 3.8 System Bus Access
  - 3.9 Quick Access
  - 3.10 Security
  - 3.11 Debug Module DMI Registers
    - 3.11.1 Debug Module Status (`dmstatus`, at `0x11`)
    - 3.11.2 Debug Module Control (`dmcontrol`, at `0x10`)
    - 3.11.3 Hart Info (`hartinfo`, at `0x12`)
    - 3.11.4 Halt Summary (`haltsum`, at `0x13`)
    - 3.11.5 Hart Array Window Select (`hawindowsel`, at `0x14`)
    - 3.11.6 Hart Array Window (`hawindow`, at `0x15`)
    - 3.11.7 Abstract Control and Status (`abstractcs`, at `0x16`)
    - 3.11.8 Abstract Command (`command`, at `0x17`)
    - 3.11.9 Abstract Command Autoexec (`abstractauto`, at `0x18`)
    - 3.11.10 Device Tree Addr 0 (`devtreeaddr0`, at `0x19`)
    - 3.11.11 Abstract Data 0 (`data0`, at `0x04`)
    - 3.11.12 Program Buffer 0 (`progbuf0`, at `0x20`)
    - 3.11.13 Authentication Data (`authdata`, at `0x30`)
    - 3.11.14 System Bus Access Control and Status (`sbcs`, at `0x38`)
    - 3.11.15 System Bus Address 31:0 (`sbaddress0`, at `0x39`)
    - 3.11.16 System Bus Address 63:32 (`sbaddress1`, at `0x3a`)
    - 3.11.17 System Bus Address 95:64 (`sbaddress2`, at `0x3b`)
    - 3.11.18 System Bus Data 31:0 (`sbdata0`, at `0x3c`)
    - 3.11.19 System Bus Data 63:32 (`sbdata1`, at `0x3d`)
    - 3.11.20 System Bus Data 95:64 (`sbdata2`, at `0x3e`)
    - 3.11.21 System Bus Data 127:96 (`sbdata3`, at `0x3f`)
- 4 RISC-V Debug
  - 4.1 Debug Mode
  - 4.2 Load-Reserved/Store-Conditional Instructions
  - 4.3 Single Step
  - 4.4 Reset
    - 4.4.1 `dret` Instruction
  - 4.5 Core Debug Registers
  - 4.6 Virtual Debug Registers
- 5 Trigger Module
- 6 Debug Transport Module (DTM)
- A Hardware Implementations
- B Debugger Implementation
- C Future Ideas
- Index
- D Change Log

## 图目录

| 编号 | 译名 |
|---|---|
| 2.1 | RISC-V 调试系统概览 |
| 3.1 | Run/Halt 调试状态机 |

## 表目录

| 编号 | 译名 |
|---|---|
| 1.1 | 寄存器访问缩写 |
| 3.1 | Debug Module Interface 地址空间 |
| 3.2 | Data 寄存器的使用 |
| 3.3 | `cmdtype` 的含义 |
| 3.4 | Abstract Register Numbers |
| 3.5 | Debug Module Debug Bus Registers |
| 4.1 | Core Debug Registers |
| 4.2 | 进入 Debug Mode 时 DPC 中的虚拟地址 |
| 4.3 | Virtual Core Debug Registers |
| 4.4 | Privilege Level 编码 |
| 5.1 | Trigger Registers |
| 5.2 | 建议的 Breakpoint Timing |
| 6.1 | JTAG DTM TAP Registers |
| 6.2 | JTAG Connector Diagram |
| 6.3 | JTAG Connector Pinout |
| B.1 | Memory Read Timeline |
| C.1 | Debug Module Debug Bus Registers |
