

from ..common.config import * 
from ..common.util import get_packed_field


def expect_no_dispatch(dut):
    assert get_packed_field(dut.o_rs_entry, RS_BUSY_BIT) == 0
    assert int(dut.o_writes_rd.value) == 0
    assert int(dut.o_dest_tag.value) == 0
    assert int(dut.o_dest_arch.value) == 0

def expect_rs_common(dut, op, rob_tag, busy=1):
    assert get_packed_field(dut.o_rs_entry, RS_BUSY_BIT) == busy
    assert get_packed_field(dut.o_rs_entry, RS_OP_HI, RS_OP_LO) == op
    assert get_packed_field(dut.o_rs_entry, RS_ROB_TAG_HI, RS_ROB_TAG_LO) == rob_tag


def expect_src_ready(dut, src, value):
    prefix = "SRC0" if src == 0 else "SRC1"
    assert get_packed_field(dut.o_rs_entry, globals()[f"RS_{prefix}_READY_BIT"]) == 1
    assert get_packed_field(
        dut.o_rs_entry,
        globals()[f"RS_{prefix}_VALUE_HI"],
        globals()[f"RS_{prefix}_VALUE_LO"],
    ) == value


def expect_rename(dut, writes, rd=0, tag=0):
    assert int(dut.o_writes_rd.value) == writes
    assert int(dut.o_dest_arch.value) == rd
    assert int(dut.o_dest_tag.value) == tag



def expect_src_waits(dut, src, tag):
    if src == 0:
        ready_bit = RS_SRC0_READY_BIT
        tag_hi = RS_SRC0_TAG_HI
        tag_lo = RS_SRC0_TAG_LO
    elif src == 1:
        ready_bit = RS_SRC1_READY_BIT
        tag_hi = RS_SRC1_TAG_HI
        tag_lo = RS_SRC1_TAG_LO
    else:
        raise ValueError(f"Invalid src index: {src}")

    assert get_packed_field(dut.o_rs_entry, ready_bit) == 0
    assert get_packed_field(dut.o_rs_entry, tag_hi, tag_lo) == tag