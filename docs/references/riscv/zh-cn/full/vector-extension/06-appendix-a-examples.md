# Appendix A: Vector Assembly Code Examples

以下内容作为非规范性文本提供，用于帮助说明 vector ISA。

## A.1. Vector-vector add example

```asm
    # 32 bit integer 的 vector-vector add 例程
    # void vvaddint32(size_t n, const int*x, const int*y, int*z)
    # { for (size_t i=0; i<n; i++) { z[i]=x[i]+y[i]; } }
    #
    # a0 = n, a1 = x, a2 = y, a3 = z
    # 非 vector 指令缩进显示
vvaddint32:
    vsetvli t0, a0, e32, ta, ma  # 根据 32 bit vector 设置 vector length
    vle32.v v0, (a1)             # 取得第一个 vector
      sub a0, a0, t0             # 递减已完成数量
      slli t0, t0, 2             # 已完成数量乘以 4 byte
      add a1, a1, t0             # 推进指针
    vle32.v v1, (a2)             # 取得第二个 vector
      add a2, a2, t0             # 推进指针
    vadd.vv v2, v0, v1           # vector 求和
    vse32.v v2, (a3)             # 存储结果
      add a3, a3, t0             # 推进指针
      bnez a0, vvaddint32        # 回到循环
      ret                        # 完成
```

## A.2. Example with mixed-width mask and compute

```asm
# 使用一种宽度计算 predicate，使用另一种宽度执行 masked compute。
#   int8_t a[]; int32_t b[], c[];
#   for (i=0;  i<n; i++) { b[i] =  (a[i] < 5) ? c[i] : 1; }
#
# mixed-width 代码保持 SEW/LMUL=8
loop:
    vsetvli a4, a0, e8, m1, ta, ma    # 用 byte vector 计算 predicate
    vle8.v v1, (a1)                   # 加载 a[i]
      add a1, a1, a4                  # 推进指针
    vmslt.vi v0, v1, 5                # a[i] < 5?

    vsetvli x0, a0, e32, m4, ta, mu   # 32 bit 值的 vector
      sub a0, a0, a4                  # 递减计数
    vmv.v.i v4, 1                     # 将 immediate splat 到 destination
    vle32.v v4, (a3), v0.t            # 加载请求的 C 元素，其他元素保持不变
      sll t1, a4, 2
      add a3, a3, t1                  # 推进指针
    vse32.v v4, (a2)                  # 存储 b[i]
      add a2, a2, t1                  # 推进指针
      bnez a0, loop                   # 还有元素吗？
```

## A.3. Memcpy example

```asm
    # void *memcpy(void* dest, const void* src, size_t n)
    # a0=dest, a1=src, a2=n
memcpy:
      mv a3, a0                       # 复制 destination
loop:
    vsetvli t0, a2, e8, m8, ta, ma    # 8 bit vector
    vle8.v v0, (a1)                   # 加载 byte
      add a1, a1, t0                  # 推进指针
      sub a2, a2, t0                  # 递减计数
    vse8.v v0, (a3)                   # 存储 byte
      add a3, a3, t0                  # 推进指针
      bnez a2, loop                   # 还有元素吗？
      ret                             # 返回
```

## A.4. Conditional example

```asm
# (int16) z[i] = ((int8) x[i] < 5) ? (int16) a[i] : (int16) b[i];
loop:
    vsetvli t0, a0, e8, m1, ta, ma    # 使用 8 bit 元素
    vle8.v v0, (a1)                   # 取得 x[i]
      sub a0, a0, t0                  # 递减元素计数
      add a1, a1, t0                  # 推进 x[i] 指针
    vmslt.vi v0, v0, 5                # 在 v0 中设置 mask
    vsetvli t0, a0, e16, m2, ta, mu   # 使用 16 bit 元素
      slli t0, t0, 1                  # 乘以 2 byte
    vle16.v v2, (a2), v0.t            # z[i] = a[i] 情况
    vmnot.m v0, v0                    # 反转 v0
      add a2, a2, t0                  # 推进 a[i] 指针
    vle16.v v2, (a3), v0.t            # z[i] = b[i] 情况
      add a3, a3, t0                  # 推进 b[i] 指针
    vse16.v v2, (a4)                  # 存储 z
      add a4, a4, t0                  # 推进 z[i] 指针
      bnez a0, loop
```

