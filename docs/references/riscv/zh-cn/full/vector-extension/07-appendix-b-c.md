# Appendix B: Calling Convention (Not authoritative - Placeholder Only)

> Note：本附录只是一个占位符，用于帮助说明代码示例中使用的约定；它不被视为冻结内容，也不属于批准流程的一部分。官方 RISC-V psABI 文档正在扩展，以规定 vector calling conventions。

在 RISC-V psABI 中，vector register `v0`-`v31` 全部为 caller-saved。`vl` 与 `vtype` CSR 也是 caller-saved。

过程可以假定进入时 `vstart` 为 0。过程可以假定从过程调用返回时 `vstart` 为 0。

> Note：应用软件通常不应显式写入 `vstart`。任何确实把 `vstart` 显式写为非零值的过程，必须在返回或调用另一个过程之前把 `vstart` 清零。

`vcsr` 的 `vxrm` 与 `vxsat` 字段具有 thread storage duration。

执行 system call 会使所有 caller-saved vector register（`v0`-`v31`、`vl`、`vtype`）和 `vstart` 变为 unspecified。

> Note：这种方案允许导致 context switch 的 system call 避免保存并随后恢复 vector register。

> Note：多数 OS 会选择保持这些 register 不变，或把它们复位到初始状态，以避免跨 process 边界泄露信息。

# Appendix C: Fractional `Lmul` example

本附录给出一个非规范性示例，帮助说明 compiler 可以在何处很好地利用 fractional `LMUL` 特性。

考虑以下用 C 编写的循环，虽然它有些刻意构造：

```c
void add_ref(long N,
    signed char *restrict c_c, signed char *restrict c_a, signed char *restrict c_b,
    long *restrict l_c, long *restrict l_a, long *restrict l_b,
    long *restrict l_d, long *restrict l_e, long *restrict l_f,
    long *restrict l_g, long *restrict l_h, long *restrict l_i,
    long *restrict l_j, long *restrict l_k, long *restrict l_l,
    long *restrict l_m) {
  long i;
  for (i = 0; i < N; i++) {
    c_c[i] = c_a[i] + c_b[i]; // 注意这个 'char' 加法制造了 mixed type 情况
    l_c[i] = l_a[i] + l_b[i];
    l_f[i] = l_d[i] + l_e[i];
    l_i[i] = l_g[i] + l_h[i];
    l_l[i] = l_k[i] + l_j[i];
    l_m[i] += l_m[i] + l_c[i] + l_f[i] + l_i[i] + l_l[i];
  }
}
```

该示例循环因为需要许多输入变量和临时量而具有很高的 register pressure。compiler 认识到循环中有两种数据类型：8 bit `char` 和 64 bit `long *`。如果没有 fractional `LMUL`，compiler 会被迫为 8 bit 计算使用 `LMUL=1`，并为 64 bit 计算使用 `LMUL=8`，以便同一循环迭代内所有计算具有相同元素数量。在 `LMUL=8` 下，register allocator 只有 4 个 register 可用。鉴于该循环需要大量 64 bit 变量和临时量，compiler 最终生成很多 spill code。下面的代码展示了这种效果：

