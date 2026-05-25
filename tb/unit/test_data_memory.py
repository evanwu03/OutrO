

from pathlib import Path
import os

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb_tools.runner import get_runner

from ..common.clock_reset import start_clock
from ..common.clock_reset import reset_dut


def setup_dut(dut): 
    dut.i_mem_write_en.value = 0
    dut.i_addr.value = 0
    dut.i_wdata.value = 0


@cocotb.test()
async def test_basic_write_read(dut):

    clk = dut.i_clk
    rst = dut.i_nrst


    start_clock(clk, period_ns=10)

    await reset_dut(clk, rst, active_low=True, cycles=2)
    
    # Write 0xDEADBEEF to address 0x0
    dut.i_mem_write_en.value = 1
    dut.i_addr.value = 0x0
    dut.i_wdata.value = 0xDEADBEEF

    await RisingEdge(dut.i_clk)

    # Disable write
    dut.i_mem_write_en.value = 0

    # Read back
    dut.i_addr.value = 0x0

    await Timer(1, unit="ns")

    assert dut.o_rdata.value.to_unsigned() == 0xDEADBEEF


@cocotb.test()
async def test_multiple_addresses(dut):

    clk = dut.i_clk
    rst = dut.i_nrst


    start_clock(clk, period_ns=10)

    await reset_dut(clk, rst, active_low=True, cycles=2)

    # Write address (0x0) <- 0x11111111
    dut.i_mem_write_en.value = 1
    dut.i_addr.value = 0x0
    dut.i_wdata.value = 0x11111111

    await RisingEdge(dut.i_clk)

    # Write address (0x4) <- 0x22222222
    dut.i_addr.value = 0x4
    dut.i_wdata.value = 0x22222222

    await RisingEdge(dut.i_clk)

    dut.i_mem_write_en.value = 0

    # Read address 0x0
    dut.i_addr.value = 0x0
    await Timer(1, unit="ns")

    assert dut.o_rdata.value.to_unsigned() == 0x11111111

    # Read address 0x4
    dut.i_addr.value = 0x4
    await Timer(1, unit="ns")

    assert dut.o_rdata.value.to_unsigned() == 0x22222222


@cocotb.test()
async def test_unaligned_address(dut):

    clk = dut.i_clk
    rst = dut.i_nrst


    start_clock(clk, period_ns=10)

    await reset_dut(clk, rst, active_low=True, cycles=2)

    # Attempt unaligned write
    dut.i_mem_write_en.value = 1
    dut.i_addr.value = 0x2
    dut.i_wdata.value = 0x22222222

    await RisingEdge(dut.i_clk)

    dut.i_mem_write_en.value = 0

    # Read same unaligned address
    dut.i_addr.value = 0x2

    await Timer(1, unit="ns")

    assert dut.o_rdata.value.to_unsigned() == 0

    # Verify aligned word 0 was not modified on accident
    dut.i_addr.value = 0x0

    await Timer(1, unit="ns")

    assert dut.o_rdata.value.to_unsigned() == 0



def test_instr_fifo_runner():
    
    sim = os.getenv("SIM", "questa")
    proj_path = Path(__file__).resolve().parent.parent.parent

    sources = [proj_path / "hdl" / "memory" / "data_memory.sv"]

    runner = get_runner(sim)

    parameters = {}

    runner.build(
        sources=sources,
        hdl_toplevel="data_memory",
        parameters=parameters,
        build_dir="sim_build/data_mem_test",
        always=True,
        clean=True
        
    )

    runner.test(
        hdl_toplevel="data_memory",
        test_module="tb.unit.test_data_memory",
        parameters=parameters,
        build_dir="sim_build/data_mem_test", 
    )


if __name__ == "__main__":
    test_instr_fifo_runner()