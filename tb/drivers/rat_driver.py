
from cocotb.triggers import RisingEdge, Timer
from ..common.config import ARCH_REG_COUNT, ROB_DEPTH

async def lookup(dut, src0_arch, src1_arch):
    dut.i_src0_arch.value = src0_arch
    dut.i_src1_arch.value = src1_arch

    await Timer(1, unit="ns")

    return {
        "src0_valid": int(dut.o_src0_rat_valid.value),
        "src0_tag": int(dut.o_src0_rat_tag.value),
        "src1_valid": int(dut.o_src1_rat_valid.value),
        "src1_tag": int(dut.o_src1_rat_tag.value),
    }


async def rename_dest(dut, dest_arch, dest_tag):
    assert 0 <= dest_arch < ARCH_REG_COUNT
    assert 0 <= dest_tag < ROB_DEPTH

    dut.i_writes_rd.value = 1
    dut.i_dest_arch.value = dest_arch
    dut.i_dest_tag.value = dest_tag

    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    dut.i_writes_rd.value = 0
    dut.i_dest_arch.value = 0
    dut.i_dest_tag.value = 0

    await Timer(1, unit="ns")


# Not used currently
""" async def commit_dest(dut, commit_arch, commit_tag):
    assert 0 <= commit_arch < ARCH_REG_COUNT
    assert 0 <= commit_tag < ROB_DEPTH

    dut.i_commit_valid.value = 1
    dut.i_commit_arch.value = commit_arch
    dut.i_commit_tag.value = commit_tag

    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    dut.i_commit_valid.value = 0
    dut.i_commit_writes_rd.value = 0
    dut.i_commit_arch.value = 0
    dut.i_commit_tag.value = 0

    await Timer(1, unit="ns")
 """
