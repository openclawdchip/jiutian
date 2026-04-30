# Appendix A: Software optimization guide

## A.1. strlen

`orc.b` 指令允许在一个 `XLEN` 大小的数据块中高效检测 NUL 字节：

- 对不包含任何 NUL 字节的数据块执行 `orc.b`，其结果将为全一。
- 对 `orc.b` 的结果按位取反之后，可通过 `ctz`/`clz`（取决于数据的字节序）检测第一个 NUL 字节之前的数据字节数（如果存在）。

下面给出一个完整的 `strlen` 函数示例。它使用这些技术，同时也演示了如何将这些技术用于非对齐/部分数据：

```asm
#include <sys/asm.h>
  .text
  .globl strlen
  .type  strlen, @function
strlen:
  andi    a3, a0, (SZREG-1)   // offset
  andi    a1, a0, -SZREG      // align pointer
.Lprologue:
  li      a4, SZREG
  sub     a4, a4, a3          // XLEN - offset
  slli    a3, a3, PTRLOG      // offset * 8
  REG_L   a2, 0(a1)           // chunk
  /*
   * Shift the partial/unaligned chunk we loaded to remove the bytes
   * from before the start of the string, adding NUL bytes at the end.
   */
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
  srl a2, a2 ,a3          // chunk >> (offset * 8)
#else
  sll     a2, a2, a3
#endif
  orc.b   a2, a2
  not a2, a2
  /*
   * Non-NUL bytes in the string have been expanded to 0x00, while
   * NUL bytes have become 0xff.  Search for the first set bit
   * (corresponding to a NUL byte in the original chunk).
   */
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
  ctz     a2, a2
#else
  clz     a2, a2
#endif
  /*
   * The first chunk is special: compare against the number of valid
   * bytes in this chunk.
   */
  srli    a0, a2, 3
  bgtu    a4, a0, .Ldone
  addi    a3, a1, SZREG
  li      a4, -1
  .align 2
  /*
   * Our critical loop is 4 instructions and processes data in 4 byte
   * or 8 byte chunks.
   */
.Lloop:
  REG_L   a2, SZREG(a1)
  addi    a1, a1, SZREG
  orc.b   a2, a2
  beq     a2, a4, .Lloop
.Lepilogue:
  not     a2, a2
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
  ctz     a2, a2
#else
  clz     a2, a2
#endif
  sub     a1, a1, a3
  add a0, a0, a1
  srli    a2, a2, 3
  add     a0, a0, a2
.Ldone:
  ret
```

代码注释译文：

- `offset`：偏移。
- `align pointer`：对齐指针。
- `XLEN - offset`：`XLEN - offset`。
- `offset * 8`：`offset * 8`。
- `chunk`：数据块。
- 将已加载的部分/非对齐数据块移位，移除字符串起始位置之前的字节，并在末尾添加 NUL 字节。
- 字符串中的非 NUL 字节已扩展为 `0x00`，而 NUL 字节已变为 `0xff`。搜索第一个置位比特，该比特对应原始数据块中的 NUL 字节。
- 第一个数据块比较特殊：需要与该数据块中的有效字节数进行比较。
- 关键循环为 4 条指令，并按 4 字节或 8 字节数据块处理数据。

## A.2. strcmp

```asm
#include <sys/asm.h>
  .text
  .globl strcmp
  .type  strcmp, @function
strcmp:
  or    a4, a0, a1
  li    t2, -1
  and   a4, a4, SZREG-1
  bnez  a4, .Lsimpleloop

  # Main loop for aligned strings
.Lloop:
  REG_L a2, 0(a0)
  REG_L a3, 0(a1)
  orc.b t0, a2
  bne   t0, t2, .Lfoundnull
  addi  a0, a0, SZREG
  addi  a1, a1, SZREG
  beq   a2, a3, .Lloop
  # Words don't match, and no null byte in first word.
  # Get bytes in big-endian order and compare.
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
  rev8  a2, a2
  rev8  a3, a3
#endif
  # Synthesize (a2 >= a3) ? 1 : -1 in a branchless sequence.
  sltu a0, a2, a3
  neg  a0, a0
  ori  a0, a0, 1
  ret
.Lfoundnull:
  # Found a null byte.
  # If words don't match, fall back to simple loop.
  bne   a2, a3, .Lsimpleloop
  # Otherwise, strings are equal.
  li    a0, 0
  ret
  # Simple loop for misaligned strings
.Lsimpleloop:
  lbu   a2, 0(a0)
  lbu   a3, 0(a1)
  addi  a0, a0, 1
  addi  a1, a1, 1
  bne   a2, a3, 1f
  bnez  a2, .Lsimpleloop
1:
  sub   a0, a2, a3
  ret
.size   strcmp, .-strcmp
```

代码注释译文：

- `Main loop for aligned strings`：已对齐字符串的主循环。
- `Words don't match, and no null byte in first word.`：字不匹配，并且第一个字中没有空字节。
- `Get bytes in big-endian order and compare.`：按大端顺序取得字节并进行比较。
- `Synthesize (a2 >= a3) ? 1 : -1 in a branchless sequence.`：用无分支序列合成 `(a2 >= a3) ? 1 : -1`。
- `Found a null byte.`：发现空字节。
- `If words don't match, fall back to simple loop.`：如果字不匹配，则回退到简单循环。
- `Otherwise, strings are equal.`：否则，字符串相等。
- `Simple loop for misaligned strings`：用于非对齐字符串的简单循环。

