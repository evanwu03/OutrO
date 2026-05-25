
from __future__ import annotations

import os
from pathlib import Path

import cocotb
from cocotb_tools.runner import get_runner
from cocotb.triggers import Timer

LANGUAGE = os.getenv("TOPLEVEL_LANG", "verilog").lower().strip()

async def load_program(dut, instrs):
    for i, instr in enumerate(instrs):
        dut.memory[i].value = instr
    await Timer(1, unit="ns")


@cocotb.test()
async def test_dual_fetch_happy_path(dut):
    program = [
        0x11111111,
        0x22222222,
        0x33333333,
        0x44444444,
    ]

    await load_program(dut, program)

    # PC = 0 fetches instruction 0 and 1
    dut.i_pc.value = 0x0
    await Timer(1, unit="ns")

    assert dut.o_instr_0.value.to_unsigned() == 0x11111111
    assert dut.o_instr_1.value.to_unsigned() == 0x22222222

    # PC = 8 fetches instruction 2 and 3
    dut.i_pc.value = 0x8
    await Timer(1, unit="ns")

    assert dut.o_instr_0.value.to_unsigned() == 0x33333333
    assert dut.o_instr_1.value.to_unsigned() == 0x44444444


@cocotb.test()
async def test_odd_instruction_count_second_fetch_invalid(dut):
    program = [
        0xAAAA0001,
        0xBBBB0002,
        0xCCCC0003,
    ]

    await load_program(dut, program)

    # PC = 8 points to third instruction.
    # instr0 should be valid, instr1 should be out-of-bounds.
    dut.i_pc.value = 0x8
    await Timer(1, unit="ns")

    assert dut.o_instr_0.value.to_unsigned() == 0xCCCC0003
    assert dut.o_instr_1.value.to_unsigned() == 0x0


@cocotb.test()
async def test_non_word_aligned_pc_returns_zero(dut):
    program = [
        0x11111111,
        0x22222222,
    ]

    await load_program(dut, program)

    # PC = 2 is not 4-byte aligned.
    dut.i_pc.value = 0x2
    await Timer(1, unit="ns")

    assert dut.o_instr_0.value.to_unsigned() == 0x0
    assert dut.o_instr_1.value.to_unsigned() == 0x0


def run_test(testcase, instr_count, build_dir):
    sim = os.getenv("SIM", "questa")
    proj_path = Path(__file__).resolve().parent.parent.parent

    sources = [proj_path / "hdl" / "frontend" / "instruction_memory.sv"]

    runner = get_runner(sim)

    runner.build(
        sources=sources,
        hdl_toplevel="instruction_memory",
        parameters={"INSTR_COUNT": instr_count},
        build_dir=build_dir,
        always=True,
    )

    runner.test(
        hdl_toplevel="instruction_memory",
        test_module="tb.unit.test_instruction_memory",
        testcase=testcase,
        parameters={"INSTR_COUNT": instr_count},
        build_dir=build_dir,
    )


def test_dual_fetch_runner():
    run_test(
        testcase="test_dual_fetch_happy_path",
        instr_count=4,
        build_dir="sim_build/instr_count_4",
    )


def test_odd_count_runner():
    run_test(
        testcase="test_odd_instruction_count_second_fetch_invalid",
        instr_count=3,
        build_dir="sim_build/instr_count_3_odd",
    )


def test_unaligned_runner():
    run_test(
        testcase="test_non_word_aligned_pc_returns_zero",
        instr_count=3,
        build_dir="sim_build/instr_count_3_unaligned",
    )

if __name__ == "__main__":
    test_dual_fetch_runner()
    test_odd_count_runner()
    test_unaligned_runner()