#!/usr/bin/env python3
"""
Custom Disassembler for the 32-Bit RISC Processor.
Decodes 32-bit Hex machine code files back into readable assembly syntax.

Author: Antigravity AI & Suyash Mahar
License: MIT
"""

import os
import re
import sys
import argparse

# Define instruction set architecture mapping (indices correspond to opcodes)
OPCODES = [
    # 0 - 23: Reserved
    *[None] * 24,
    # 24 - 31: Control & Memory
    "LD", "ST", None, "JMP", None, "BEQ", "BNE", "LDR",
    # 32 - 39: Arithmetic & Comparison
    "ADD", "SUB", "MUL", "DIV", "CMPEQ", "CMPLT", "CMPLE", None,
    # 40 - 47: Bitwise Logical & Shift
    "AND", "OR", "XOR", None, "SHL", "SHR", "SRA", None,
    # 48 - 55: Immediate Arithmetic & Comparison
    "ADDC", "SUBC", "MULC", "DIVC", "CMPEQC", "CMPLTC", "CMPLEC", None,
    # 56 - 63: Immediate Logical & Shift
    "ANDC", "ORC", "XORC", None, "SHLC", "SHRC", "SRAC", None,
    # 64: Raw 32-bit constant
    "LONG"
]

def decode_literal(binary_str, bits=16):
    """
    Decodes a two's complement binary string of length `bits` into a signed integer.
    """
    val = int(binary_str, 2)
    if val & (1 << (bits - 1)):
        val = val - (1 << bits)
    return val

def disassemble_word(word_hex, pc):
    """
    Disassembles a single 32-bit hex word at a given Program Counter address.
    """
    word_hex = word_hex.strip()
    if not word_hex or word_hex.startswith("#") or word_hex.startswith(";"):
        return None
        
    try:
        # Check if it represents a valid hex number
        val = int(word_hex, 16)
    except ValueError:
        return f"; [Invalid Hex] {word_hex}"

    # Form 32-bit binary string
    binary_str = f"{val:032b}"
    
    # Extract 6-bit opcode
    opcode_num = int(binary_str[0:6], 2)
    
    if opcode_num >= len(OPCODES) or OPCODES[opcode_num] is None:
        return f"; [Illegal Opcode: 0b{binary_str[0:6]} at PC=0x{pc:04X}] LONG 0x{val:08X}"

    op_name = OPCODES[opcode_num]

    # Decode register bits
    rc_num = int(binary_str[6:11], 2)
    ra_num = int(binary_str[11:16], 2)
    
    # Check if the instruction uses an immediate (ends in 'C', or is LD, ST, BEQ, BNE, LDR)
    is_immediate = op_name.endswith("C") or op_name in ("LD", "ST", "BEQ", "BNE", "LDR")

    if op_name == "LONG":
        return f"LONG 0x{val:08X}"
        
    elif op_name in ("LD", "ST", "BEQ", "BNE"):
        # Format: OP %Rc, literal, %Ra
        literal_bin = binary_str[16:32]
        literal = decode_literal(literal_bin, 16)
        
        if op_name in ("BEQ", "BNE"):
            # Branches have label/offset syntax
            return f"{op_name} %r{rc_num}, {literal}, %r{ra_num}  ; branch offset = {literal} bytes"
        else:
            return f"{op_name} %r{rc_num}, {literal}, %r{ra_num}"
            
    elif op_name in ("JMP", "LDR"):
        # Forms: JMP %Ra, %Rc or LDR label/literal, %Rc
        # Check if Ra is 31 (PC-relative/literal for label variant)
        if ra_num == 31 and op_name == "LDR":
            literal_bin = binary_str[16:32]
            literal = decode_literal(literal_bin, 16)
            return f"{op_name} {literal}, %r{rc_num}"
        else:
            return f"{op_name} %r{ra_num}, %r{rc_num}"
            
    elif is_immediate:
        # Standard immediate type: OP %Ra, literal, %Rc
        literal_bin = binary_str[16:32]
        literal = decode_literal(literal_bin, 16)
        return f"{op_name} %r{ra_num}, {literal}, %r{rc_num}"
        
    else:
        # Standard register type: OP %Ra, %Rb, %Rc
        rb_num = int(binary_str[16:21], 2)
        return f"{op_name} %r{ra_num}, %r{rb_num}, %r{rc_num}"

def main():
    parser = argparse.ArgumentParser(description="Professional Disassembler for 32-Bit RISC Processor Core.")
    parser.add_argument("input_file", help="Path to hex program file (.txt or .hex)")
    parser.add_argument("-o", "--output", help="Path to write the disassembled assembly text")
    
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(args.input_file, "r") as f:
        lines = f.readlines()

    disassembled_lines = [
        "; ===========================================================",
        f"; Disassembled from: {os.path.basename(args.input_file)}",
        "; ===========================================================",
        ""
    ]
    
    pc = 0
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if line_stripped.startswith("#") or line_stripped.startswith(";"):
            # Forward comments
            disassembled_lines.append(line_stripped)
            continue
            
        asm_str = disassemble_word(line_stripped, pc)
        if asm_str:
            # Print with address comment
            disassembled_lines.append(f"    {asm_str:<45} ; PC = 0x{pc:04X} ({pc})")
            pc += 4

    output_content = "\n".join(disassembled_lines) + "\n"
    if args.output:
        with open(args.output, "w") as f_out:
            f_out.write(output_content)
        print(f"Successfully disassembled: {pc // 4} instructions -> {args.output}")
    else:
        sys.stdout.write(output_content)

if __name__ == "__main__":
    main()
