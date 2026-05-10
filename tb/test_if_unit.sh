
#!bin/bash

source ../.venv/bin/activate

# Run test_instruction_memory tests
SIM=questa WAVES=1 GUI=1 HDL_TOPLEVEL_LANG=verilog pytest -s --log-cli-level=INFO -o log_cli=True test_if_unit.py
