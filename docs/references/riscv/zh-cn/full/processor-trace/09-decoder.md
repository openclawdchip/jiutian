# Chapter 9 Decoder

该 decoder implementation 假定没有 branch predictor 或 return address stack，即 `return_stack_size_p` 和 `bpred_size_p` 均为 zero。

encoder 和 decoder 的 reference C-code implementations 可在以下位置找到：

`https://github.com/riscv/riscv-trace-spec/tree/master/te_codec/src`

## 9.1 Decoder pseudo code

下面为 decoder pseudo code。注释已翻译，函数名、变量名、字段名、opcode 名保持原文。

```text
# global variables
global pc                                  # 重建的 program counter
global last_pc                             # previous instruction 的 PC
global branches = 0                        # 待处理 branches 数量
global branch_map = 0                      # branch 的 not taken/taken (1/0) status 的 bit vector
                                           # for branches
global bool stop_at_last_branch = FALSE    # 标志：reconstruction 应在 final branch 结束
global bool inferred_address = FALSE       # 标志：format 0/1/2 报告的 address 不是
                                           # uninferable jump 后续地址，因此是 inferred
global bool start_of_trace = TRUE          # 标志：第 1 个 trace packet 尚待处理
global address                             # 从 te_inst messages 重建出的 address
global options                             # Operating mode flags
global array return_stack                  # 保存 return address stack 的 array
global irstack_depth = 0                   # return address stack 的 depth

# Process te_inst packet. 每次收到 te_inst packet 时调用 #
function process_te_inst (te_inst)
if (te_inst.format == 3)
    if (te_inst.subformat == 3) # Support packet
        process_support(te_inst)
        return
    if (te_inst.subformat == 2) # Context packet
        return
    inferred_address = FALSE
    address = (te_inst.address << discovery_response.iaddress_lsb)
    if (te_inst.subformat == 1 or start_of_trace)
        branches = 0
        branch_map = 0
    if (is_branch(get_instr(address))) # 如果该 instruction 是 branch，则有 1 个 unprocessed branch
        branch_map = branch_map | (te_inst.branch << branches)
        branches++
    if (te_inst.subformat == 0 and !start_of_trace)
        follow_execution_path(address, te_inst)
    else
        pc = address
        last_pc = pc # previous pc 未知，但保证 is_sequential_jump() 正确运行
    start_of_trace = FALSE
    irstack_depth = 0
else
    if (start_of_trace) # 这不应发生
        ERROR: Expecting trace to start with format 3
        return
    if (te_inst.format == 2 or te_inst.branches != 0)
        stop_at_last_branch = FALSE
        if (options.full_address)
            address = (te_inst.address << discovery_response.iaddress_lsb)
        else
            address += (te_inst.address << discovery_response.iaddress_lsb)
    if (te_inst.format == 1)
        stop_at_last_branch = (te_inst.branches == 0)
        # Branch map 将包含 <= 1 个 branch（如果最后 reported instruction 是 branch，则为 1）
        branch_map = branch_map | (te_inst.branch_map << branches)
        if (te_inst.branches == 0)
            branches += 31
        else
            branches += te_inst.branches
    follow_execution_path(address, te_inst)

# Follow execution path to reported address #
function follow_execution_path(address, te_inst)
local previous_address = pc
local stop_here = FALSE
while (TRUE)
    if (inferred_address) # 从 previously reported address 再迭代一次，以找到第二次出现
        stop_here = next_pc(previous_address)
        if (stop_here)
            inferred_address = FALSE
    else
        stop_here = next_pc(address)
    if (branches == 1 and is_branch(get_instr(pc)) and stop_at_last_branch)
        # 到达 final branch，在此停止；不要跟随到 next instruction，
        # 因为还不知道它是否 retires
        stop_at_last_branch = FALSE
        return
    if (stop_here)
        # 到达 uninferable discontinuity 后续 reported address；在此停止
        if (branches > (is_branch(get_instr(pc)) ? 1 : 0))
            # 检查所有 branches 已处理，若该 instruction 是 branch，则允许剩 1 个
            ERROR: unprocessed branches
        return
    if (te_inst.format != 3 and pc == address and !stop_at_last_branch and
        (te_inst.notify != get_previous_bit(te_inst, "notify")) and
        (branches == (is_branch(get_instr(pc)) ? 1 : 0)))
        # 所有 branches 已处理，且因 notification 到达 reported address，
        # 而不是作为 uninferable jump target
        return
    if (te_inst.format != 3 and pc == address and !stop_at_last_branch and
        !is_uninferable_discon(get_instr(last_pc)) and
        (te_inst.updiscon == get_previous_bit(te_inst, "updiscon")) and
        (branches == (is_branch(get_instr(pc)) ? 1 : 0)) and
        ((te_inst.irreport == get_previous_bit(te_inst, "irreport")) or
         te_inst.irdepth == irstack_depth))
        # 所有 branches 已处理，并到达 reported address，但它不是
        # uninferable jump target。暂时在此停止，标志表示这可能不是
        # final retired instruction
        inferred_address = TRUE
        return
    if (te_inst.format == 3 and pc == address and
        (branches == (is_branch(get_instr(pc)) ? 1 : 0)))
        # 所有 branches 已处理，并到达 reported address
        return

# Compute next PC #
function next_pc (address)
local instr = get_instr(pc)
local this_pc = pc
local stop_here = FALSE
if (is_inferable_jump(instr))
    pc += instr.imm
else if (is_sequential_jump(instr, last_pc)) # lui/auipc 后跟使用同一 register 的 jump
    pc = sequential_jump_target(pc, last_pc)
else if (is_implicit_return(instr))
    pc = pop_return_stack()
else if (is_uninferable_discon(instr))
    if (stop_at_last_branch)
        ERROR: unexpected uninferable discontinuity
    else
        pc = address
        stop_here = TRUE
else if (is_taken_branch(instr))
    pc += instr.imm
else
    pc += instruction_size(instr)
if (is_call(instr))
    push_return_stack(this_pc)
last_pc = this_pc
return stop_here

# Process support packet #
function process_support (te_inst)
local stop_here = FALSE
options = te_inst.options
if (te_inst.qual_status != no_change)
    start_of_trace = TRUE # Trace ended，因此准备再次开始
if (te_inst.qual_status == ended_upd and inferred_address)
    local previous_address = pc
    inferred_address = FALSE
    while (TRUE)
        stop_here = next_pc(previous_address)
        if (stop_here)
            return
return

# Determine if instruction is a branch, adjust branch count/map,
# and return taken status #
function is_taken_branch (instr)
local bool taken = FALSE
if (!is_branch(instr))
    return FALSE
if (branches == 0)
    ERROR: cannot resolve branch
else
    taken = !branch_map[0]
    branches--
    branch_map >> 1
return taken

# Determine if instruction is a branch #
function is_branch (instr)
if ((instr.opcode == BEQ) or
    (instr.opcode == BNE) or
    (instr.opcode == BLT) or
    (instr.opcode == BGE) or
    (instr.opcode == BLTU) or
    (instr.opcode == BGEU) or
    (instr.opcode == C.BEQZ) or
    (instr.opcode == C.BNEZ))
    return TRUE
return FALSE

# Determine if instruction is an inferable jump #
function is_inferable_jump (instr)
if ((instr.opcode == JAL) or
    (instr.opcode == C.JAL) or
    (instr.opcode == C.J) or
    (instr.opcode == JALR and instr.rs1 == 0))
    return TRUE
return FALSE

# Determine if instruction is an uninferable jump #
function is_uninferable_jump (instr)
if ((instr.opcode == JALR and instr.rs1 != 0) or
    (instr.opcode == C.JALR) or
    (instr.opcode == C.JR))
    return TRUE
return FALSE

# Determine if instruction is an uninferable discontinuity #
function is_uninferable_discon (instr)
if (is_uninferable_jump(instr) or
    (instr.opcode == URET) or
    (instr.opcode == SRET) or
    (instr.opcode == MRET) or
    (instr.opcode == DRET) or
    (instr.opcode == ECALL) or
    (instr.opcode == EBREAK) or
    (instr.opcode == C.EBREAK))
    return TRUE
return FALSE

# Determine if instruction is a sequentially inferable jump #
function is_sequential_jump (instr, prev_addr)
if (not (is_uninferable_jump(instr) and options.sijump))
    return FALSE
local prev_instr = get_instr(prev_addr)
if((prev_instr.opcode == AUIPC) or
   (prev_instr.opcode == LUI) or
   (prev_instr.opcode == C.LUI))
    return (instr.rs1 == prev_instr.rd)
return FALSE

# Find the target of a sequentially inferable jump #
function sequential_jump_target (addr, prev_addr)
local instr = get_instr(addr)
local prev_instr = get_instr(prev_addr)
local target = 0
if (prev_instr.opcode == AUIPC)
    target = prev_addr
target += prev_instr.imm
if (instr.opcode == JALR)
    target += instr.imm
return target

# Determine if instruction is a call #
# - excludes tail calls as they do not push an address onto the return stack
function is_call (instr)
if ((instr.opcode == JALR and instr.rd == 1) or
    (instr.opcode == C.JALR) or
    (instr.opcode == JAL and instr.rd == 1) or
    (instr.opcode == C.JAL))
    return TRUE
return FALSE

# Determine if instruction return address can be implicitly inferred #
function is_implicit_return (instr)
if (options.implicit_return == 0) # Implicit return mode disabled
    return FALSE
if ((instr.opcode == JALR and instr.rs1 == 1 and instr.rd == 0) or
    (instr.opcode == C.JR and instr.rs1 == 1))
    if ((te_inst.irreport != get_previous_bit(te_inst, "irreport")) and
        te_inst.irdepth == irstack_depth)
        return FALSE
    return (irstack_depth > 0)
return FALSE

# Push address onto return stack #
function push_return_stack (address)
if (options.implicit_return == 0) # Implicit return mode disabled
    return
local irstack_depth_max = discovery_response.return_stack_size ?
    2**discovery_response.return_stack_size :
    2**discovery_response.call_counter_size
local instr = get_instr(address)
local link = address
if (irstack_depth == irstack_depth_max)
    # 删除 stack 中最旧 entry，为下面新增 entry 腾出空间
    irstack_depth--
    for (i = 0; i < irstack_depth; i++)
        return_stack[i] = return_stack[i+1]
link += instruction_size(instr)
return_stack[irstack_depth] = link
irstack_depth++
return

# Pop address from return stack #
function pop_return_stack ()
irstack_depth-- # 该 function 不会在 irstack_depth 为 0 时调用，因此无需检查 underflow
local link = return_stack[irstack_depth]
return link
```
