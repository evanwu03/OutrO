# test_instruction_fetch_unit.py
import os
from pathlib import Path

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb_tools.runner import get_runner

from ..common.clock_reset import start_clock, reset_dut

""" Contents of program.hex for reference"""
""" PROGRAM = [
    0x00000000,
    0x11111111,
    0x22222222,
    0x33333333,
    0x44444444,
    0x55555555,
    0x66666666,
    0x77777777,
    0x88888888,
    0x99999999,
    0xAAAAAAAA,
    0xBBBBBBBB,
    0xCCCCCCCC,
    0xDDDDDDDD,
    0xEEEEEEEE,
    0xFFFFFFFF
]
 """

PROGRAM_HEX = (Path(__file__).resolve().parent.parent / "../programs/program.hex").resolve()

with open(PROGRAM_HEX) as f:
    PROGRAM = [int(line.strip(), 16) for line in f if line.strip()]

instr_count = len(PROGRAM)

async def setup_dut(dut, pc=0, stall=False) -> None:
    dut.i_pc.value = pc

    if(stall):
        dut.i_instr_stall.value = 1
    else: 
        dut.i_instr_stall.value = 0


@cocotb.test()
async def test_fetch_instruction_pairs(dut):
    """
    Model external PC feedback:
      i_pc <= o_pc_next each cycle

    The FIFO streams one pair out while the IF unit pushes the next pair in.
    """
    

    clk = dut.i_clk
    rst = dut.i_nrst

    pc = 0

    start_clock(clk, period_ns=10)

    await setup_dut(dut, pc=pc, stall=False)
    await reset_dut(clk, rst, active_low=True, cycles=2)


    # Prime the FIFO with the first fetch pair.
    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    # First pair should now be visible.
    assert int(dut.w_pop_valid0.value) == 1
    assert int(dut.w_pop_valid1.value) == 1
    assert int(dut.o_instr0.value) == PROGRAM[0]
    assert int(dut.o_instr1.value) == PROGRAM[1]
    assert int(dut.o_pc_next.value) == 8

    # Now stream through the rest.
    # At each cycle:
    #   - current visible pair is checked
    #   - o_pc_next is fed back into i_pc
    #   - decode pops current pair
    #   - IF pushes next pair
    for idx in range(0, len(PROGRAM) - 1, 2):
        expected_instr0 = PROGRAM[idx]
        expected_instr1 = PROGRAM[idx + 1]
        expected_pc_next = pc + 8

        actual_instr0 = int(dut.o_instr0.value)
        actual_instr1 = int(dut.o_instr1.value)
        actual_pc_next = int(dut.o_pc_next.value)

        dut._log.info(
            "idx=%0d PC=0x%08X instr0=0x%08X expected0=0x%08X "
            "instr1=0x%08X expected1=0x%08X pc_next=0x%08X expected_pc_next=0x%08X",
            idx,
            pc,
            actual_instr0,
            expected_instr0,
            actual_instr1,
            expected_instr1,
            actual_pc_next,
            expected_pc_next,
        )

        assert int(dut.w_pop_valid0.value) == 1
        assert int(dut.w_pop_valid1.value) == 1

        assert actual_instr0 == expected_instr0, (
            f"PC=0x{pc:08X}: instr0 mismatch. "
            f"Got 0x{actual_instr0:08X}, expected 0x{expected_instr0:08X}"
        )

        assert actual_instr1 == expected_instr1, (
            f"PC=0x{pc:08X}: instr1 mismatch. "
            f"Got 0x{actual_instr1:08X}, expected 0x{expected_instr1:08X}"
        )

        assert actual_pc_next == expected_pc_next, (
            f"PC=0x{pc:08X}: pc_next mismatch. "
            f"Got 0x{actual_pc_next:08X}, expected 0x{expected_pc_next:08X}"
        )

        # Feed back next PC for next fetch.
        pc = actual_pc_next
        dut.i_pc.value = pc

        await RisingEdge(dut.i_clk)
        await Timer(1, unit="ns")

    assert int(dut.w_fifo_empty.value) == 1
    assert int(dut.w_pop_valid0.value) == 0
    assert int(dut.w_pop_valid1.value) == 0


