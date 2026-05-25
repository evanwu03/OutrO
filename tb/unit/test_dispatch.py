

""" Test scenarios: 
 
1. Invalid instruction
   i_decoded.valid = 0
   expect:
      o_rs_entry.busy = 0
      o_writes_rd = 0
      o_dest_tag = 0

2. ROB not ready
   valid = 1, i_rob_ready = 0, i_rs_ready = 1
   expect no dispatch

3. RS not ready
   valid = 1, i_rob_ready = 1, i_rs_ready = 0
   expect no dispatch

4. ADD register-register, no RAT dependencies
   ADD Rd, Rn, Rm
   RAT valid = 0 for both sources
   expect:
      RS op = RS_ADD
      src0_ready = 1, src0_value = regfile src0
      src1_ready = 1, src1_value = regfile src1
      rob_tag = i_rob_tag
      busy = 1
      ROB type = ROB_REG
      o_dest_arch = rd
      o_dest_tag = i_rob_tag
      o_writes_rd = 1

5. ADD register-register, source waits on RAT
   RAT[src0] valid = 1
   expect:
      src0_ready = 0
      src0_tag = RAT tag

6. ADD immediate
   uses_imm = 1
   expect:
      src1_ready = 1
      src1_value = decoded.offset/immediate
      src1 RAT tag ignored

7. LDR
   expect:
      RS op = RS_LOAD
      ROB type = ROB_REG
      writes_rd = 1
      dest_arch = rd

8. STR
   expect:
      RS op = RS_STORE
      ROB type = ROB_STORE
      writes_rd = 0
      busy = 1
      rob_tag = i_rob_tag

9. Branch
   expect:
      RS op = RS_BRANCH or RS_BRANCH_LINK
      ROB type = ROB_BRANCH
      writes_rd = 0

10. ADD immediate with src0 waiting on RAT

Instruction:
    ADD R3, R1, #0x44

Inputs:
    valid = 1
    ROB ready = 1
    RS ready = 1
    RAT[src0] valid = 1, tag = 4
    uses_imm = 1
    i_rob_tag = 6

Expect:
    RS op = RS_ADD
    src0_ready = 0
    src0_tag = 4
    src1_ready = 1
    src1_value = 0x44
    rob_tag = 6
    busy = 1
    ROB type = ROB_REG
    writes_rd = 1
    dest_arch = R3
    dest_tag = 6 """

import os
from pathlib import Path

import cocotb
from cocotb_tools.runner import get_runner
from cocotb.triggers import Timer

from ..common.config import * 
from ..common.util import set_decoded
from ..common.util import get_packed_field
from ..common.util import pack_decoded

from ..drivers.dispatch_check import expect_no_dispatch
from ..drivers.dispatch_check import expect_rs_common
from ..drivers.dispatch_check import expect_src_waits
from ..drivers.dispatch_check import expect_src_ready
from ..drivers.dispatch_check import expect_rename


def setup_dut(dut, rob_ready=1, rs_ready=1, rob_tag=0):
    dut.i_rs_ready.value = rs_ready
    dut.i_rob_ready.value = rob_ready
    dut.i_rob_tag.value = rob_tag

    dut.i_src0_reg_value.value = 0x11111111
    dut.i_src1_reg_value.value = 0x22222222

    dut.i_src0_rat_valid.value = 0
    dut.i_src0_rat_tag.value = 0
    dut.i_src1_rat_valid.value = 0
    dut.i_src1_rat_tag.value = 0

    set_decoded(dut, valid=0)


async def apply_decoded(
    dut,
    rob_ready=1,
    rs_ready=1,
    rob_tag=0,
    valid=1,
    **fields
):
    setup_dut(
        dut,
        rob_ready=rob_ready,
        rs_ready=rs_ready,
        rob_tag=rob_tag,
    )

    set_decoded(
        dut,
        valid=valid,
        **fields,
    )

    await Timer(1, unit="ns")
    
# =========================
# Tests
# =========================

