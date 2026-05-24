

import cocotb
from cocotb.triggers import Timer
from ..common.config import *
from ..common.instruction_builder import *


async def drive_and_check_data_proc(
    dut,
    *,
    name,
    opcode,
    uses_imm=1,
    set_cond=0,
    rn=0,
    rd=0,
    operand2=1,
):
    instr = build_data_proc_instr(
        uses_imm=uses_imm,
        opcode=opcode,
        set_cond=set_cond,
        rn=rn,
        rd=rd,
        operand2=operand2,
    )


    dut.i_instr.value = instr

    await Timer(1, unit="ns")

    dut._log.info("Testing %s instruction: 0x%08x", name, instr)
    dut._log.info("Decoded packed instruction: 0x%x", int(dut.decoded.value))

    actual_instr_class = int(dut.w_instr_class.value)
    actual_alu_opcode  = int(dut.w_alu_opcode.value)
    actual_uses_imm    = int(dut.w_uses_imm.value)
    actual_set_cond    = int(dut.w_set_cond.value)
    actual_rn          = int(dut.w_rn.value)
    actual_rd          = int(dut.w_rd.value)
    actual_op2         = int(dut.w_op2.value)

    assert actual_instr_class == CLASS_ALU, (
        f"[{name}] instr_class got 0b{actual_instr_class:02b}, "
        f"expected 0b{CLASS_ALU:02b}"
    )

    assert actual_alu_opcode == opcode, (
        f"[{name}] alu_opcode got 0b{actual_alu_opcode:04b}, "
        f"expected 0b{opcode:04b}"
    )

    assert actual_uses_imm == uses_imm, (
        f"[{name}] uses_imm got 0b{actual_uses_imm:b}, "
        f"expected 0b{uses_imm:b}"
    )

    assert actual_set_cond == set_cond, (
        f"[{name}] set_cond got 0b{actual_set_cond:b}, "
        f"expected 0b{set_cond:b}"
    )

    assert actual_rn == rn, (
        f"[{name}] set_cond got 0b{actual_rn:b}, "
        f"expected 0b{rn:b}"
    )

    assert actual_rd == rd, (
        f"[{name}] set_cond got 0b{actual_rd:b}, "
        f"expected 0b{rd:b}"
    )

    assert actual_op2 == operand2, (
        f"[{name}] set_cond got 0b{actual_op2:b}, "
        f"expected 0b{operand2:b}"
    )


async def drive_and_check_mem_instr(
    dut,
    *,
    name,
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
    instr = build_single_data_transfer_instr(
        uses_reg_offset=uses_reg_offset,
        pre_index=pre_index,
        offset_dir=offset_dir,
        is_byte=is_byte,
        writeback=writeback,
        is_load=is_load,
        rn=rn,
        rd=rd,
        offset=offset,
    )

    dut.i_instr.value = instr

    await Timer(1, unit="ns")

    dut._log.info("Testing %s instruction: 0x%08x", name, instr)
    dut._log.info("Decoded packed instruction: 0x%x", int(dut.decoded.value))

    actual_instr_class = int(dut.w_instr_class.value)

    assert actual_instr_class == CLASS_MEM, (
        f"[{name}] instr_class got 0b{actual_instr_class:02b}, "
        f"expected 0b{CLASS_MEM:02b}"
    )

    assert int(dut.w_uses_imm.value) == uses_reg_offset, (
        f"[{name}] I-bit got {int(dut.w_uses_imm.value)}, "
        f"expected {uses_reg_offset}"
    )

    assert int(dut.w_pre_index.value) == pre_index, (
        f"[{name}] P-bit got {int(dut.w_pre_index.value)}, "
        f"expected {pre_index}"
    )

    assert int(dut.w_offset_dir.value) == offset_dir, (
        f"[{name}] U-bit got {int(dut.w_offset_dir.value)}, "
        f"expected {offset_dir}"
    )

    assert int(dut.w_is_byte.value) == is_byte, (
        f"[{name}] B-bit got {int(dut.w_is_byte.value)}, "
        f"expected {is_byte}"
    )

    assert int(dut.w_writeback.value) == writeback, (
        f"[{name}] W-bit got {int(dut.w_writeback.value)}, "
        f"expected {writeback}"
    )

    assert int(dut.w_is_load.value) == is_load, (
        f"[{name}] L-bit got {int(dut.w_is_load.value)}, "
        f"expected {is_load}"
    )

    assert int(dut.w_rn.value) == rn, (
        f"[{name}] rn got R{int(dut.w_rn.value)}, expected R{rn}"
    )

    assert int(dut.w_rd.value) == rd, (
        f"[{name}] rd got R{int(dut.w_rd.value)}, expected R{rd}"
    )

    assert int(dut.w_offset.value) == offset, (
        f"[{name}] offset got 0x{int(dut.w_offset.value):03x}, "
        f"expected 0x{offset:03x}"
    )

async def drive_and_check_branch_instr(
    dut,
    *,
    name,
    is_link,
    offset,
):
    instr = build_branch_instr(
        is_link=is_link,
        offset=offset,
    )

    dut.i_instr.value = instr

    await Timer(1, unit="ns")

    dut._log.info("Testing %s instruction: 0x%08x", name, instr)
    dut._log.info("Decoded packed instruction: 0x%x", int(dut.decoded.value))

    actual_instr_class = int(dut.w_instr_class.value)
    actual_is_link     = int(dut.w_is_link.value)
    actual_offset      = int(dut.w_offset.value)

    assert actual_instr_class == CLASS_BRANCH, (
        f"[{name}] instr_class got 0b{actual_instr_class:02b}, "
        f"expected 0b{CLASS_BRANCH:02b}"
    )

    assert actual_is_link == is_link, (
        f"[{name}] is_link got {actual_is_link}, expected {is_link}"
    )

    assert actual_offset == (offset & 0xFFFFFF), (
        f"[{name}] offset got 0x{actual_offset:06x}, "
        f"expected 0x{(offset & 0xFFFFFF):06x}"
    )