

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    dut.i_nrst.value = 0
    dut.i_pc_next.value = 0
    dut.i_write_en_0.value = 0
    dut.i_write_en_1.value = 0
    dut.i_rd_0.value = 0
    dut.i_rd_1.value = 0
    dut.i_commit0_wdata.value = 0
    dut.i_commit1_wdata.value = 0
    dut.i_rs1_0.value = 0
    dut.i_rs2_0.value = 0
    dut.i_rs1_1.value = 0
    dut.i_rs2_1.value = 0

    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    dut.i_nrst.value = 1
    await RisingEdge(dut.i_clk)


@cocotb.test()
async def test_register_file_basic(dut):
    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())

    await reset_dut(dut)

    # Write R1 <- 0xAAAA5555 using port 0
    dut.i_write_en_0.value = 1
    dut.i_rd_0.value = 1
    dut.i_commit0_wdata.value = 0xAAAA5555

    dut.i_write_en_1.value = 0
    dut.i_pc_next.value = 4

    await RisingEdge(dut.i_clk)

    dut.i_write_en_0.value = 0

    # Async read (R1) => 0xAAAA5555
    dut.i_rs1_0.value = 1
    await Timer(1, unit="ns")

    assert dut.o_rs1_0.value.to_unsigned() == 0xAAAA5555

    # Write R2 and R3 simultaneously
    # (R2) <= 0x11111111
    dut.i_write_en_0.value = 1
    dut.i_rd_0.value = 2
    dut.i_commit0_wdata.value = 0x11111111


    # (R3) <= 0x22222222
    dut.i_write_en_1.value = 1
    dut.i_rd_1.value = 3
    dut.i_commit1_wdata.value = 0x22222222


    # (PC) <= 8
    dut.i_pc_next.value = 8

    await RisingEdge(dut.i_clk)

    dut.i_write_en_0.value = 0
    dut.i_write_en_1.value = 0

    dut.i_rs1_0.value = 2
    dut.i_rs2_0.value = 3
    await Timer(1, unit="ns")

    assert dut.o_rs1_0.value.to_unsigned()  == 0x11111111
    assert dut.o_rs2_0.value.to_unsigned()  == 0x22222222

    # Check PC/R15 updated from i_pc_next
    dut.i_rs1_1.value = 15
    await Timer(1, unit="ns")

    assert dut.o_rs1_1.value.to_unsigned()  == 8
    assert dut.o_pc.value.to_unsigned() == 8