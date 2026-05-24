

from ..common.config import * 


def build_data_proc_instr(
    cond=0b0000,
    uses_imm=1,
    opcode=ARM_ADD,
    set_cond=0,
    rn=0,
    rd=0,
    operand2=1,
):
    """
    Build a simplified ARM data-processing instruction.

    Format:
    [31:28] cond
    [27:26] class = 00 for data processing / ALU
    [25]    I bit
    [24:21] opcode
    [20]    S bit
    [19:16] Rn
    [15:12] Rd
    [11:0]  Operand2
    """

    instr = 0
    instr |= (cond     & 0xF)  << 28
    instr |= (CLASS_ALU & 0x3) << 26
    instr |= (uses_imm & 0x1)  << 25
    instr |= (opcode   & 0xF)  << 21
    instr |= (set_cond & 0x1)  << 20
    instr |= (rn       & 0xF)  << 16
    instr |= (rd       & 0xF)  << 12
    instr |= (operand2 & 0xFFF)

    return instr


def build_single_data_transfer_instr(
    *,
    cond=0b0000,
    uses_reg_offset=0,
    pre_index=1,
    offset_dir=1,
    is_byte=0,
    writeback=0,
    is_load=1,
    rn=0,
    rd=0,
    offset=0,
):
    """
    Build simplified ARM LDR/STR instruction.

    ARM single data transfer format:
    [31:28] cond
    [27:26] class = 01
    [25]    I bit, 0 = immediate offset, 1 = register offset
    [24]    P bit, pre/post indexing
    [23]    U bit, add/subtract offset
    [22]    B bit, byte/word
    [21]    W bit, writeback
    [20]    L bit, 1 = load, 0 = store
    [19:16] Rn base register
    [15:12] Rd source/destination register
    [11:0]  offset
    """

    instr = 0
    instr |= (cond            & 0xF)   << 28
    instr |= (CLASS_MEM       & 0x3)   << 26
    instr |= (uses_reg_offset & 0x1)   << 25
    instr |= (pre_index       & 0x1)   << 24
    instr |= (offset_dir      & 0x1)   << 23
    instr |= (is_byte         & 0x1)   << 22
    instr |= (writeback       & 0x1)   << 21
    instr |= (is_load         & 0x1)   << 20
    instr |= (rn              & 0xF)   << 16
    instr |= (rd              & 0xF)   << 12
    instr |= (offset          & 0xFFF)

    return instr


def build_branch_instr(
    *,
    cond=0b0000,
    is_link=0,
    offset=0,
):
    """
    Build simplified ARM branch instruction.

    Format:
    [31:28] cond
    [27:26] class = 10
    [25]    branch encoding bit, set to 1 for real ARM-style branch
    [24]    L bit, 1 = branch with link
    [23:0]  signed branch offset field, raw here
    """

    instr = 0
    instr |= (cond         & 0xF)      << 28
    instr |= (CLASS_BRANCH & 0x3)      << 26
    instr |= 1                         << 25
    instr |= (is_link      & 0x1)      << 24
    instr |= (offset       & 0xFFFFFF)

    return instr
