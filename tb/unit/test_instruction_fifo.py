

# test_instruction_fifo.py

import os
from pathlib import Path

import cocotb
from cocotb.triggers import RisingEdge
from cocotb_tools.runner import get_runner
from cocotb.triggers import Timer

from ..drivers.instr_fifo_driver import push
from ..drivers.instr_fifo_driver import push_values
from ..drivers.instr_fifo_driver import pop_n_and_check
from ..drivers.instr_fifo_driver import pop_request
from ..drivers.instr_fifo_driver import fill_fifo_with_n


from ..common.clock_reset import start_clock
from ..common.clock_reset import reset_dut

# Globals
from ..common.config import INSTRUCTION_FIFO_DEPTH, DATA_WIDTH


async def setup_fifo(dut): 
    dut.i_nrst.value = 0
    dut.wr_en0.value = 0
    dut.wr_en1.value = 0
    dut.rd_en0.value = 0
    dut.rd_en1.value = 0

    dut.i_push_instr0.value = 0
    dut.i_push_instr1.value = 0




@cocotb.test()
async def test_full_fifo_attempt_push_two(dut):
    """
    Case:
    - FIFO is full
    - attempt to push two instructions
    - both should be rejected
    """


    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)

    await setup_fifo(dut)
    
    await reset_dut(clk, rst, active_low=True, cycles=2)

    await fill_fifo_with_n(dut, INSTRUCTION_FIFO_DEPTH)

    assert int(dut.o_fifo_full.value) == 1
    assert int(dut.o_fifo_empty.value) == 0

    # Try to push two extra instructions. They should not enter.
    await push(dut, 1, 1, 1000, 1001)

    assert int(dut.o_fifo_full.value) == 1

    # Pop all entries and make sure only original entries are present.
    await pop_n_and_check(dut, list(range(INSTRUCTION_FIFO_DEPTH)))

    assert int(dut.o_fifo_empty.value) == 1


@cocotb.test()
async def test_empty_fifo_attempt_pop_two(dut):
    """
    Case:
    - FIFO is empty
    - attempt to pop two instructions
    - neither should be valid
    """

    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)

    await setup_fifo(dut)
    
    await reset_dut(clk, rst, active_low=True, cycles=2)

    
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

    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)

    await setup_fifo(dut)
    
    await reset_dut(clk, rst, active_low=True, cycles=2)

    await fill_fifo_with_n(dut, INSTRUCTION_FIFO_DEPTH - 1)

    assert int(dut.o_fifo_full.value) == 0
    assert int(dut.o_fifo_empty.value) == 0

    await push(dut, WR0, WR1, INSTR0, INSTR1)

    assert int(dut.o_fifo_full.value) == 1

    expected = list(range(INSTRUCTION_FIFO_DEPTH - 1)) + [INSTR0]
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

    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)

    await setup_fifo(dut)
    
    await reset_dut(clk, rst, active_low=True, cycles=2)

    await fill_fifo_with_n(dut, INSTRUCTION_FIFO_DEPTH - 2)

    await push(dut, WR0, WR1, INSTR0, INSTR1)

    assert int(dut.o_fifo_full.value) == 1

    expected = list(range(INSTRUCTION_FIFO_DEPTH - 2)) + [INSTR0, INSTR1]
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

    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)

    await setup_fifo(dut)
    
    await reset_dut(clk, rst, active_low=True, cycles=2)

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

    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)

    await setup_fifo(dut)
    
    await reset_dut(clk, rst, active_low=True, cycles=2)

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

    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)

    await setup_fifo(dut)
    
    await reset_dut(clk, rst, active_low=True, cycles=2)

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
    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)

    await setup_fifo(dut)
    
    await reset_dut(clk, rst, active_low=True, cycles=2)

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



@cocotb.test()
async def test_pop_nine_instructions_until_empty(dut):
    """
    Case:
    - FIFO contains 9 instructions
    - Pop two instructions at a time
    - For the first 4 pops, valid0 and valid1 should both be high
    - For the final pop, only valid0 should be high
    - After final pop, FIFO should be empty
    """

    """
    This checks the sequence: 

    count = 9 → valid0=1, valid1=1
    pop 2

    count = 7 → valid0=1, valid1=1
    pop 2

    count = 5 → valid0=1, valid1=1
    pop 2

    count = 3 → valid0=1, valid1=1
    pop 2

    count = 1 → valid0=1, valid1=0
    pop 1

    count = 0 → valid0=0, valid1=0, empty=1
    """

    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)

    await setup_fifo(dut)
    
    await reset_dut(clk, rst, active_low=True, cycles=2)

    expected_values = list(range(9000, 9009))

    await push_values(dut, expected_values)

    assert int(dut.o_fifo_empty.value) == 0
    assert int(dut.o_pop_valid0.value) == 1
    assert int(dut.o_pop_valid1.value) == 1

    await pop_n_and_check(dut, expected_values)

    assert int(dut.o_fifo_empty.value) == 1
    assert int(dut.o_fifo_full.value) == 0
    assert int(dut.o_pop_valid0.value) == 0
    assert int(dut.o_pop_valid1.value) == 0