@cocotb.test()
async def test_decoded_valid_bit_sanity(dut):


    await apply_decoded(
        dut, 
        rob_ready=1,
        rs_ready=1,
        rob_tag=0,
        valid=1,
        instr_class=CLASS_ALU,
        alu_opcode=ARM_ADD,
        rn=1,
        rm=2,
        rd=3,
        uses_imm=0,
    )

    dut._log.info(f"i_decoded raw = 0x{int(dut.i_decoded.value):x}")
    assert int(dut.i_decoded.value) != 0


@cocotb.test()
async def test_no_dispatch_when_rob_not_ready(dut):

    await apply_decoded(
        dut=dut,
        rob_ready=0,
        rs_ready=1,
        rob_tag=0,
        valid=1,
        instr_class=CLASS_ALU,
        alu_opcode=ARM_ADD,
        rn=1,
        rm=2,
        rd=3,
        uses_imm=0,
    )


    expect_no_dispatch(dut)


@cocotb.test()
async def test_no_dispatch_when_rs_not_ready(dut):
    
    await apply_decoded(
        dut=dut,
        rob_ready=1,
        rs_ready=0,
        rob_tag=0,
        valid=1,
        instr_class=CLASS_ALU,
        alu_opcode=ARM_ADD,
        rn=1,
        rm=2,
        rd=3,
        uses_imm=0,
    )

    expect_no_dispatch(dut)


@cocotb.test()
async def test_add_reg_reg_no_rat_dependencies(dut):
    RN, RM, RD = 1, 2, 3
    ROB_TAG = 6
    SRC0_VALUE = 0xAAAA0001
    SRC1_VALUE = 0xBBBB0002

    await apply_decoded(
        dut,
        instr_class=CLASS_ALU,
        alu_opcode=ARM_ADD,
        rn=RN,
        rm=RM,
        rd=RD,
        uses_imm=0,
    )

    dut.i_rob_tag.value = ROB_TAG
    dut.i_src0_reg_value.value = SRC0_VALUE
    dut.i_src1_reg_value.value = SRC1_VALUE

    await Timer(1, unit="ns")

    expect_rs_common(dut, RS_ADD, ROB_TAG, busy=0)
    expect_src_ready(dut, 0, SRC0_VALUE)
    expect_src_ready(dut, 1, SRC1_VALUE)

    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_REG
    expect_rename(dut, writes=1, rd=RD, tag=ROB_TAG)



@cocotb.test()
async def test_add_reg_reg_src0_waits_on_rat(dut):

    RN = 1
    RM = 2
    RD = 3

    ROB_TAG = 6
    SRC0_RAT_TAG = 4
    SRC1_VALUE = 0xBBBB0002

    # ADD R3, R1, R2
    await apply_decoded(
        dut,
        valid=1,
        instr_class=CLASS_ALU,
        alu_opcode=ARM_ADD,
        rn=RN,
        rm=RM,
        rd=RD,
        uses_imm=0,
    )

    dut.i_rob_tag.value = ROB_TAG

    # src0 has a pending producer in RAT.
    dut.i_src0_rat_valid.value = 1
    dut.i_src0_rat_tag.value = SRC0_RAT_TAG

    # src1 has no dependency, so it should use regfile value.
    dut.i_src1_rat_valid.value = 0
    dut.i_src1_reg_value.value = SRC1_VALUE

    await Timer(1, unit="ns")

    # RAT/ARF lookup addresses
    assert int(dut.o_src0_arch.value) == RN
    assert int(dut.o_src1_arch.value) == RM

    # RS entry basics
    expect_rs_common(
        dut, 
        op=RS_ADD, 
        rob_tag=ROB_TAG, busy=0
    )

    expect_src_waits(dut, 0, SRC0_RAT_TAG)
    expect_src_ready(dut, 1, SRC1_VALUE)

    # ROB entry
    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_REG
    expect_rename(dut, writes=1, rd=RD, tag=ROB_TAG)


