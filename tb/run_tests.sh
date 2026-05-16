
#!/usr/bin/env bash
set -e

source ../.venv/bin/activate

PYTEST_FLAGS="-s --log-cli-level=INFO -o log_cli=True"

run_pytest () {
    SIM=questa WAVES=0 GUI=0 HDL_TOPLEVEL_LANG=verilog \
    pytest $PYTEST_FLAGS "$@"
}

if [ "$#" -eq 0 ]; then
    echo "Error: no test selection provided."
    echo "Usage: $0 {decoder|instr_mem|instr_queue|all|pytest_args...}"
    exit 1
fi

case "$1" in
    decoder)
        run_pytest test_decoder.py
        ;;

    instr_mem)
        run_pytest test_instruction_memory.py
        ;;

    instr_fifo)
        run_pytest test_instruction_fifo.py
        ;;

    instr_fetch)
        run_pytest test_if_unit.py
        ;;

    *)
        run_pytest "$@"
        ;;
esac