# RISC-V Processor Trace

Version 1.0

4d009c4de4c68d547adb4adec307a438feb3d815

Gajinder Panesar, Iain Robertson  
`<gajinder.panesar@ultrasoc.com>`, `<iain.robertson@ultrasoc.com>`  
UltraSoC Technologies Ltd.  
2020 年 3 月 20 日

## 目录

1. Introduction
   1. Terminology
   2. Nomenclature
2. Branch Trace
   1. Instruction delta trace concepts
      1. Sequential instructions
      2. Uninferable PC discontinuities
      3. Branches
      4. Interrupts and exceptions
      5. Synchronization
      6. End of trace
   2. Optional and run-time configurable modes
      1. Delta address mode
      2. Full address mode
      3. Implicit exception mode
      4. Sequentially inferable jump mode
      5. Implicit return mode
      6. Branch prediction mode
      7. Jump target cache mode
3. Hart to encoder interface
   1. Interface requirements
      1. Jump classification and target inference
      2. Relationship between RISC-V core and the encoder
   2. Instruction interface
      1. Simplifications for single-retirement
      2. Alternative multiple-retirement interface configurations
      3. Optional sideband signals
      4. Using trigger outputs from the Debug Module
      5. Example retirement sequences
4. Filtering
5. Trace Encoder Output Packets
   1. Format 3 packets
   2. Format 3 subformat 0 - Synchronisation
      1. Format 3 branch field
   3. Format 3 subformat 1 - Exception
      1. Format 3 tvalepc field
   4. Format 3 subformat 2 - Context
   5. Format 3 subformat 3 - Support
      1. Format 3 subformat 3 qual_status field
   6. Format 2 packets
      1. Format 2 notify field
      2. Format 2 notify and updiscon fields
      3. Format 2 irreport and irdepth
   7. Format 1 packets
      1. Format 1 updiscon field
      2. Format 1 branch_map field
      3. Format 1 irstatus and irdepth fields
   8. Format 0 packets
      1. Format 0 subformat field
      2. Format 0 branch_fmt field
      3. Format 0 irstatus and irdepth fields
6. Reference Algorithm
   1. Format selection
   2. Resynchronisation
   3. Multiple retirement considerations
7. Parameters and Discovery
   1. Discovery of encoder parameters
   2. Example ipxact description
8. Future Directions
   1. Data trace
   2. Fast profiling
   3. Inter-instruction cycle counts
   4. Transport
9. Decoder
   1. Decoder pseudo code
10. Example code and packets

## 图清单

| 编号 | 标题 |
| --- | --- |
| 5.1 | Example encapsulated packet format |
| 6.1 | Instruction delta trace algorithm |

## 表清单

| 编号 | 标题 |
| --- | --- |
| 3.1 | Instruction interface signals |
| 3.2 | Instruction interface signals - multiple retirement per block |
| 3.3 | Instruction interface signals - single retirement per block |
| 3.4 | Context type ctype values and corresponding actions |
| 3.5 | Optional sideband encoder input signals |
| 3.6 | Optional sideband encoder output signals |
| 3.7 | Debug Module trigger support (`mcontrolaction`) |
| 3.8 | Example 1: 9 Instructions retired over four cycles, 2 branches |
| 5.1 | Packet format 3, subformat 0 |
| 5.2 | Packet format 3, subformat 1 |
| 5.3 | Packet format 3, subformat 2 |
| 5.4 | Packet format 3, subformat 3 |
| 5.5 | Packet format 2 |
| 5.6 | Packet format 1 - address, branch map |
| 5.7 | Packet format 1 - no address, branch map |
| 5.8 | Packet format 0, subformat 0 - no address, branch count |
| 5.9 | Packet format 0, subformat 0 - address, branch count |
| 5.10 | Packet format 0, subformat 1 - jump target index, branch map |
| 5.11 | Packet format 0, subformat 1 - jump target index, no branch map |
| 7.1 | Parameters to the encoder |
| 7.2 | Required attributes |
| 7.3 | Optional filtering attributes |
| 7.4 | Other recommended attributes |