@cocotb.test()
async def test_add_immediate_uses_offset_as_src1_value(dut):

    RN = 1
    RD = 3
    ROB_TAG = 6
    SRC0_VALUE = 0xAAAA0001
    IMM_VALUE = 0x44
    IGNORED_RAT_TAG = 4

    # ADD R3, R1, #0x44
    await apply_decoded(
        dut,
        rob_tag=ROB_TAG,
        valid=1,
        instr_class=CLASS_ALU,
        alu_opcode=ARM_ADD,
        rn=RN,
        rm=2,
        rd=RD,
        uses_imm=1,
        offset=IMM_VALUE,
    )

 
    dut.i_src0_rat_valid.value = 0
    dut.i_src0_reg_value.value = SRC0_VALUE

    # src1 RAT should be ignored because uses_imm = 1
    dut.i_src1_rat_valid.value = 1
    dut.i_src1_rat_tag.value = IGNORED_RAT_TAG
    dut.i_src1_reg_value.value = 0xBBBB0002

    await Timer(1, unit="ns")


    assert int(dut.o_src0_arch.value) == RN
    assert int(dut.o_dest_arch.value) == RD

    assert get_packed_field(dut.o_rs_entry, RS_BUSY_BIT) == 0
    assert get_packed_field(dut.o_rs_entry, RS_OP_HI, RS_OP_LO) == RS_ADD
    assert get_packed_field(dut.o_rs_entry, RS_ROB_TAG_HI, RS_ROB_TAG_LO) == ROB_TAG

    expect_rs_common(
        dut, 
        op=RS_ADD, 
        rob_tag=ROB_TAG, busy=0
    )

    # src0 comes from regfile
    expect_src_ready(dut, 0, SRC0_VALUE)
    

    # src1 comes from immediate offset, not RAT
    expect_src_ready(dut, 1, IMM_VALUE)


    expect_rename(dut, writes=1, rd=RD, tag=ROB_TAG)
    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_REG


@cocotb.test()
async def test_load_dispatch(dut):
    RN = 1
    RD = 3
    ROB_TAG = 5
    BASE_VALUE = 0x1000

    # LDR R3, [R1, ...]
    await apply_decoded(
        dut, 
        rob_tag=ROB_TAG,
        valid=1,
        instr_class=CLASS_MEM,
        rn=RN,
        rd=RD,
        is_load=1,
        uses_imm=0,

    )

    # set up RAT
    dut.i_src0_rat_valid.value = 0
    dut.i_src0_reg_value.value = BASE_VALUE

    await Timer(1, unit="ns")

    assert int(dut.o_src0_arch.value) == RN

    expect_rs_common(
        dut, 
        RS_LOAD,
        ROB_TAG,
        busy=0
    )

    expect_src_ready(dut, 0, BASE_VALUE)

    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_REG
    expect_rename(dut, writes=1, rd=RD, tag=ROB_TAG)


@cocotb.test()
async def test_store_dispatch_does_not_rename(dut):
    RN = 1
    RM = 2
    RD = 3
    ROB_TAG = 5
    BASE_VALUE = 0x1000
    OFFSET_VALUE = 0x20

    # STR R3, [R1 +/- R2]
    """ et_decoded(
        dut,
        valid=1,
        instr_class=CLASS_MEM,
        rn=RN,
        rm=RM,
        rd=RD,
        is_load=0,
        uses_imm=1,
        offset=OFFSET_VALUE,
    """

    await apply_decoded(
        dut,
        rob_tag=ROB_TAG,
        valid=1,
        instr_class=CLASS_MEM,
        rn=RN,
        rm=RM,
        rd=RD,
        is_load=0,
        uses_imm=1,
        offset=OFFSET_VALUE,
    )


    # Setup RAT
    dut.i_src0_rat_valid.value = 0
    dut.i_src0_reg_value.value = BASE_VALUE

    await Timer(1, unit="ns")

    assert int(dut.o_src0_arch.value) == RN

    expect_rs_common(dut, op=RS_STORE, rob_tag=ROB_TAG, busy=0)

    # Store should occupy RS/ROB, but should not update RAT rename mapping
    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_STORE
    expect_rename(dut, writes=0, rd=RN, tag=0)



