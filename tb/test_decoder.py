

# test_decoder.py

import os
from pathlib import Path

import cocotb
from cocotb_tools.runner import get_runner
from cocotb.triggers import Timer



def get_packed_field(handle, start, stop=None):
    full_value = handle.value
    if stop is None:
        return full_value[start]
    else:
        return full_value[start:stop]


import cocotb
from cocotb.triggers import Timer


# ARM data-processing opcode values
ARM_AND = 0b0000
ARM_SUB = 0b0010
ARM_ADD = 0b0100
ARM_CMN = 0b1011
ARM_TEQ = 0b1001
ARM_MVN = 0b1111

CLASS_ALU    = 0b00
CLASS_MEM    = 0b01
CLASS_BRANCH = 0b10
CLASS_OTHER  = 0b11

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
    actual_is_branch   = int(dut.w_is_branch.value)
    actual_is_link     = int(dut.w_is_link.value)
    actual_offset      = int(dut.w_offset.value)

    assert actual_instr_class == CLASS_BRANCH, (
        f"[{name}] instr_class got 0b{actual_instr_class:02b}, "
        f"expected 0b{CLASS_BRANCH:02b}"
    )

    assert actual_is_branch == 1, (
        f"[{name}] is_branch got {actual_is_branch}, expected 1"
    )

    assert actual_is_link == is_link, (
        f"[{name}] is_link got {actual_is_link}, expected {is_link}"
    )

    assert actual_offset == (offset & 0xFFFFFF), (
        f"[{name}] offset got 0x{actual_offset:06x}, "
        f"expected 0x{(offset & 0xFFFFFF):06x}"
    )

@cocotb.test()
async def test_decode_data_processing_instructions(dut):
    """
    Generic decode test for supported ARM data-processing instructions.
    """

    test_vectors = [
        ("AND", ARM_AND),
        ("SUB", ARM_SUB),
        ("ADD", ARM_ADD),
        ("CMN", ARM_CMN),
        ("TEQ", ARM_TEQ),
        ("MVN", ARM_MVN),
    ]

    for name, opcode in test_vectors:
        await drive_and_check_data_proc(
            dut,
            name=name,
            opcode=opcode,
            uses_imm=1,
            set_cond=0,
            rn=1,
            rd=0,
            operand2=1,
        )


@cocotb.test()
async def test_decode_load_store_instructions(dut):
    """
    Generic decode test for ARM LDR/STR single data transfer instructions.
    """

    test_vectors = [
        {
            "name": "LDR R0, [R1, #4]",
            "is_load": 1,
            "rn": 1,
            "rd": 0,
            "offset": 4,
            "pre_index": 1,
            "offset_dir": 1,
            "is_byte": 0,
            "writeback": 0,
        },
        {
            "name": "STR R2, [R3, #8]",
            "is_load": 0,
            "rn": 3,
            "rd": 2,
            "offset": 8,
            "pre_index": 1,
            "offset_dir": 1,
            "is_byte": 0,
            "writeback": 0,
        },
        {
            "name": "LDRB R4, [R5, #12]",
            "is_load": 1,
            "rn": 5,
            "rd": 4,
            "offset": 12,
            "pre_index": 1,
            "offset_dir": 1,
            "is_byte": 1,
            "writeback": 0,
        },
        {
            "name": "STR R6, [R7, #-16]",
            "is_load": 0,
            "rn": 7,
            "rd": 6,
            "offset": 16,
            "pre_index": 1,
            "offset_dir": 0,
            "is_byte": 0,
            "writeback": 0,
        },
        {
            "name": "LDR R8, [R9, #20]!",
            "is_load": 1,
            "rn": 9,
            "rd": 8,
            "offset": 20,
            "pre_index": 1,
            "offset_dir": 1,
            "is_byte": 0,
            "writeback": 1,
        },
    ]

    for tv in test_vectors:
        await drive_and_check_mem_instr(dut, **tv)


@cocotb.test()
async def test_decode_branch_instructions(dut):
    """
    Test decoding of B and BL instructions.
    """
    test_vectors = [
        {
            "name": "B forward",
            "is_link": 0,
            "offset": 0x000004,
        },
        {
            "name": "BL forward",
            "is_link": 1,
            "offset": 0x000010,
        },
        {
            "name": "B max positive raw offset",
            "is_link": 0,
            "offset": 0x7FFFFF,
        },
        {
            "name": "BL negative raw offset",
            "is_link": 1,
            "offset": 0xFFFFFC,
        },
    ]

    for tv in test_vectors:
        await drive_and_check_branch_instr(dut, **tv)

def test_if_unit_runner():
    
    sim = os.getenv("SIM", "questa")
    proj_path = Path(__file__).resolve().parent.parent

    sources = [ 
        proj_path / "hdl"  /"include" / "cpu_pkg.sv",
        proj_path / "hdl" / "decode_stage" / "decoder.sv",
        ]

    runner = get_runner(sim)

    parameters = {"INSTR_WIDTH": 32}

    runner.build(
        sources=sources,
        hdl_toplevel="decoder",
        parameters=parameters,
        build_dir="sim_build/decoder_test",
        always=True,
        clean=True
        
    )

    runner.test(
        hdl_toplevel="decoder",
        test_module="test_decoder",
        parameters=parameters,
        build_dir="sim_build/decoder_test",
        
    )

if __name__ == "__main__":
    test_if_unit_runner()