@cocotb.test()
async def test_simultaneous_push_two_pop_two(dut):
    """
    Case:
    - FIFO starts with 4 instructions: 100, 101, 102, 103
    - In one clock cycle:
        pop 2 instructions
        push 2 new instructions: 200, 201
    - Count should remain effectively the same
    - Next visible outputs should be 102 and 103
    - Then after another pop, outputs should be 200 and 201
    """

    clk = dut.i_clk
    rst = dut.i_nrst

    start_clock(clk, period_ns=10)

    await setup_fifo(dut)
    
    await reset_dut(clk, rst, active_low=True, cycles=2)

    # Fill FIFO with 4 instructions
    await push(dut, 1, 1, 100, 101)
    await push(dut, 1, 1, 102, 103)

    await Timer(1, unit="ns")

    # Before simultaneous operation, head should show 100 and 101
    assert int(dut.o_fifo_empty.value) == 0
    assert int(dut.o_pop_valid0.value) == 1
    assert int(dut.o_pop_valid1.value) == 1
    assert int(dut.o_pop_instr0.value) == 100
    assert int(dut.o_pop_instr1.value) == 101

    # Same-cycle pop 2 and push 2
    dut.rd_en0.value = 1
    dut.rd_en1.value = 1
    dut.wr_en0.value = 1
    dut.wr_en1.value = 1
    dut.i_push_instr0.value = 200
    dut.i_push_instr1.value = 201

    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    # Deassert controls
    dut.rd_en0.value = 0
    dut.rd_en1.value = 0
    dut.wr_en0.value = 0
    dut.wr_en1.value = 0

    await Timer(1, unit="ns")

    # FIFO should now expose 102 and 103
    assert int(dut.o_fifo_empty.value) == 0
    assert int(dut.o_fifo_full.value) == 0
    assert int(dut.o_pop_valid0.value) == 1
    assert int(dut.o_pop_valid1.value) == 1
    assert int(dut.o_pop_instr0.value) == 102
    assert int(dut.o_pop_instr1.value) == 103

    # Pop 102 and 103
    dut.rd_en0.value = 1
    dut.rd_en1.value = 1

    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    dut.rd_en0.value = 0
    dut.rd_en1.value = 0

    await Timer(1, unit="ns")

    # FIFO should now expose newly pushed 200 and 201
    assert int(dut.o_pop_valid0.value) == 1
    assert int(dut.o_pop_valid1.value) == 1
    assert int(dut.o_pop_instr0.value) == 200
    assert int(dut.o_pop_instr1.value) == 201

    # Pop 200 and 201
    dut.rd_en0.value = 1
    dut.rd_en1.value = 1

    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    dut.rd_en0.value = 0
    dut.rd_en1.value = 0

    await Timer(1, unit="ns")

    # FIFO should now be empty
    assert int(dut.o_fifo_empty.value) == 1
    assert int(dut.o_pop_valid0.value) == 0
    assert int(dut.o_pop_valid1.value) == 0


def test_instr_fifo_runner():
    
    sim = os.getenv("SIM", "questa")
    proj_path = Path(__file__).resolve().parent.parent.parent

    sources = [proj_path / "hdl" / "frontend" / "instruction_fifo.sv"]

    runner = get_runner(sim)

    runner.build(
        sources=sources,
        hdl_toplevel="instruction_fifo",
        parameters={"DATA_WIDTH": DATA_WIDTH, "DEPTH": INSTRUCTION_FIFO_DEPTH},
        build_dir="sim_build/instr_fifo_test",
        always=True,
        clean=True
        
    )

    runner.test(
        hdl_toplevel="instruction_fifo",
        test_module="tb.unit.test_instruction_fifo",
        parameters={"DATA_WIDTH": DATA_WIDTH, "DEPTH": INSTRUCTION_FIFO_DEPTH},
        build_dir="sim_build/instr_fifo_test",
        
    )


if __name__ == "__main__":
    test_instr_fifo_runner()
    