@cocotb.test()
async def test_branch_dispatch(dut):
    ROB_TAG = 2
    BRANCH_OFFSET = 0x40

    # B [offset]
    await apply_decoded(
        dut,
        rob_tag=ROB_TAG,
        valid=1,
        instr_class=CLASS_BRANCH,
        is_branch=1,
        is_link=0,
        offset=BRANCH_OFFSET,
    )
    
    await Timer(1, unit="ns")

    expect_rs_common(dut, op=RS_BRANCH, rob_tag=ROB_TAG, busy=0)
    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_BRANCH
   
    expect_rename(dut, writes=0, rd=0, tag=0)


@cocotb.test()
async def test_branch_link_dispatch(dut):
    ROB_TAG = 2
    BRANCH_OFFSET = 0x40

    # BL #offset
    await apply_decoded(
        dut,
        rob_tag=ROB_TAG,
        valid=1,
        instr_class=CLASS_BRANCH,
        is_branch=1,
        is_link=1,
        offset=BRANCH_OFFSET,
    )

    await Timer(1, unit="ns")

    expect_rs_common(dut, op=RS_BRANCH_LINK, rob_tag=ROB_TAG, busy=0)
    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_BRANCH
    # Current RTL does not rename link register yet
    expect_rename(dut, writes=0, rd=0, tag=0)


@cocotb.test()
async def test_add_immediate_src0_waits_on_rat(dut):
    RN = 1
    RD = 3
    ROB_TAG = 6
    SRC0_RAT_TAG = 4
    IMM_VALUE = 0x44

    # ADD R3, R1, #0x44
    await apply_decoded(
        dut,
        valid=1,
        rob_tag=ROB_TAG,
        instr_class=CLASS_ALU,
        alu_opcode=ARM_ADD,
        rn=RN,
        rm=2,              # Should be ignored because uses_imm = 1
        rd=RD,
        uses_imm=1,
        offset=IMM_VALUE,
    )


    # src0 depends on an older in-flight producer
    dut.i_src0_rat_valid.value = 1
    dut.i_src0_rat_tag.value = SRC0_RAT_TAG

    # src1 RAT should be ignored because src1 is immediate
    dut.i_src1_rat_valid.value = 1
    dut.i_src1_rat_tag.value = 7
    dut.i_src1_reg_value.value = 0xDEADBEEF

    await Timer(1, unit="ns")

    # Lookup / rename arch outputs
    assert int(dut.o_src0_arch.value) == RN
    assert int(dut.o_dest_arch.value) == RD

    # RS entry basics
    expect_rs_common(dut, op=RS_ADD, rob_tag=ROB_TAG, busy=0)

    # src0 waits on RAT tag
    expect_src_waits(dut, 0, SRC0_RAT_TAG)

    # src1 uses immediate, so RAT/regfile should be ignored
    expect_src_ready(dut, 1, IMM_VALUE)

    # ROB entry
    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_REG

    # RAT rename output
    expect_rename(dut, writes=1, rd=RD, tag=ROB_TAG)


def test_dispatch_unit_runner():
    
    sim = os.getenv("SIM", "questa")
    proj_path = Path(__file__).resolve().parent.parent.parent

    sources = [proj_path / "hdl"  /"include" / "cpu_pkg.sv",
               proj_path / "hdl" / "dispatch" / "dispatch_unit.sv"]

    runner = get_runner(sim)

    parameters = {}


    runner.build(
        sources=sources,
        hdl_toplevel="dispatch_unit",
        parameters=parameters,
        build_dir="sim_build/dispatch_test",
        always=True,
        clean=True
        
    )

    runner.test(
        hdl_toplevel="dispatch_unit",
        test_module="tb.unit.test_dispatch",
        parameters=parameters,
        build_dir="sim_build/dispatch_test",
        
    )

if __name__ == "__main__":
    test_dispatch_unit_runner()