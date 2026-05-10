
#!bin/bash

source ../.venv/bin/activate

# Run test_instruction_memory tests
SIM=questa WAVES=0 GUI=0 HDL_TOPLEVEL_LANG=verilog pytest -s --log-cli-level=INFO -o log_cli=True test_decoder.py
