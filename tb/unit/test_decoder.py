

# test_decoder.py

import os
from pathlib import Path

import cocotb
from cocotb_tools.runner import get_runner

from ..common.config import *
from ..drivers.decoder_driver import *

def get_packed_field(handle, start, stop=None):
    full_value = handle.value
    if stop is None:
        return full_value[start]
    else:
        return full_value[start:stop]



@cocotb.test()
async def test_decode_data_processing_instructions(dut):
    """
    Generic decode test for supported ARM data-processing instructions.
    """

    test_vectors = [
        ("AND", ARM_AND),
        ("SUB", ARM_SUB),
        ("ADD", ARM_ADD),
        ("CMN", ARM_CMN),
        ("TEQ", ARM_TEQ),
        ("MVN", ARM_MVN),
    ]

    for name, opcode in test_vectors:
        await drive_and_check_data_proc(
            dut,
            name=name,
            opcode=opcode,
            uses_imm=1,
            set_cond=0,
            rn=1,
            rd=0,
            operand2=1,
        )


@cocotb.test()
async def test_decode_load_store_instructions(dut):
    """
    Generic decode test for ARM LDR/STR single data transfer instructions.
    """

    test_vectors = [
        {
            "name": "LDR R0, [R1, #4]",
            "is_load": 1,
            "rn": 1,
            "rd": 0,
            "offset": 4,
            "pre_index": 1,
            "offset_dir": 1,
            "is_byte": 0,
            "writeback": 0,
        },
        {
            "name": "STR R2, [R3, #8]",
            "is_load": 0,
            "rn": 3,
            "rd": 2,
            "offset": 8,
            "pre_index": 1,
            "offset_dir": 1,
            "is_byte": 0,
            "writeback": 0,
        },
        {
            "name": "LDRB R4, [R5, #12]",
            "is_load": 1,
            "rn": 5,
            "rd": 4,
            "offset": 12,
            "pre_index": 1,
            "offset_dir": 1,
            "is_byte": 1,
            "writeback": 0,
        },
        {
            "name": "STR R6, [R7, #-16]",
            "is_load": 0,
            "rn": 7,
            "rd": 6,
            "offset": 16,
            "pre_index": 1,
            "offset_dir": 0,
            "is_byte": 0,
            "writeback": 0,
        },
        {
            "name": "LDR R8, [R9, #20]!",
            "is_load": 1,
            "rn": 9,
            "rd": 8,
            "offset": 20,
            "pre_index": 1,
            "offset_dir": 1,
            "is_byte": 0,
            "writeback": 1,
        },
    ]

    for tv in test_vectors:
        await drive_and_check_mem_instr(dut, **tv)


@cocotb.test()
async def test_decode_branch_instructions(dut):
    """
    Test decoding of B and BL instructions.
    """
    test_vectors = [
        {
            "name": "B forward",
            "is_link": 0,
            "offset": 0x000004,
        },
        {
            "name": "BL forward",
            "is_link": 1,
            "offset": 0x000010,
        },
        {
            "name": "B max positive raw offset",
            "is_link": 0,
            "offset": 0x7FFFFF,
        },
        {
            "name": "BL negative raw offset",
            "is_link": 1,
            "offset": 0xFFFFFC,
        },
    ]

    for tv in test_vectors:
        await drive_and_check_branch_instr(dut, **tv)

def test_if_unit_runner():
    
    sim = os.getenv("SIM", "questa")
    proj_path = Path(__file__).resolve().parent.parent.parent

    sources = [ 
        proj_path / "hdl"  /"include" / "cpu_pkg.sv",
        proj_path / "hdl" / "dispatch" / "decoder.sv",
        ]

    runner = get_runner(sim)

    parameters = {"INSTR_WIDTH": 32}

    runner.build(
        sources=sources,
        hdl_toplevel="decoder",
        parameters=parameters,
        build_dir="sim_build/decoder_test",
        always=True,
        clean=True
        
    )

    runner.test(
        hdl_toplevel="decoder",
        test_module="tb.unit.test_decoder",
        parameters=parameters,
        build_dir="sim_build/decoder_test",
        
    )

if __name__ == "__main__":
    test_if_unit_runner()