## A.5. SAXPY example

```asm
# void
# saxpy(size_t n, const float a, const float *x, float *y)
# {
#   size_t i;
#   for (i=0; i<n; i++)
#     y[i] = a * x[i] + y[i];
# }
#
# register arguments:
#     a0      n
#     fa0     a
#     a1      x
#     a2      y
saxpy:
    vsetvli a4, a0, e32, m8, ta, ma
    vle32.v v0, (a1)
    sub a0, a0, a4
    slli a4, a4, 2
    add a1, a1, a4
    vle32.v v8, (a2)
    vfmacc.vf v8, fa0, v0
    vse32.v v8, (a2)
    add a2, a2, a4
    bnez a0, saxpy
    ret
```

## A.6. SGEMM example

```asm
# RV64IDV system
#
# void
# sgemm_nn(size_t n,
#          size_t m,
#          size_t k,
#          const float*a,   // m * k matrix
#          size_t lda,
#          const float*b,   // k * n matrix
#          size_t ldb,
#          float*c,         // m * n matrix
#          size_t ldc)
#
#  c += a*b (alpha=1, 输入矩阵不转置)
#  matrix 按 C row-major order 存储

#define n a0
#define m a1
#define k a2
#define ap a3
#define astride a4
#define bp a5
#define bstride a6
#define cp a7
#define cstride t0
#define kt t1
#define nt t2
#define bnp t3
#define cnp t4
#define akp t5
#define bkp s0
#define nvl s1
#define ccp s2
#define amp s3

# 将 args 用作额外临时量
#define ft12 fa0
#define ft13 fa1
#define ft14 fa2
#define ft15 fa3

# 此版本在内层循环中把 C matrix 的 16*VLMAX block 保存在 vector register 中，
# 但除此之外不做 cache 或 TLB tiling。

sgemm_nn:
    addi sp, sp, -FRAMESIZE
    sd s0, OFFSET(sp)
    sd s1, OFFSET(sp)
    sd s2, OFFSET(sp)

    # 检查零大小 matrix
    beqz n, exit
    beqz m, exit
    beqz k, exit

    # 将元素 stride 转换为 byte stride
    ld cstride, OFFSET(sp)            # 从 stack frame 取得参数
    slli astride, astride, 2
    slli bstride, bstride, 2
    slli cstride, cstride, 2

    slti t6, m, 16
    bnez t6, end_rows

c_row_loop:                           # 跨 C block 行循环
    mv nt, n                          # 初始化下一行 C block 的 n counter
    mv bnp, bp                        # 初始化 B n-loop pointer
    mv cnp, cp                        # 初始化 C n-loop pointer

c_col_loop:                           # 跨一行 C block 循环
    vsetvli nvl, nt, e32, ta, ma      # 32 bit vector, LMUL=1
    mv akp, ap                        # 将 A 指针复位到开头
    mv bkp, bnp                       # 步进到 B matrix 下一列

    # 从内存初始化当前 C submatrix block
    vle32.v  v0, (cnp); add ccp, cnp, cstride;
    vle32.v  v1, (ccp); add ccp, ccp, cstride;
    vle32.v  v2, (ccp); add ccp, ccp, cstride;
    vle32.v  v3, (ccp); add ccp, ccp, cstride;
    vle32.v  v4, (ccp); add ccp, ccp, cstride;
    vle32.v  v5, (ccp); add ccp, ccp, cstride;
    vle32.v  v6, (ccp); add ccp, ccp, cstride;
    vle32.v  v7, (ccp); add ccp, ccp, cstride;
    vle32.v  v8, (ccp); add ccp, ccp, cstride;
    vle32.v  v9, (ccp); add ccp, ccp, cstride;
    vle32.v v10, (ccp); add ccp, ccp, cstride;
    vle32.v v11, (ccp); add ccp, ccp, cstride;
    vle32.v v12, (ccp); add ccp, ccp, cstride;
    vle32.v v13, (ccp); add ccp, ccp, cstride;
    vle32.v v14, (ccp); add ccp, ccp, cstride;
    vle32.v v15, (ccp)

    mv kt, k                          # 初始化 inner loop counter
    # 内层循环按 vfmacc 指令 4-cycle occupancy 和 single-issue pipeline 调度
    # Software pipeline loads
    flw ft0, (akp); add amp, akp, astride;
    flw ft1, (amp); add amp, amp, astride;
    flw ft2, (amp); add amp, amp, astride;
    flw ft3, (amp); add amp, amp, astride;
    # 从 B matrix 取得 vector
    vle32.v v16, (bkp)

k_loop:
    vfmacc.vf v0, ft0, v16
    add bkp, bkp, bstride
    flw ft4, (amp)
    add amp, amp, astride
    vfmacc.vf v1, ft1, v16
    addi kt, kt, -1                   # 递减 k counter
    flw ft5, (amp)
    add amp, amp, astride
    vfmacc.vf v2, ft2, v16
    flw ft6, (amp)
    add amp, amp, astride
    flw ft7, (amp)
    vfmacc.vf v3, ft3, v16
    add amp, amp, astride
    flw ft8, (amp)
    add amp, amp, astride
    vfmacc.vf v4, ft4, v16
    flw ft9, (amp)
    add amp, amp, astride
    vfmacc.vf v5, ft5, v16
    flw ft10, (amp)
    add amp, amp, astride
    vfmacc.vf v6, ft6, v16
    flw ft11, (amp)
    add amp, amp, astride
    vfmacc.vf v7, ft7, v16
    flw ft12, (amp)
    add amp, amp, astride
    vfmacc.vf v8, ft8, v16
    flw ft13, (amp)
    add amp, amp, astride
    vfmacc.vf v9, ft9, v16
    flw ft14, (amp)
    add amp, amp, astride
    vfmacc.vf v10, ft10, v16
    flw ft15, (amp)
    add amp, amp, astride
    addi akp, akp, 4                  # 移到 a 的下一列
    vfmacc.vf v11, ft11, v16
    beqz kt, 1f                       # 不越过 matrix 末尾加载
    flw ft0, (akp)
    add amp, akp, astride
1:  vfmacc.vf v12, ft12, v16
    beqz kt, 1f
    flw ft1, (amp)
    add amp, amp, astride
1:  vfmacc.vf v13, ft13, v16
    beqz kt, 1f
    flw ft2, (amp)
    add amp, amp, astride
1:  vfmacc.vf v14, ft14, v16
    beqz kt, 1f                       # 跳出循环
    flw ft3, (amp)
    add amp, amp, astride
    vfmacc.vf v15, ft15, v16
    vle32.v v16, (bkp)                # 取得 B matrix 的下一个 vector，与 jump stall 重叠
    j k_loop

1:  vfmacc.vf v15, ft15, v16

    # 将 C matrix block 保存回内存
    vse32.v  v0, (cnp); add ccp, cnp, cstride;
    vse32.v  v1, (ccp); add ccp, ccp, cstride;
    vse32.v  v2, (ccp); add ccp, ccp, cstride;
    vse32.v  v3, (ccp); add ccp, ccp, cstride;
    vse32.v  v4, (ccp); add ccp, ccp, cstride;
    vse32.v  v5, (ccp); add ccp, ccp, cstride;
    vse32.v  v6, (ccp); add ccp, ccp, cstride;
    vse32.v  v7, (ccp); add ccp, ccp, cstride;
    vse32.v  v8, (ccp); add ccp, ccp, cstride;
    vse32.v  v9, (ccp); add ccp, ccp, cstride;
    vse32.v v10, (ccp); add ccp, ccp, cstride;
    vse32.v v11, (ccp); add ccp, ccp, cstride;
    vse32.v v12, (ccp); add ccp, ccp, cstride;
    vse32.v v13, (ccp); add ccp, ccp, cstride;
    vse32.v v14, (ccp); add ccp, ccp, cstride;
    vse32.v v15, (ccp)

    # 下列 tail 指令应在 C block save 的空闲 slot 中更早调度。
    # 这里为了清晰保留在此处。
    # 推进跨一行 block 循环的指针
    slli t6, nvl, 2
    add cnp, cnp, t6                  # 移动 C block pointer
    add bnp, bnp, t6                  # 移动 B block pointer
    sub nt, nt, nvl                   # 递减 n 维元素计数
    bnez nt, c_col_loop               # 还有工作吗？

    # 移到下一组行
    addi m, m, -16                    # 上面处理了 16 行
    slli t6, astride, 4               # astride 乘以 16
    add ap, ap, t6                    # A matrix pointer 下移 16 行
    slli t6, cstride, 4               # cstride 乘以 16
    add cp, cp, t6                    # C matrix pointer 下移 16 行

    slti t6, m, 16
    beqz t6, c_row_loop

    # 处理 matrix 末尾少于 16 行的情况。
    # 可根据 code-size 考量，使用按 2 的幂递减的较小版本。
end_rows:
    # 未完成。

exit:
    ld s0, OFFSET(sp)
    ld s1, OFFSET(sp)
    ld s2, OFFSET(sp)
    addi sp, sp, FRAMESIZE
    ret
```

