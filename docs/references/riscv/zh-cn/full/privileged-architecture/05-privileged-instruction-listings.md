# 第 5 章 RISC-V Privileged Instruction Set Listings

源范围：PDF 第 87-88 页；Chapter 5 RISC-V Privileged Instruction Set Listings。

> 说明：本文件为严格全文机器初译后术语保护稿；CSR 名、寄存器名、指令名、异常名、字段名按原文保留。

<!-- Source PDF page 87 -->


## 第5章
RISC-V 特权指令集
房源
本章介绍 RISC-V 特权指令中定义的所有指令的指令集列表
建筑学。
本手册第一卷提供了非特权指令的指令集列表，包括 ECALL 和 EBREAK 指令。
75

<!-- Source PDF page 88 -->
31 27 26 25 24 20 19 15 14 12 11 7 6 0
funct7 rs2 rs1 funct3 rd 操作码 R 型
imm[11:0] rs1 funct3 rd 操作码 I 型
陷阱返回指令
0000000 00010 00000 000 00000 1110011 URET
0001000 00010 00000 000 00000 1110011 SRET
0011000 00010 00000 000 00000 1110011 MRET
中断管理指令
0001000 00101 00000 000 00000 1110011 WFI
主管内存管理指令
0001001 rs2 rs1 000 00000 1110011 SFENCE.VMA
虚拟机监控程序内存管理指令
0010001 rs2 rs1 000 00000 1110011 HFENCE.BVMA
1010001 rs2 rs1 000 00000 1110011 HFENCE.GVMA
表 5.1：RISC-V 特权指令
