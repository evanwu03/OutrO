

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

# These values must match cpu_pkg.sv
CLASS_ALU    = 0
CLASS_MEM    = 1
CLASS_BRANCH = 2
CLASS_OTHER  = 3

ARM_AND = 0b0000
ARM_SUB = 0b0010
ARM_ADD = 0b0100
ARM_CMN = 0b1011
ARM_TEQ = 0b1001
ARM_MVN = 0b1111


RS_NOP         = 0
RS_AND         = 1
RS_SUB         = 2
RS_ADD         = 3
RS_CMN         = 4
RS_TEQ         = 5
RS_MVN         = 6
RS_LOAD        = 7
RS_STORE       = 8
RS_BRANCH      = 9
RS_BRANCH_LINK = 10

ROB_NOP    = 0b00
ROB_STORE  = 0b01
ROB_BRANCH = 0b10
ROB_REG    = 0b11


DECODED_WIDTH = 76

VALID_BIT = 75

COND_HI = 74
COND_LO = 71

INSTR_CLASS_HI = 70
INSTR_CLASS_LO = 69

RN_HI = 68
RN_LO = 65

RM_HI = 64
RM_LO = 61

RD_HI = 60
RD_LO = 57

ALU_OPCODE_HI = 56
ALU_OPCODE_LO = 53

SET_COND_BIT = 52
USES_IMM_BIT = 51

OP2_HI = 50
OP2_LO = 39

OFFSET_HI = 38
OFFSET_LO = 7

PRE_INDEX_BIT = 6
OFFSET_DIR_BIT = 5
IS_BYTE_BIT = 4
WRITE_BACK_BIT = 3
IS_LOAD_BIT = 2

IS_BRANCH_BIT = 1
IS_LINK_BIT = 0


# rob_entry_t packed layout
# typedef struct packed {
#     rob_instr_e instr_type;      // 2
#     arch_reg_t dest_arch_reg;    // 4
#     logic [31:0] value;          // 32
#     logic ready;                 // 1
# } rob_entry_t;

ROB_ENTRY_WIDTH = 39

ROB_INSTR_TYPE_HI = 38
ROB_INSTR_TYPE_LO = 37

ROB_DEST_ARCH_HI = 36
ROB_DEST_ARCH_LO = 33

ROB_VALUE_HI = 32
ROB_VALUE_LO = 1

ROB_READY_BIT = 0


# rs_entry_t packed layout
# typedef struct packed {
#     logic busy;                 // 1
#     rs_op_e op;                 // 4
#     logic src0_ready;           // 1
#     logic [31:0] src0_value;    // 32
#     rob_tag_t src0_tag;         // 3
#     logic src1_ready;           // 1
#     logic [31:0] src1_value;    // 32
#     rob_tag_t src1_tag;         // 3
#     rob_tag_t rob_tag;          // 3
#     logic [31:0] address;       // 32
# } rs_entry_t;

RS_ENTRY_WIDTH = 112

RS_BUSY_BIT = RS_ENTRY_WIDTH - 1          # 111

RS_OP_HI = 110
RS_OP_LO = 107

RS_SRC0_READY_BIT = 106

RS_SRC0_VALUE_HI = 105
RS_SRC0_VALUE_LO = 74

RS_SRC0_TAG_HI = 73
RS_SRC0_TAG_LO = 71

RS_SRC1_READY_BIT = 70

RS_SRC1_VALUE_HI = 69
RS_SRC1_VALUE_LO = 38

RS_SRC1_TAG_HI = 37
RS_SRC1_TAG_LO = 35

RS_ROB_TAG_HI = 34
RS_ROB_TAG_LO = 32

RS_ADDRESS_HI = 31
RS_ADDRESS_LO = 0


def get_packed_field(handle, start, stop=None):
    full_value = handle.value
    if stop is None:
        return full_value[start]
    else:
        return full_value[start:stop]


def set_packed_field(handle, start, stop=None, *, value):
    full_value = handle.value
    if stop is None:
        full_value[start] = value
    else:
        full_value[start:stop] = value
    handle.value = full_value


def clear_decoded(dut):
    dut.i_decoded.value = 0



