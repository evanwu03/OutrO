
from cocotb.triggers import RisingEdge
from cocotb.triggers import Timer

from ..common.config import DATA_WIDTH

def mask_data(x):
    return x & ((1 << DATA_WIDTH) - 1)

async def push(dut, wr0, wr1, instr0=0, instr1=0):
    dut.wr_en0.value = int(wr0)
    dut.wr_en1.value = int(wr1)
    dut.rd_en0.value = 0
    dut.rd_en1.value = 0

    dut.i_push_instr0.value = mask_data(instr0)
    dut.i_push_instr1.value = mask_data(instr1)

    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    dut.wr_en0.value = 0
    dut.wr_en1.value = 0

async def push_values(dut, values):
    """
    Push a list of instruction values into the FIFO.
    Uses dual-push when possible.
    """
    idx = 0

    while idx < len(values):
        remaining = len(values) - idx

        if remaining >= 2:
            await push(dut, 1, 1, values[idx], values[idx + 1])
            idx += 2
        else:
            await push(dut, 1, 0, values[idx], 0)
            idx += 1


async def pop_request(dut, rd0=True, rd1=True):
    """
    Samples FIFO output before the clock edge that performs the pop.
    Then advances one cycle.
    """
    dut.wr_en0.value = 0
    dut.wr_en1.value = 0
    dut.rd_en0.value = int(rd0)
    dut.rd_en1.value = int(rd1)

    await Timer(1, unit="ns")

    valid0 = int(dut.o_pop_valid0.value)
    valid1 = int(dut.o_pop_valid1.value)

    instr0 = int(dut.o_pop_instr0.value) if valid0 else None
    instr1 = int(dut.o_pop_instr1.value) if valid1 else None
    
    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    dut.rd_en0.value = 0
    dut.rd_en1.value = 0

    return valid0, valid1, instr0, instr1


async def fill_fifo_with_n(dut, n):
    """
    Fill FIFO with instruction values 0, 1, 2, ...
    """
    value = 0

    while value < n:
        remaining = n - value

        if remaining >= 2:
            await push(dut, 1, 1, value, value + 1)
            value += 2
        else:
            await push(dut, 1, 0, value, 0)
            value += 1


async def pop_n_and_check(dut, expected_values):
    idx = 0

    while idx < len(expected_values):
        remaining = len(expected_values) - idx

        if remaining >= 2:
            valid0, valid1, instr0, instr1 = await pop_request(dut, True, True)

            assert valid0 == 1
            assert valid1 == 1
            assert instr0 == expected_values[idx]
            assert instr1 == expected_values[idx + 1]

            idx += 2

        else:
            valid0, valid1, instr0, instr1 = await pop_request(dut, True, True)

            assert valid0 == 1
            assert valid1 == 0
            assert instr0 == expected_values[idx]

            idx += 1


