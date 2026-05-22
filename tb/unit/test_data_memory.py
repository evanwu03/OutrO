

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    dut.i_nrst.value = 0
    dut.i_mem_write_en.value = 0
    dut.i_addr.value = 0
    dut.i_wdata.value = 0

    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    dut.i_nrst.value = 1
    await RisingEdge(dut.i_clk)


@cocotb.test()
async def test_basic_write_read(dut):

    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())

    await reset_dut(dut)

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

    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())

    await reset_dut(dut)

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

    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())

    await reset_dut(dut)

    # Attempt unaligned write
    dut.i_mem_write_en.value = 1
    dut.i_addr.value = 0x2
    dut.i_wdata.value = 0x22222222

    await RisingEdge(dut.i_clk)

    dut.i_mem_write_en.value = 0

    # Read same unaligned address
    dut.i_addr.value = 0x2

    await Timer(1, unit="ns")

    assert dut.o_rdata.value.integer == 0

    # Verify aligned word 0 was not modified on accident
    dut.i_addr.value = 0x0

    await Timer(1, unit="ns")

    assert dut.o_rdata.value.integer == 0