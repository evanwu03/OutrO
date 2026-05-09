

# test_instruction_fifo.py

import os
from pathlib import Path
import logging

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_tools.runner import get_runner
from cocotb.triggers import Timer


DEPTH = 16
DATA_WIDTH = 36


def mask_data(x):
    return x & ((1 << DATA_WIDTH) - 1)


async def reset_dut(dut):
    dut.i_nrst.value = 0

    dut.wr_en0.value = 0
    dut.wr_en1.value = 0
    dut.rd_en0.value = 0
    dut.rd_en1.value = 0

    dut.i_push_instr0.value = 0
    dut.i_push_instr1.value = 0

    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    dut.i_nrst.value = 1
    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")


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


@cocotb.test()
async def test_full_fifo_attempt_push_two(dut):
    """
    Case:
    - FIFO is full
    - attempt to push two instructions
    - both should be rejected
    """
    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    await fill_fifo_with_n(dut, DEPTH)

    assert int(dut.o_fifo_full.value) == 1
    assert int(dut.o_fifo_empty.value) == 0

    # Try to push two extra instructions. They should not enter.
    await push(dut, 1, 1, 1000, 1001)

    assert int(dut.o_fifo_full.value) == 1

    # Pop all entries and make sure only original entries are present.
    await pop_n_and_check(dut, list(range(DEPTH)))

    assert int(dut.o_fifo_empty.value) == 1


@cocotb.test()
async def test_empty_fifo_attempt_pop_two(dut):
    """
    Case:
    - FIFO is empty
    - attempt to pop two instructions
    - neither should be valid
    """

    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    assert int(dut.o_fifo_empty.value) == 1
    assert int(dut.o_pop_valid0.value) == 0
    assert int(dut.o_pop_valid1.value) == 0

    valid0, valid1, instr0, instr1 = await pop_request(dut, True, True)

    cocotb.log.info(f"instr0 = {instr0}, instr1 = {instr1}")

    assert valid0 == 0
    assert valid1 == 0
    assert int(dut.o_fifo_empty.value) == 1


@cocotb.test()
async def test_one_free_slot_instr1_not_pushed(dut):
    """
    Case:
    - FIFO has exactly 1 free slot
    - wr_en0 and wr_en1 are both requested
    - only instr0 should be pushed
    - instr1 should be rejected
    """

    INSTR0 = 2000
    INSTR1 = 2001
    WR0 = 1
    WR1 = 1

    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    await fill_fifo_with_n(dut, DEPTH - 1)

    assert int(dut.o_fifo_full.value) == 0
    assert int(dut.o_fifo_empty.value) == 0

    await push(dut, WR0, WR1, INSTR0, INSTR1)

    assert int(dut.o_fifo_full.value) == 1

    expected = list(range(DEPTH - 1)) + [INSTR0]
    await pop_n_and_check(dut, expected)

    assert int(dut.o_fifo_empty.value) == 1


@cocotb.test()
async def test_two_free_slots_push_instr0_and_instr1(dut):
    """
    Case:
    - FIFO has exactly 2 free slots
    - instr0 and instr1 should both be pushed
    """

    INSTR0 = 3000
    INSTR1 = 3001
    WR0 = 1
    WR1 = 1

    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    await fill_fifo_with_n(dut, DEPTH - 2)

    await push(dut, WR0, WR1, INSTR0, INSTR1)

    assert int(dut.o_fifo_full.value) == 1

    expected = list(range(DEPTH - 2)) + [INSTR0, INSTR1]
    await pop_n_and_check(dut, expected)

    assert int(dut.o_fifo_empty.value) == 1


