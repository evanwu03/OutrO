#!/usr/bin/env bash
set -e

source ../.venv/bin/activate

PYTEST_FLAGS="-s --log-cli-level=INFO -o log_cli=True"

TESTS=(
  unit/test_decoder.py
  unit/test_instruction_memory.py
  unit/test_instruction_fifo.py
  unit/test_if_unit.py
  unit/test_dispatch.py
  unit/test_rat.py
  unit/test_data_memory.py
)

run_pytest () {
  SIM=questa WAVES=0 GUI=0 HDL_TOPLEVEL_LANG=verilog \
    pytest $PYTEST_FLAGS "$@"
}

if [ "$#" -eq 0 ]; then
  echo "Error: no test selection provided."
  echo "Usage: $0 {all|decoder|instr_mem|instr_fifo|instr_fetch|dispatch|rat|data_mem|pytest_args...}"
  exit 1
fi

case "$1" in
  all)
    run_pytest "${TESTS[@]}"
    ;;
  decoder)
    run_pytest unit/test_decoder.py
    ;;
  instr_mem)
    run_pytest unit/test_instruction_memory.py
    ;;
  instr_fifo)
    run_pytest unit/test_instruction_fifo.py
    ;;
  instr_fetch)
    run_pytest unit/test_if_unit.py
    ;;
  dispatch)
    run_pytest unit/test_dispatch.py
    ;;
  rat)
    run_pytest unit/test_rat.py
    ;;
  data_mem)
    run_pytest unit/test_data_memory.py
    ;;
  *)
    run_pytest "$@"
    ;;
esac