## A.7. Division approximation example

```asm
# v1 = v1 / v2，达到接近 23 bit precision。
vfrec7.v v3, v2             # 估计 1/v2
  li t0, 0x40000000
vmv.v.x v4, t0              # Splat 2.0
vfnmsac.vv v4, v2, v3       # 2.0 - v2 * est(1/v2)
vfmul.vv v3, v3, v4         # 更好的 1/v2 估计
vmv.v.x v4, t0              # Splat 2.0
vfnmsac.vv v4, v2, v3       # 2.0 - v2 * est(1/v2)
vfmul.vv v3, v3, v4         # 更好的 1/v2 估计
vfmul.vv v1, v1, v3         # v1/v2 的估计
```

## A.8. Square root approximation example

```asm
# v1 = sqrt(v1)，达到接近 23 bit precision。
  fmv.w.x ft0, x0           # 屏蔽零输入
vmfne.vf v0, v1, ft0        #   以避免 div by zero
vfrsqrt7.v v2, v1, v0.t     # 估计 1/sqrt(x)
vmfne.vf v0, v2, ft0, v0.t  # 额外屏蔽 +inf 输入
  li t0, 0xbf000000
  fmv.w.x ft0, t0           # -0.5
vfmul.vf v3, v1, ft0, v0.t  # -0.5 * x
vfmul.vv v4, v2, v2, v0.t   # est * est
  li t0, 0x3fc00000
vmv.v.x v5, t0, v0.t        # Splat 1.5
vfmadd.vv v4, v3, v5, v0.t  # 1.5 - 0.5 * x * est * est
vfmul.vv v1, v1, v4, v0.t   # 估计到 14 bit
vfmul.vv v4, v1, v1, v0.t   # est * est
vfmadd.vv v4, v3, v5, v0.t  # 1.5 - 0.5 * x * est * est
vfmul.vv v1, v1, v4, v0.t   # 估计到 23 bit
```

