

# test_instruction_fetch_unit.py

import os
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb_tools.runner import get_runner
from cocotb.triggers import Timer


async def reset_dut(dut):
    dut.i_nrst.value = 0
    dut.i_pc.value = 0
    dut.i_instr_stall.value = 0


    await RisingEdge(dut.i_clk)
    await RisingEdge(dut.i_clk)

    dut.i_nrst.value = 1
    #await RisingEdge(dut.i_clk)
    #await Timer(1, unit="ns")

@cocotb.test()
async def test_alu_instruction(dut):
    assert True



def test_if_unit_runner():
    
    sim = os.getenv("SIM", "questa")
    proj_path = Path(__file__).resolve().parent.parent

    sources = [ 
        proj_path / "hdl"  /"include" / "cpu_pkg.sv",
        proj_path / "hdl" / "decode_stage" / "decoder.sv",
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
        test_module="test_decoder",
        parameters=parameters,
        build_dir="sim_build/decoder_test",
        
    )

if __name__ == "__main__":
    test_if_unit_runner()