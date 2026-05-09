
#!bin/bash

source ../.venv/bin/activate

# Run test_instruction_memory tests
SIM=questa HDL_TOPLEVEL_LANG=verilog pytest -s --log-cli-level=INFO -o log_cli=True test_instruction_fifo.py
