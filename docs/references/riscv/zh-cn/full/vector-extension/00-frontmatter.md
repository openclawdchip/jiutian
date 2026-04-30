# RISC-V "V" Vector Extension

Version 1.0

## 目录

- Changes from v1.0-rc2
- 1. Introduction
- 2. Implementation-defined Constant Parameters
- 3. Vector Extension Programmer's Model
  - 3.1. Vector Registers
  - 3.2. Vector Context Status in `mstatus`
  - 3.3. Vector Context Status in `vsstatus`
  - 3.4. Vector type register, `vtype`
  - 3.5. Vector Length Register `vl`
  - 3.6. Vector Byte Length `vlenb`
  - 3.7. Vector Start Index CSR `vstart`
  - 3.8. Vector Fixed-Point Rounding Mode Register `vxrm`
  - 3.9. Vector Fixed-Point Saturation Flag `vxsat`
  - 3.10. Vector Control and Status Register `vcsr`
  - 3.11. State of Vector Extension at Reset
- 4. Mapping of Vector Elements to Vector Register State
  - 4.1. Mapping for `LMUL = 1`
  - 4.2. Mapping for `LMUL < 1`
  - 4.3. Mapping for `LMUL > 1`
  - 4.4. Mapping across Mixed-Width Operations
  - 4.5. Mask Register Layout
- 5. Vector Instruction Formats
  - 5.1. Scalar Operands
  - 5.2. Vector Operands
  - 5.3. Vector Masking
  - 5.4. Prestart, Active, Inactive, Body, and Tail Element Definitions
- 6. Configuration-Setting Instructions (`vsetvli`/`vsetivli`/`vsetvl`)
  - 6.1. `vtype` encoding
  - 6.2. `AVL` encoding
  - 6.3. Constraints on Setting `vl`
  - 6.4. Example of stripmining and changes to `SEW`
- 7. Vector Loads and Stores
- 8. Vector Memory Alignment Constraints
- 9. Vector Memory Consistency Model
- 10. Vector Arithmetic Instruction Formats
- 11. Vector Integer Arithmetic Instructions
- 12. Vector Fixed-Point Arithmetic Instructions
- 13. Vector Floating-Point Instructions
- 14. Vector Reduction Operations
- 15. Vector Mask Instructions
- 16. Vector Permutation Instructions
- 17. Exception Handling
- 18. Standard Vector Extensions
- 19. Vector Instruction Listing
- Appendix A: Vector Assembly Code Examples
- Appendix B: Calling Convention (Not authoritative - Placeholder Only)
- Appendix C: Fractional `Lmul` example

## 贡献者

贡献者包括：Alon Amid、Krste Asanovic、Allen Baum、Alex Bradbury、Tony Brewer、Chris Celio、Aliaksei Chapyzhenka、Silviu Chiricescu、Ken Dockser、Bob Dreyer、Roger Espasa、Sean Halle、John Hauser、David Horner、Bruce Hoult、Bill Huffman、Nicholas Knight、Constantine Korikov、Ben Korpan、Hanna Kruppe、Yunsup Lee、Guy Lemieux、Grigorios Magklis、Filip Moc、Rich Newell、Albert Ou、David Patterson、Colin Schmidt、Alex Solomatnikov、Steve Wallach、Andrew Waterman、Jim Wilson。

## Changes from v1.0-rc2

澄清：这是用于公开评审的冻结版本。