def pack_decoded(
    *,
    valid=0,
    cond=0,
    instr_class=0,
    rn=0,
    rm=0,
    rd=0,
    alu_opcode=0,
    set_cond=0,
    uses_imm=0,
    op2=0,
    offset=0,
    pre_index=0,
    offset_dir=0,
    is_byte=0,
    write_back=0,
    is_load=0,
    is_branch=0,
    is_link=0,
):
    fields = [
        (valid,       1),
        (cond,        4),
        (instr_class, 2),
        (rn,          4),
        (rm,          4),
        (rd,          4),
        (alu_opcode,  4),
        (set_cond,    1),
        (uses_imm,    1),
        (op2,         12),
        (offset,      32),
        (pre_index,   1),
        (offset_dir,  1),
        (is_byte,     1),
        (write_back,  1),
        (is_load,     1),
        (is_branch,   1),
        (is_link,     1),
    ]

    value = 0
    for field_value, width in fields:
        value = (value << width) | (int(field_value) & ((1 << width) - 1))

    return value

def set_decoded(dut, **kwargs):
    dut.i_decoded.value = pack_decoded(**kwargs)


def set_defaults(dut):
    dut.i_rs_ready.value = 1
    dut.i_rob_ready.value = 1
    dut.i_rob_tag.value = 5

    dut.i_src0_reg_value.value = 0x11111111
    dut.i_src1_reg_value.value = 0x22222222

    dut.i_src0_rat_valid.value = 0
    dut.i_src0_rat_tag.value = 0
    dut.i_src1_rat_valid.value = 0
    dut.i_src1_rat_tag.value = 0

    set_decoded(dut, valid=0)




# =========================
# Tests
# =========================

@cocotb.test()
async def test_decoded_valid_bit_sanity(dut):
    set_defaults(dut)

    dut.i_rs_ready.value = 1
    dut.i_rob_ready.value = 1

    dut.i_decoded.value = pack_decoded(
        valid=1,
        instr_class=CLASS_ALU,
        alu_opcode=ARM_ADD,
        rn=1,
        rm=2,
        rd=3,
        uses_imm=0,
    )

    await Timer(1, unit="ns")

    dut._log.info(f"i_decoded raw = 0x{int(dut.i_decoded.value):x}")
    assert int(dut.i_decoded.value) != 0


@cocotb.test()
async def test_no_dispatch_when_rob_not_ready(dut):
    set_defaults(dut)

    set_decoded(
        dut,
        valid=1,
        instr_class=CLASS_ALU,
        alu_opcode=ARM_ADD,
        rn=1,
        rm=2,
        rd=3,
        uses_imm=0,
    )

    dut.i_rob_ready.value = 0
    dut.i_rs_ready.value = 1

    await Timer(1, unit="ns")

    assert get_packed_field(dut.o_rs_entry, RS_BUSY_BIT) == 0
    assert int(dut.o_writes_rd.value) == 0
    assert int(dut.o_dest_tag.value) == 0
    assert int(dut.o_dest_arch.value) == 0


@cocotb.test()
async def test_no_dispatch_when_rs_not_ready(dut):
    set_defaults(dut)

    set_decoded(
        dut,
        valid=1,
        instr_class=CLASS_ALU,
        alu_opcode=ARM_ADD,
        rn=1,
        rm=2,
        rd=3,
        uses_imm=0,
    )

    dut.i_rob_ready.value = 1
    dut.i_rs_ready.value = 0

    await Timer(1, unit="ns")

    assert get_packed_field(dut.o_rs_entry, RS_BUSY_BIT) == 0
    assert int(dut.o_writes_rd.value) == 0
    assert int(dut.o_dest_tag.value) == 0
    assert int(dut.o_dest_arch.value) == 0



