import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb_tools.runner import get_runner
import os
from pathlib import Path

from ..common.clock_reset import start_clock, reset_dut
from ..common.config import * 
from ..drivers.rat_driver import lookup, rename_dest

async def setup_dut(dut): 
    dut.i_src0_arch.value = 0
    dut.i_src1_arch.value = 0

    dut.i_writes_rd.value = 0
    dut.i_dest_arch.value = 0
    dut.i_dest_tag.value = 0

    dut.i_commit_valid.value = 0
    dut.i_commit_arch.value = 0
    dut.i_commit_tag.value = 0

@cocotb.test()
async def test_rat_reset_clears_all_entries(dut):
    """After reset, all RAT entries should be invalid."""
    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)
    await setup_dut(dut)
    await reset_dut(clk, rst, active_low=True, cycles=2)
 
    for reg in range(ARCH_REG_COUNT):
        result = await lookup(dut, reg, reg)

        assert result["src0_valid"] == 0, f"RAT[{reg}] src0 valid should be 0 after reset"
        assert result["src1_valid"] == 0, f"RAT[{reg}] src1 valid should be 0 after reset"


@cocotb.test()
async def test_rat_single_rename_lookup(dut):
    """Renaming one architectural register should make that RAT entry valid."""
    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)
    await setup_dut(dut)
    await reset_dut(clk, rst, active_low=True, cycles=2)
 
    # Rename R3 -> ROB5
    await rename_dest(dut, dest_arch=3, dest_tag=5)

    result = await lookup(dut, src0_arch=3, src1_arch=4)

    assert result["src0_valid"] == 1
    assert result["src0_tag"] == 5

    assert result["src1_valid"] == 0


@cocotb.test()
async def test_rat_two_source_lookup(dut):
    """Both source ports should independently read their RAT entries."""
    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)
    await setup_dut(dut)
    await reset_dut(clk, rst, active_low=True, cycles=2)
 

    # Rename R1 -> ROB2
    await rename_dest(dut, dest_arch=1, dest_tag=2)

    # Rename R7 -> ROB6
    await rename_dest(dut, dest_arch=7, dest_tag=6)

    result = await lookup(dut, src0_arch=1, src1_arch=7)

    assert result["src0_valid"] == 1
    assert result["src0_tag"] == 2

    assert result["src1_valid"] == 1
    assert result["src1_tag"] == 6


@cocotb.test()
async def test_rat_overwrite_same_arch_register(dut):
    """A newer rename to the same architectural register should overwrite the older tag."""
    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)
    await setup_dut(dut)
    await reset_dut(clk, rst, active_low=True, cycles=2)
 
    # Older instruction writes R2 -> ROB3
    await rename_dest(dut, dest_arch=2, dest_tag=3)

    result = await lookup(dut, src0_arch=2, src1_arch=0)
    assert result["src0_valid"] == 1
    assert result["src0_tag"] == 3

    # Newer instruction writes R2 -> ROB4
    await rename_dest(dut, dest_arch=2, dest_tag=4)

    result = await lookup(dut, src0_arch=2, src1_arch=0)
    assert result["src0_valid"] == 1
    assert result["src0_tag"] == 4


@cocotb.test()
async def test_rat_max_rob_tag_lookup(dut):
    """ROB tag 7 should work as the maximum valid tag for an 8-entry ROB."""
    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)
    await setup_dut(dut)
    await reset_dut(clk, rst, active_low=True, cycles=2)
 

    # Rename R8 -> ROB7
    await rename_dest(dut, dest_arch=8, dest_tag=ROB_TAG_MAX)

    result = await lookup(dut, src0_arch=8, src1_arch=0)

    assert result["src0_valid"] == 1
    assert result["src0_tag"] == ROB_TAG_MAX


@cocotb.test()
async def test_rat_no_write_when_writes_rd_low(dut):
    """When i_writes_rd is low, the RAT should not allocate a new alias."""
    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)
    await setup_dut(dut)
    await reset_dut(clk, rst, active_low=True, cycles=2)
 

    dut.i_writes_rd.value = 0
    dut.i_dest_arch.value = 5
    dut.i_dest_tag.value = 7

    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    result = await lookup(dut, src0_arch=5, src1_arch=0)

    assert result["src0_valid"] == 0


@cocotb.test()
async def test_rat_does_not_rename_pc(dut):
    """R15 is PC, so the RAT should not rename it."""
    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)
    await setup_dut(dut)
    await reset_dut(clk, rst, active_low=True, cycles=2)
 

    # Try to rename PC/R15 -> ROB6
    await rename_dest(dut, dest_arch=ARCH_PC, dest_tag=6)

    result = await lookup(dut, src0_arch=ARCH_PC, src1_arch=0)

    assert result["src0_valid"] == 0



@cocotb.test()
async def test_rat_same_cycle_commit_and_rename_same_arch_rename_wins(dut):
    """
    If an older mapping commits and a newer instruction renames the same arch register
    in the same cycle, the final RAT entry should point to the new ROB tag.
    """
    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)
    await setup_dut(dut)
    await reset_dut(clk, rst, active_low=True, cycles=2)
 

    # Existing mapping: R1 -> ROB2
    await rename_dest(dut, dest_arch=1, dest_tag=2)

    # Same cycle:
    # commit R1/ROB2, rename R1/ROB3
    dut.i_commit_valid.value = 1
    dut.i_commit_arch.value = 1
    dut.i_commit_tag.value = 2

    dut.i_writes_rd.value = 1
    dut.i_dest_arch.value = 1
    dut.i_dest_tag.value = 3

    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    dut.i_commit_valid.value = 0
    dut.i_commit_arch.value = 0
    dut.i_commit_tag.value = 0

    dut.i_writes_rd.value = 0
    dut.i_dest_arch.value = 0
    dut.i_dest_tag.value = 0

    result = await lookup(dut, src0_arch=1, src1_arch=0)

    assert result["src0_valid"] == 1
    assert result["src0_tag"] == 3


def test_if_unit_runner():
    
    sim = os.getenv("SIM", "questa")
    proj_path = Path(__file__).resolve().parent.parent.parent

    sources = [proj_path / "hdl"  /"include" / "cpu_pkg.sv",
               proj_path / "hdl" / "dispatch" / "rat.sv"]

    runner = get_runner(sim)

    parameters = {}


    runner.build(
        sources=sources,
        hdl_toplevel="rat",
        parameters=parameters,
        build_dir="sim_build/rat_test",
        always=True,
        clean=True
        
    )

    runner.test(
        hdl_toplevel="rat",
        test_module="tb.unit.test_rat",
        parameters=parameters,
        build_dir="sim_build/rat_test",
        
    )

if __name__ == "__main__":
    test_if_unit_runner()