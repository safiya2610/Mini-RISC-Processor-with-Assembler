# 32-Bit Single-Core RISC Processor Core



A custom-designed, 32-bit single-core unpipelined RISC processor architecture implemented from scratch in Verilog HDL. This project serves as a comprehensive exploration of hardware description languages, computer architecture principles, and hardware-software co-design.

Alongside the processor core, this repository includes a custom-built software ecosystem featuring a Python-based assembler and disassembler toolchain.

---

## Key Features & Capabilities

* **32-Bit Standard Core:** Full 32-bit data path and address bus handling.
* **Dual Execution Modes:** Hardware-level separation between **User Mode** and **Supervisor (Kernel) Mode** for system security.
* **Interrupt Handling:** Support for both synchronous exceptions (illegal opcodes) and asynchronous external interrupts (hardware IRQs and system reset).
* **Custom Toolchain:** Specialized Python scripts to convert human-readable assembly instructions into raw binary machine code and vice versa.

---

## Architecture & Specifications Overview

The processor design is inspired by the structured computational principles of the **MIT 6.004 (Computation Structures)** framework. It executes a robust instruction set capable of general-purpose computing tasks.

### Memory Subsystem
* **Addressing:** Byte-addressable memory architecture where each individual byte is 8-bit.
* **Data Access:** Memory operations fetch/store 4 bytes simultaneously, creating a 32-bit wide memory access path.
* **Address Space:** The core is theoretically capable of addressing up to $2^{32}$ bytes ($4\text{ GB}$) of physical memory.

### Register Configuration
* Employs a register file consisting of **32 general-purpose registers (`r0` to `r31`)**, each 32-bit wide.
* **Hardware Restrictions:** Registers `r27` through `r30` are strictly reserved for internal hardware operations and exception handling. 
* **Constant Zero:** Register `r31` is hardwired to `0x00000000`, providing a permanent zero reference for optimizations.

---

## Execution Modes & Privilege Levels

### 1. User Mode
* Indicated when the Most Significant Bit (MSB) of the Program Counter (PC) is set to `0`.
* Restricted execution environment. If an external interrupt or hardware fault occurs, the core automatically switches context to Supervisor Mode, pausing the active application.

### 2. Supervisor Mode (Kernel Mode)
* Active when the MSB of the Program Counter (PC) is set to `1`.
* Privileged execution environment where hardware interrupts are safely masked/ignored during critical routines.
* **System Calls:** User space programs can trigger a kernel switch by executing an illegal opcode. The processor then automatically jumps to the exception vector address `0x00000008`, caching the return address in the `XP` (`r27`) register, and loading the new privileged PC at `0x80000008`.

---

## Instruction Set Architecture (ISA)

The processor supports **30 fundamental instructions** structured tightly into two 32-bit encoding formats:
1. **R-Type (Register Format):** `<OP_code><RegAdd1><RegAdd2><RegAdd3><constant>`
2. **I-Type (Immediate Format):** `<OP_code><RegAdd1><RegAdd2><16BitLiteral>`

| Instruction | Type | Functional Description |
| :--- | :--- | :--- |
| **ADD / SUB** | R-Type | Performs signed addition/subtraction between two registers and stores the result. |
| **ADDC / SUBC** | I-Type | Adds or subtracts a 16-bit constant value to/from a target register. |
| **AND / OR / XOR** | R-Type | Standard bitwise logical operations between source registers. |
| **ANDC / ORC / XORC**| I-Type | Bitwise operations combining a register with a sign-extended 16-bit literal value. |
| **BEQ / BNE** | I-Type | Conditional branching based on zero-flag check; saves next PC to `reg3` for linking. |
| **CMPLE / CMPEQ / CMPLT**| R-Type | Compares values (Less than/Equal/Less than or Equal) and writes a `0x1` boolean flag if true. |
| **LD / LDR / ST** | I-Type | Memory interface: Load, Program-Counter relative Load, and Store operations. |
| **MUL / MULC** | Mixed | Hardware multiplication support using register values or 16-bit constants. |
| **SHL / SHR / SRA** | Mixed | Bitwise shifts (Logical Left, Logical Right, and Arithmetic Right with sign preservation). |
| **JMP** | R-Type | Unconditional jump to a computed target register address, caching current PC into `reg3`. |

---

## Sample Assembly Syntax

The assembler reads a custom variant of AT&T style syntax. Instructions are formatted as: 
`[Opcode] [Operand1], [Operand2], [Destination]`

```assembly
; =============================================
; Sample Arithmetic Program
; =============================================
    AND %r31, %r31, %r0     ; Clear r0 by masking with r31 (0)
    CMPEQ %r31, %r31, %r1   ; Load 1 into r1 because r31 equals r31
    ADD %r1, %r1, %r2       ; r2 = r1 + r1 (Loads 2 into r2)
    OR %r2, %r1, %r3        ; Bitwise OR operations
    SHL %r1, %r2, %r4       ; Logical shift left operation