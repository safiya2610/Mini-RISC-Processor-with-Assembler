# ==============================================================================
# Makefile for 32-Bit RISC Processor Core and Toolchain
# ==============================================================================
# Provides automated tasks for assembling programs, disassembling hex binaries,
# running hardware simulations, and workspace cleanup.
#
# Systems supported: Windows (PowerShell/CMD), Linux, macOS
# ==============================================================================

# Executables
PYTHON     := python
RM         := rm -rf

# Paths
TOOLCHAIN_DIR  := toolchain
ASM_SCRIPT     := $(TOOLCHAIN_DIR)/assembler.py
DISASM_SCRIPT  := $(TOOLCHAIN_DIR)/disassembler.py
TEST_DIR       := tests/assembly
HARDWARE_DIR   := hardware
RTL_DIR        := $(HARDWARE_DIR)/rtl
TB_DIR         := $(HARDWARE_DIR)/tb

.PHONY: help assemble disassemble clean sim test

help:
	@echo "======================================================================"
	@echo "               32-Bit RISC Processor Core Toolchain"
	@echo "======================================================================"
	@echo "Available commands:"
	@echo "  make assemble      Assemble all test programs to hex/bin format"
	@echo "  make disassemble   Disassemble assembled hex files back to assembly"
	@echo "  make sim           Compile and run RTL simulation using Icarus Verilog"
	@echo "  make clean         Remove generated binaries, hex files, and waveforms"
	@echo "======================================================================"

assemble:
	@echo "Assembling BasicTest..."
	$(PYTHON) $(ASM_SCRIPT) $(TEST_DIR)/BasicTest.r.asm -o $(TEST_DIR)/BasicTest.hex -f hex
	$(PYTHON) $(ASM_SCRIPT) $(TEST_DIR)/BasicTest.r.asm -o $(TEST_DIR)/BasicTest.bin -f bin
	@echo "Assembling BranchingTest..."
	$(PYTHON) $(ASM_SCRIPT) $(TEST_DIR)/BranchingTest.r.asm -o $(TEST_DIR)/BranchingTest.hex -f hex
	@echo "Assembly completed successfully."

disassemble:
	@echo "Disassembling BasicTest hex file..."
	$(PYTHON) $(DISASM_SCRIPT) $(TEST_DIR)/BasicTest.hex -o $(TEST_DIR)/BasicTest.dis.asm
	@echo "Disassembly completed successfully."

sim:
	@echo "Looking for Icarus Verilog compiler (iverilog)..."
	@where iverilog >nul 2>nul || (echo "Error: iverilog not found in PATH. Please install Icarus Verilog to run simulation." && exit 1)
	@echo "Compiling RTL and Testbench..."
	iverilog -g2012 -o cpu_sim.vvp $(RTL_DIR)/*.v $(RTL_DIR)/*.sv $(TB_DIR)/ProcessorTestbench.v $(TB_DIR)/BasicTestMemory.v
	@echo "Running simulation..."
	vvp cpu_sim.vvp
	@echo "Simulation completed. View cpu_sim.vcd (if generated) in GTKWave."

clean:
	@echo "Cleaning up generated files..."
	@del /f /q $(TEST_DIR)\*.hex $(TEST_DIR)\*.bin $(TEST_DIR)\*.dis.asm *.vvp *.vcd 2>nul || rm -f $(TEST_DIR)/*.hex $(TEST_DIR)/*.bin $(TEST_DIR)/*.dis.asm *.vvp *.vcd
	@echo "Clean completed."