@cocotb.test()
async def test_more_than_two_free_slots_push_both_happy_path(dut):
    """
    Case:
    - FIFO has more than 2 free slots
    - instr0 and instr1 should both be pushed
    """
    INSTR0 = 4000
    INSTR1 = 4001
    WR0 = 1
    WR1 = 1

    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    await push(dut, WR0, WR1, INSTR0, INSTR1)

    assert int(dut.o_fifo_empty.value) == 0
    assert int(dut.o_pop_valid0.value) == 1
    assert int(dut.o_pop_valid1.value) == 1

    valid0, valid1, instr0, instr1 = await pop_request(dut, True, True)

    assert valid0 == 1
    assert valid1 == 1
    assert instr0 == INSTR0
    assert instr1 == INSTR1

    assert int(dut.o_fifo_empty.value) == 1


@cocotb.test()
async def test_count_two_pop_instr0_and_instr1(dut):
    """
    Case:
    - count = 2
    - instr0 and instr1 can both be popped
    """
    INSTR0 = 5000
    INSTR1 = 5001
    WR0 = 1
    WR1 = 1

    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    await push(dut, WR0, WR1, INSTR0, INSTR1)

    assert int(dut.o_pop_valid0.value) == 1
    assert int(dut.o_pop_valid1.value) == 1

    valid0, valid1, instr0, instr1 = await pop_request(dut, True, True)

    assert valid0 == 1
    assert valid1 == 1
    assert instr0 == INSTR0
    assert instr1 == INSTR1

    assert int(dut.o_fifo_empty.value) == 1


@cocotb.test()
async def test_count_one_only_pop_instr0(dut):
    """
    Case:
    - count = 1
    - only instr0 should be valid
    - instr1 should not be valid
    """
    INSTR0 = 6000
    INSTR1 = 0
    WR0 = 1
    WR1 = 0

    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    await push(dut, WR0, WR1, INSTR0, INSTR1)

    assert int(dut.o_pop_valid0.value) == 1
    assert int(dut.o_pop_valid1.value) == 0

    valid0, valid1, instr0, instr1 = await pop_request(dut, True, True)

    assert valid0 == 1
    assert valid1 == 0
    assert instr0 == INSTR0
    assert instr1 is None

    assert int(dut.o_fifo_empty.value) == 1


@cocotb.test()
async def test_count_greater_than_two_pop_both_happy_path(dut):
    """
    Case:
    - count > 2
    - instr0 and instr1 should both pop correctly
    """
    cocotb.start_soon(Clock(dut.i_clk, 10, unit="ns").start())
    await reset_dut(dut)

    await push(dut, 1, 1, 7000, 7001)
    await push(dut, 1, 1, 7002, 7003)

    valid0, valid1, instr0, instr1 = await pop_request(dut, True, True)

    assert valid0 == 1
    assert valid1 == 1
    assert instr0 == 7000
    assert instr1 == 7001

    # The next two should now be at the head.
    assert int(dut.o_pop_valid0.value) == 1
    assert int(dut.o_pop_valid1.value) == 1
    assert int(dut.o_pop_instr0.value) == 7002
    assert int(dut.o_pop_instr1.value) == 7003

    valid0, valid1, instr0, instr1 = await pop_request(dut, True, True)

    assert valid0 == 1
    assert valid1 == 1
    assert instr0 == 7002
    assert instr1 == 7003

    assert int(dut.o_fifo_empty.value) == 1



def test_instr_fifo_runner():
    
    sim = os.getenv("SIM", "questa")
    proj_path = Path(__file__).resolve().parent.parent

    sources = [proj_path / "hdl" / "instruction_fetch_unit" / "instruction_fifo.sv"]

    runner = get_runner(sim)

    runner.build(
        sources=sources,
        hdl_toplevel="instruction_fifo",
        parameters={"DATA_WIDTH": 36, "DEPTH":16},
        build_dir="sim_build/instr_fifo_test",
        always=True,
        clean=True
        
    )

    runner.test(
        hdl_toplevel="instruction_fifo",
        test_module="test_instruction_fifo",
        parameters={"DATA_WIDTH": 36, "DEPTH":16},
        build_dir="sim_build/instr_fifo_test",
        
    )


if __name__ == "__main__":
    test_instr_fifo_runner()
    