@cocotb.test()
async def test_add_reg_reg_no_rat_dependencies(dut):
    set_defaults(dut)

    RN = 1
    RM = 2
    RD = 3
    ROB_TAG = 6
    SRC0_VALUE = 0xAAAA0001
    SRC1_VALUE = 0xBBBB0002

    # ADD R3, R1, R2
    set_decoded(
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

    # No RAT dependencies.
    dut.i_src0_rat_valid.value = 0
    dut.i_src1_rat_valid.value = 0

    # Values from architectural register file.
    dut.i_src0_reg_value.value = SRC0_VALUE
    dut.i_src1_reg_value.value = SRC1_VALUE

    await Timer(1, unit="ns")

    # RAT/ARF lookup addresses
    assert int(dut.o_src0_arch.value) == RN
    assert int(dut.o_src1_arch.value) == RM

    # RS entry
    assert get_packed_field(dut.o_rs_entry, RS_BUSY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_OP_HI, RS_OP_LO) == RS_ADD
    assert get_packed_field(dut.o_rs_entry, RS_ROB_TAG_HI, RS_ROB_TAG_LO) == ROB_TAG

    # src0 should be ready with ARF value
    assert get_packed_field(dut.o_rs_entry, RS_SRC0_READY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_SRC0_VALUE_HI, RS_SRC0_VALUE_LO) == SRC0_VALUE

    # src1 should be ready with ARF value
    assert get_packed_field(dut.o_rs_entry, RS_SRC1_READY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_SRC1_VALUE_HI, RS_SRC1_VALUE_LO) == SRC1_VALUE

    # Since RAT valid was 0, dependency tags are unused/default.
    assert get_packed_field(dut.o_rs_entry, RS_SRC0_TAG_HI, RS_SRC0_TAG_LO) == 0
    assert get_packed_field(dut.o_rs_entry, RS_SRC1_TAG_HI, RS_SRC1_TAG_LO) == 0

    # ROB entry
    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_REG

    # RAT rename/update output
    assert int(dut.o_writes_rd.value) == 1
    assert int(dut.o_dest_arch.value) == RD
    assert int(dut.o_dest_tag.value) == ROB_TAG



@cocotb.test()
async def test_add_reg_reg_src0_waits_on_rat(dut):
    set_defaults(dut)

    RN = 1
    RM = 2
    RD = 3

    ROB_TAG = 6
    SRC0_RAT_TAG = 4
    SRC1_VALUE = 0xBBBB0002

    # ADD R3, R1, R2
    set_decoded(
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
    assert get_packed_field(dut.o_rs_entry, RS_BUSY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_OP_HI, RS_OP_LO) == RS_ADD
    assert get_packed_field(dut.o_rs_entry, RS_ROB_TAG_HI, RS_ROB_TAG_LO) == ROB_TAG

    # src0 should wait on RAT tag
    assert get_packed_field(dut.o_rs_entry, RS_SRC0_READY_BIT) == 0
    assert get_packed_field(dut.o_rs_entry, RS_SRC0_TAG_HI, RS_SRC0_TAG_LO) == SRC0_RAT_TAG

    # src1 should be ready with ARF/regfile value
    assert get_packed_field(dut.o_rs_entry, RS_SRC1_READY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_SRC1_VALUE_HI, RS_SRC1_VALUE_LO) == SRC1_VALUE

    # ROB entry
    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_REG

    # RAT rename/update output for destination Rd
    assert int(dut.o_writes_rd.value) == 1
    assert int(dut.o_dest_arch.value) == RD
    assert int(dut.o_dest_tag.value) == ROB_TAG



@cocotb.test()
async def test_add_immediate_uses_offset_as_src1_value(dut):
    set_defaults(dut)

    RN = 1
    RD = 3
    ROB_TAG = 6
    SRC0_VALUE = 0xAAAA0001
    IMM_VALUE = 0x44
    IGNORED_RAT_TAG = 4

    # ADD R3, R1, #0x44
    set_decoded(
        dut,
        valid=1,
        instr_class=CLASS_ALU,
        alu_opcode=ARM_ADD,
        rn=RN,
        rm=2,
        rd=RD,
        uses_imm=1,
        offset=IMM_VALUE,
    )

    dut.i_rob_tag.value = ROB_TAG

    dut.i_src0_rat_valid.value = 0
    dut.i_src0_reg_value.value = SRC0_VALUE

    # src1 RAT should be ignored because uses_imm = 1
    dut.i_src1_rat_valid.value = 1
    dut.i_src1_rat_tag.value = IGNORED_RAT_TAG
    dut.i_src1_reg_value.value = 0xBBBB0002

    await Timer(1, unit="ns")

    assert int(dut.o_src0_arch.value) == RN
    assert int(dut.o_dest_arch.value) == RD

    assert get_packed_field(dut.o_rs_entry, RS_BUSY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_OP_HI, RS_OP_LO) == RS_ADD
    assert get_packed_field(dut.o_rs_entry, RS_ROB_TAG_HI, RS_ROB_TAG_LO) == ROB_TAG

    # src0 comes from regfile
    assert get_packed_field(dut.o_rs_entry, RS_SRC0_READY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_SRC0_VALUE_HI, RS_SRC0_VALUE_LO) == SRC0_VALUE

    # src1 comes from immediate offset, not RAT
    assert get_packed_field(dut.o_rs_entry, RS_SRC1_READY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_SRC1_VALUE_HI, RS_SRC1_VALUE_LO) == IMM_VALUE

    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_REG

    assert int(dut.o_writes_rd.value) == 1
    assert int(dut.o_dest_tag.value) == ROB_TAG


@cocotb.test()
async def test_load_dispatch(dut):
    set_defaults(dut)

    RN = 1
    RD = 3
    ROB_TAG = 5
    BASE_VALUE = 0x1000

    # LDR R3, [R1, ...]
    set_decoded(
        dut,
        valid=1,
        instr_class=CLASS_MEM,
        rn=RN,
        rd=RD,
        is_load=1,
        uses_imm=0,
    )

    dut.i_rob_tag.value = ROB_TAG
    dut.i_src0_rat_valid.value = 0
    dut.i_src0_reg_value.value = BASE_VALUE

    await Timer(1, unit="ns")

    assert int(dut.o_src0_arch.value) == RN

    assert get_packed_field(dut.o_rs_entry, RS_BUSY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_OP_HI, RS_OP_LO) == RS_LOAD
    assert get_packed_field(dut.o_rs_entry, RS_ROB_TAG_HI, RS_ROB_TAG_LO) == ROB_TAG

    assert get_packed_field(dut.o_rs_entry, RS_SRC0_READY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_SRC0_VALUE_HI, RS_SRC0_VALUE_LO) == BASE_VALUE

    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_REG

    assert int(dut.o_writes_rd.value) == 1
    assert int(dut.o_dest_arch.value) == RD
    assert int(dut.o_dest_tag.value) == ROB_TAG


@cocotb.test()
async def test_store_dispatch_does_not_rename(dut):
    set_defaults(dut)

    RN = 1
    RM = 2
    RD = 3
    ROB_TAG = 5
    BASE_VALUE = 0x1000
    OFFSET_VALUE = 0x20

    # STR R3, [R1 +/- R2]
    set_decoded(
        dut,
        valid=1,
        instr_class=CLASS_MEM,
        rn=RN,
        rm=RM,
        rd=RD,
        is_load=0,
        uses_imm=1,
        offset=OFFSET_VALUE,
    )

    dut.i_rob_tag.value = ROB_TAG
    dut.i_src0_rat_valid.value = 0
    dut.i_src0_reg_value.value = BASE_VALUE

    await Timer(1, unit="ns")

    assert int(dut.o_src0_arch.value) == RN

    assert get_packed_field(dut.o_rs_entry, RS_BUSY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_OP_HI, RS_OP_LO) == RS_STORE
    assert get_packed_field(dut.o_rs_entry, RS_ROB_TAG_HI, RS_ROB_TAG_LO) == ROB_TAG

    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_STORE

    # Store should occupy RS/ROB, but should not update RAT rename mapping
    assert int(dut.o_writes_rd.value) == 0
    assert int(dut.o_dest_tag.value) == 0


@cocotb.test()
async def test_branch_dispatch(dut):
    set_defaults(dut)

    ROB_TAG = 2
    BRANCH_OFFSET = 0x40

    # B #offset
    set_decoded(
        dut,
        valid=1,
        instr_class=CLASS_BRANCH,
        is_branch=1,
        is_link=0,
        offset=BRANCH_OFFSET,
    )

    dut.i_rob_tag.value = ROB_TAG

    await Timer(1, unit="ns")

    assert get_packed_field(dut.o_rs_entry, RS_BUSY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_OP_HI, RS_OP_LO) == RS_BRANCH
    assert get_packed_field(dut.o_rs_entry, RS_ROB_TAG_HI, RS_ROB_TAG_LO) == ROB_TAG

    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_BRANCH

    #assert get_packed_field(dut.o_rs_entry, RS_SRC1_VALUE_HI, RS_SRC1_VALUE_LO) == BRANCH_OFFSET

    assert int(dut.o_writes_rd.value) == 0
    assert int(dut.o_dest_tag.value) == 0


@cocotb.test()
async def test_branch_link_dispatch(dut):
    set_defaults(dut)

    ROB_TAG = 2
    BRANCH_OFFSET = 0x40

    # BL #offset
    set_decoded(
        dut,
        valid=1,
        instr_class=CLASS_BRANCH,
        is_branch=1,
        is_link=1,
        offset=BRANCH_OFFSET,
    )

    dut.i_rob_tag.value = ROB_TAG

    await Timer(1, unit="ns")

    assert get_packed_field(dut.o_rs_entry, RS_BUSY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_OP_HI, RS_OP_LO) == RS_BRANCH_LINK
    assert get_packed_field(dut.o_rs_entry, RS_ROB_TAG_HI, RS_ROB_TAG_LO) == ROB_TAG

    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_BRANCH

    # Current RTL does not rename link register yet
    assert int(dut.o_writes_rd.value) == 0
    assert int(dut.o_dest_tag.value) == 0



@cocotb.test()
async def test_add_immediate_src0_waits_on_rat(dut):
    set_defaults(dut)

    RN = 1
    RD = 3
    ROB_TAG = 6
    SRC0_RAT_TAG = 4
    IMM_VALUE = 0x44

    # ADD R3, R1, #0x44
    set_decoded(
        dut,
        valid=1,
        instr_class=CLASS_ALU,
        alu_opcode=ARM_ADD,
        rn=RN,
        rm=2,              # Should be ignored because uses_imm = 1
        rd=RD,
        uses_imm=1,
        offset=IMM_VALUE,
    )

    dut.i_rob_tag.value = ROB_TAG

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
    assert get_packed_field(dut.o_rs_entry, RS_BUSY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_OP_HI, RS_OP_LO) == RS_ADD
    assert get_packed_field(dut.o_rs_entry, RS_ROB_TAG_HI, RS_ROB_TAG_LO) == ROB_TAG

    # src0 waits on RAT tag
    assert get_packed_field(dut.o_rs_entry, RS_SRC0_READY_BIT) == 0
    assert get_packed_field(dut.o_rs_entry, RS_SRC0_TAG_HI, RS_SRC0_TAG_LO) == SRC0_RAT_TAG

    # src1 uses immediate, so RAT/regfile should be ignored
    assert get_packed_field(dut.o_rs_entry, RS_SRC1_READY_BIT) == 1
    assert get_packed_field(dut.o_rs_entry, RS_SRC1_VALUE_HI, RS_SRC1_VALUE_LO) == IMM_VALUE

    # ROB entry
    assert get_packed_field(dut.o_rob_entry, ROB_INSTR_TYPE_HI, ROB_INSTR_TYPE_LO) == ROB_REG

    # RAT rename output
    assert int(dut.o_writes_rd.value) == 1
    assert int(dut.o_dest_arch.value) == RD
    assert int(dut.o_dest_tag.value) == ROB_TAG


def test_if_unit_runner():
    
    sim = os.getenv("SIM", "questa")
    proj_path = Path(__file__).resolve().parent.parent

    sources = [proj_path / "hdl"  /"include" / "cpu_pkg.sv",
               proj_path / "hdl" / "dispatch_stage" / "dispatch_unit.sv"]

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
        test_module="test_dispatch",
        parameters=parameters,
        build_dir="sim_build/dispatch_test",
        
    )

if __name__ == "__main__":
    test_if_unit_runner()