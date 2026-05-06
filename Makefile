# Makefile

# defaults
SIM ?= questa
HDL_DIR  := hdl
TB_DIR   := tb
BUILD    := build


# Location of python installation
VENV := /home/evanwu03/projects/OutrO/.venv
PYTHON_BIN := $(VENV)/bin/python

TOPLEVEL_LANG ?= verilog


# use VHDL_SOURCES for VHDL files

# COCOTB_TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL ?= cpu
COCOTB_TOPLEVEL ?= $(TOPLEVEL)

# Default log level of all "cocotb" loggers
COCOTB_LOG_LEVEL ?= DEBUG

# COCOTB_TEST_MODULES is the basename of the Python test file(s)
COCOTB_TEST_MODULES ?= test_cpu # This has to be on same level as makefile apparently

VERILOG_SOURCES :=  $(wildcard $(HDL_DIR)/*.sv) \
#	$(TB_DIR)/$(TOPLEVEL).sv \

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

