
#!bin/bash

source ../.venv/bin/activate

# Run test_instruction_memory tests
SIM=questa HDL_TOPLEVEL_LANG=verilog pytest -s  test_instruction_memory.py