@cocotb.test()
async def test_instr_stall_holds_current_output_pair(dut):
    """
    Simple stall test:
    - Fetch first pair into FIFO.
    - Assert instruction stall.
    - Feed back o_pc_next to i_pc.
    - On the next clock, FIFO may push the next pair behind it,
      but it must NOT pop the current pair.
    - Therefore o_instr0/o_instr1 should remain PROGRAM[0]/PROGRAM[1].
    """

    clk = dut.i_clk
    rst = dut.i_nrst

    pc = 0

    start_clock(clk, period_ns=10)

    await setup_dut(dut, pc=pc, stall=False)
    await reset_dut(clk, rst, active_low=True, cycles=2)
    
    # -------------------------
    # Cycle 1: fetch first pair
    # -------------------------
    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    assert int(dut.w_pop_valid0.value) == 1
    assert int(dut.w_pop_valid1.value) == 1

    assert int(dut.o_instr0.value) == PROGRAM[0]
    assert int(dut.o_instr1.value) == PROGRAM[1]

    pc_next = int(dut.o_pc_next.value)
    assert pc_next == 0x8

    # -------------------------
    # Cycle 2: keep stalled
    # Feed back next PC, but do not allow FIFO to pop.
    # The next pair may be pushed behind the first pair.
    # -------------------------
    dut.i_pc.value = pc_next
    dut.i_instr_stall.value = 1

    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    # The head of the FIFO should still be the first pair.
    assert int(dut.w_pop_valid0.value) == 1
    assert int(dut.w_pop_valid1.value) == 1

    assert int(dut.o_instr0.value) == PROGRAM[0], (
        f"Expected instr0 to remain 0x{PROGRAM[0]:08X}, "
        f"got 0x{int(dut.o_instr0.value):08X}"
    )

    assert int(dut.o_instr1.value) == PROGRAM[1], (
        f"Expected instr1 to remain 0x{PROGRAM[1]:08X}, "
        f"got 0x{int(dut.o_instr1.value):08X}"
    )


    # Cycle 3: remove stall
    # Fetch next pair of instructions 
    pc_next = int(dut.o_pc_next.value)
    assert pc_next == 0x10
    dut.i_pc.value = pc_next
    dut.i_instr_stall.value = 0

    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    assert int(dut.w_pop_valid0.value) == 1
    assert int(dut.w_pop_valid1.value) == 1

    assert int(dut.o_instr0.value) == PROGRAM[2], (
        f"Expected instr0 to be 0x{PROGRAM[2]:08X}, "
        f"got 0x{int(dut.o_instr0.value):08X}"
    )

    assert int(dut.o_instr1.value) == PROGRAM[3], (
        f"Expected instr1 to be 0x{PROGRAM[3]:08X}, "
        f"got 0x{int(dut.o_instr1.value):08X}"
    )


    pc_next = int(dut.o_pc_next.value)
    assert pc_next == 0x18
    dut.i_pc.value = pc_next
    dut.i_instr_stall.value = 0

    await RisingEdge(dut.i_clk)
    await Timer(1, unit="ns")

    assert int(dut.w_pop_valid0.value) == 1
    assert int(dut.w_pop_valid1.value) == 1

    assert int(dut.o_instr0.value) == PROGRAM[4], (
        f"Expected instr0 to be 0x{PROGRAM[4]:08X}, "
        f"got 0x{int(dut.o_instr0.value):08X}"
    )

    assert int(dut.o_instr1.value) == PROGRAM[5], (
        f"Expected instr1 to be 0x{PROGRAM[5]:08X}, "
        f"got 0x{int(dut.o_instr1.value):08X}"
    )



def test_if_unit_runner():
    
    sim = os.getenv("SIM", "questa")
    proj_path = Path(__file__).resolve().parent.parent.parent

    sources = [proj_path / "hdl" / "frontend" / "instruction_fetch_unit.sv",
               proj_path / "hdl" / "frontend" / "instruction_fifo.sv",
               proj_path / "hdl" / "frontend" / "instruction_memory.sv"]

    runner = get_runner(sim)

    parameters = {"INSTR_WIDTH": 32, 
                    "DEPTH":256,
                    "INSTR_COUNT":instr_count,
                    "BASE_ADDR": 0x0000}
    runner.build(
        sources=sources,
        hdl_toplevel="instruction_fetch_unit",
        parameters=parameters,
        build_dir="sim_build/if_unit_test",
        always=True,
        clean=True
        
    )

    runner.test(
        hdl_toplevel="instruction_fetch_unit",
        test_module="tb.unit.test_if_unit",
        parameters=parameters,
        build_dir="sim_build/if_unit_test",
        
    )

if __name__ == "__main__":
    test_if_unit_runner()