```asm
.LBB0_4:                                # %vector.body
                                        # =>This Inner Loop Header: Depth=1
  add s9, a2, s6
  vsetvli s1, zero, e8,m1,ta,mu
  vle8.v v25, (s9)
  add s1, a3, s6
  vle8.v v26, (s1)
  vadd.vv v25, v26, v25
  add s1, a1, s6
  vse8.v v25, (s1)
  add s9, a5, s10
  vsetvli s1, zero, e64,m8,ta,mu
  vle64.v v8, (s9)
  add s1, a6, s10
  vle64.v v16, (s1)
  add s1, a7, s10
  vle64.v v24, (s1)
  add s1, s3, s10
  vle64.v v0, (s1)
  sd a0, -112(s0)
  ld a0, -128(s0)
  vs8r.v v0, (a0) # Spill LMUL=8
  add s9, t6, s10
  add s11, t5, s10
  add ra, t2, s10
  add s1, t3, s10
  vle64.v v0, (s9)
  ld s9, -136(s0)
  vs8r.v v0, (s9) # Spill LMUL=8
  vle64.v v0, (s11)
  ld s9, -144(s0)
  vs8r.v v0, (s9) # Spill LMUL=8
  vle64.v v0, (ra)
  ld s9, -160(s0)
  vs8r.v v0, (s9) # Spill LMUL=8
  vle64.v v0, (s1)
  ld s1, -152(s0)
  vs8r.v v0, (s1) # Spill LMUL=8
  vadd.vv v16, v16, v8
  ld s1, -128(s0)
  vl8r.v v8, (s1) # Reload LMUL=8
  vadd.vv v8, v8, v24
  ld s1, -136(s0)
  vl8r.v v24, (s1) # Reload LMUL=8
  ld s1, -144(s0)
  vl8r.v v0, (s1) # Reload LMUL=8
  vadd.vv v24, v0, v24
  ld s1, -128(s0)
  vs8r.v v24, (s1) # Spill LMUL=8
  ld s1, -152(s0)
  vl8r.v v0, (s1) # Reload LMUL=8
  ld s1, -160(s0)
  vl8r.v v24, (s1) # Reload LMUL=8
  vadd.vv v0, v0, v24
  add s1, a4, s10
  vse64.v v16, (s1)
  add s1, s2, s10
  vse64.v v8, (s1)
  vadd.vv v8, v8, v16
  add s1, t4, s10
  ld s9, -128(s0)
  vl8r.v v16, (s9) # Reload LMUL=8
  vse64.v v16, (s1)
  add s9, t0, s10
  vadd.vv v8, v8, v16
  vle64.v v16, (s9)
  add s1, t1, s10
  vse64.v v0, (s1)
  vadd.vv v8, v8, v0
  vsll.vi v16, v16, 1
  vadd.vv v8, v8, v16
  vse64.v v8, (s9)
  add s6, s6, s7
  add s10, s10, s8
  bne s6, s4, .LBB0_4
```

如果 compiler 不使用 `LMUL=1` 进行 8 bit 计算，而被允许使用 fractional `LMUL=1/2`，那么 64 bit 计算可以使用 `LMUL=4`（注意 64 bit 元素与 8 bit 元素的比例与前一个示例保持相同）。现在 compiler 有 8 个可用 register 执行 register allocation，因而没有 spill code，如下列循环所示：

```asm
.LBB0_4:                                # %vector.body
                                        # =>This Inner Loop Header: Depth=1
  add s9, a2, s6
  vsetvli s1, zero, e8,mf2,ta,mu // LMUL=1/2 !
  vle8.v v25, (s9)
  add s1, a3, s6
  vle8.v v26, (s1)
  vadd.vv v25, v26, v25
  add s1, a1, s6
  vse8.v v25, (s1)
  add s9, a5, s10
  vsetvli s1, zero, e64,m4,ta,mu // LMUL=4
  vle64.v v28, (s9)
  add s1, a6, s10
  vle64.v v8, (s1)
  vadd.vv v28, v8, v28
  add s1, a7, s10
  vle64.v v8, (s1)
  add s1, s3, s10
  vle64.v v12, (s1)
  add s1, t6, s10
  vle64.v v16, (s1)
  add s1, t5, s10
  vle64.v v20, (s1)
  add s1, a4, s10
  vse64.v v28, (s1)
  vadd.vv v8, v12, v8
  vadd.vv v12, v20, v16
  add s1, t2, s10
  vle64.v v16, (s1)
  add s1, t3, s10
  vle64.v v20, (s1)
  add s1, s2, s10
  vse64.v v8, (s1)
  add s9, t4, s10
  vadd.vv v16, v20, v16
  add s11, t0, s10
  vle64.v v20, (s11)
  vse64.v v12, (s9)
  add s1, t1, s10
  vse64.v v16, (s1)
  vsll.vi v20, v20, 1
  vadd.vv v28, v8, v28
  vadd.vv v28, v28, v12
  vadd.vv v28, v28, v16
  vadd.vv v28, v28, v20
  vse64.v v28, (s11)
  add s6, s6, s7
  add s10, s10, s8
  bne s6, s4, .LBB0_4
```