## A.9. C standard library `strcmp` example

```asm
  # int strcmp(const char *src1, const char* src2)
strcmp:
    ## 使用 LMUL=2，但同样的 register name 对更大 LMUL 也工作
    li t1, 0                         # 初始 pointer bump
loop:
    vsetvli t0, x0, e8, m2, ta, ma   # 最大长度 byte vector
    add a0, a0, t1                   # 推进 src1 pointer
    vle8ff.v v8, (a0)                # 取得 src1 byte
    add a1, a1, t1                   # 推进 src2 pointer
    vle8ff.v v16, (a1)               # 取得 src2 byte

    vmseq.vi v0, v8, 0               # 标记 src1 中的 zero byte
    vmsne.vv v1, v8, v16             # 标记 src1 != src2
    vmor.mm v0, v0, v1               # 合并退出条件

    vfirst.m a2, v0                  # ==0 或 != ?
    csrr t1, vl                      # 取得已获取的 byte 数
    bltz a2, loop                    # 如果全相同且无 zero byte，继续循环

    add a0, a0, a2                   # 取得 src1 element address
    lbu a3, (a0)                     # 从内存取得 src1 byte
    add a1, a1, a2                   # 取得 src2 element address
    lbu a4, (a1)                     # 从内存取得 src2 byte
    sub a0, a3, a4                   # return value
    ret
```
