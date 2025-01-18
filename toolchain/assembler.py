#!/usr/bin/env python3
"""
Custom Assembler for the 32-Bit RISC Processor.
Converts assembly programs (.r.asm) into machine code (Hex, Binary, or Verilog Memory format).

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

# Global symbol table to resolve labels
symbol_table = {}

def clean_comments_and_whitespace(file_content):
    """
    Strips semi-colon and hash comments, normalizes spacing, and returns list of lines.
    """
    lines = []
    for raw_line in file_content.splitlines():
        # Remove comments starting with ; or #
        line = re.sub(r'[;#].*', '', raw_line).strip()
        if line:
            lines.append(line)
    return lines

def parse_register(token):
    """
    Parses registers like %r3, %R3, r3, R3, and returns register index (0-31).
    """
    match = re.match(r'^%?[rR](\d+)$', token)
    if match:
        reg_num = int(match.group(1))
        if 0 <= reg_num < 32:
            return reg_num
        raise ValueError(f"Register index r{reg_num} is out of bounds (must be 0-31)")
    raise ValueError(f"Invalid register format: '{token}'")

def is_register(token):
    """
    Returns True if the token matches a register format.
    """
    return bool(re.match(r'^%?[rR]\d+$', token))

def twos_complement(val, bits):
    """
    Returns the binary string of the two's complement representation of val with fixed bit width.
    """
    if val < 0:
        val = (1 << bits) + val
    val = val & ((1 << bits) - 1)
    return f"{val:0{bits}b}"

def fix_literal(literal, bits=16):
    """
    Converts literal string (decimal or hex) to a fixed-bit two's complement binary string.
    """
    try:
        if literal.lower().startswith("0x"):
            val = int(literal, 16)
        else:
            val = int(literal)
        return twos_complement(val, bits)
    except ValueError:
        raise ValueError(f"Invalid literal format: '{literal}'")

def get_label_offset(label, current_address):
    """
    Returns the PC-relative signed offset to the target label.
    """
    if label not in symbol_table:
        raise KeyError(f"Undefined label: '{label}'")
    # RISC processors often compute label offset relative to (current_address + 4) or current_address.
    # The original implementation uses: (current_address - symbol_table[label])
    # Let's preserve the original behavior:
    offset_bytes = current_address - symbol_table[label]
    return twos_complement(offset_bytes, 16)

def preprocess_glued_syntax(line):
    """
    Fixes syntax typos where the instruction is glued to a register, e.g. 'LDr1' or 'CMPLECr31'.
    """
    # Exclude label declarations starting with '.'
    if line.startswith("."):
        return line

    for op in sorted([x for x in OPCODES if x], key=len, reverse=True):
        pattern = rf"^{op}(%?[rR]\d+)"
        if re.match(pattern, line, re.IGNORECASE):
            # Insert space between instruction and register
            line = re.sub(rf"^{op}", f"{op} ", line, flags=re.IGNORECASE)
            break
    return line

def convert_inst(tokens, addr):
    """
    Converts a single instruction represented by list of tokens into its 32-bit binary representation.
    """
    op_name = tokens[0].upper()
    if op_name not in OPCODES:
        raise ValueError(f"Unknown instruction / opcode: '{op_name}'")
    
    op_code = OPCODES.index(op_name)
    opcode_bin = f"{op_code:06b}"

    # Count registers in arguments
    reg_count = sum(1 for t in tokens[1:] if is_register(t))

    if op_name == "LONG":
        # 32-bit absolute constant
        if len(tokens) < 2:
            raise ValueError("LONG directive requires a constant literal value")
        return fix_literal(tokens[1], 32)

    elif len(tokens) == 3:
        # Two-argument instructions like JMP or LDR
        # Form 1: R-Type variant with 2 registers e.g. JMP %Ra, %Rc -> JMP Ra, Rc, 0
        if reg_count == 2:
            ra = parse_register(tokens[1])
            rc = parse_register(tokens[2])
            return f"{opcode_bin}{rc:05b}{ra:05b}{0:016b}"
        # Form 2: Label variant e.g. LDR label, %Rc -> LDR Rc, 31, offset
        else:
            rc = parse_register(tokens[2])
            ra = 31  # Hardwired r31 reference
            offset = get_label_offset(tokens[1], addr)
            return f"{opcode_bin}{rc:05b}{ra:05b}{offset}"

    elif len(tokens) == 4:
        # Three-argument instructions
        if reg_count == 2:
            # Immediate or Memory instructions with 2 registers and a literal
            if op_name == "ST":
                # ST %Rc, literal, %Ra
                rc = parse_register(tokens[1])
                literal = fix_literal(tokens[2], 16)
                ra = parse_register(tokens[3])
                return f"{opcode_bin}{rc:05b}{ra:05b}{literal}"
            elif op_name in ("BEQ", "BNE"):
                # BEQ/BNE %Rc, label, %Ra
                rc = parse_register(tokens[1])
                offset = get_label_offset(tokens[2], addr)
                ra = parse_register(tokens[3])
                return f"{opcode_bin}{rc:05b}{ra:05b}{offset}"
            else:
                # Standard I-Type: OP %Ra, literal, %Rc
                ra = parse_register(tokens[1])
                literal = fix_literal(tokens[2], 16)
                rc = parse_register(tokens[3])
                return f"{opcode_bin}{rc:05b}{ra:05b}{literal}"
        elif reg_count == 3:
            # Standard R-Type instructions: OP %Ra, %Rb, %Rc
            ra = parse_register(tokens[1])
            rb = parse_register(tokens[2])
            rc = parse_register(tokens[3])
            return f"{opcode_bin}{rc:05b}{ra:05b}{rb:05b}{0:011b}"
        else:
            raise ValueError(f"Invalid operand structure for three-operand instruction '{op_name}'")
            
    else:
        raise ValueError(f"Invalid instruction argument count for '{op_name}' ({len(tokens) - 1} given)")

def main():
    parser = argparse.ArgumentParser(description="Professional Assembler for custom 32-Bit RISC Processor Core.")
    parser.add_argument("input_file", help="Path to assembly source file (.r.asm)")
    parser.add_argument("-o", "--output", help="Path to write the assembled machine code")
    parser.add_argument("-f", "--format", choices=["hex", "bin", "verilog", "binary_string"], default="hex",
                        help="Output format: 'hex' (32-bit hex words), 'bin' (raw binary bytes), "
                             "'verilog' (ready for $readmemh), 'binary_string' (32-bit bitstrings)")
    
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(args.input_file, "r") as f:
        raw_content = f.read()

    # Pre-process comments, normalize spacing, and fix stuck instructions
    raw_lines = clean_comments_and_whitespace(raw_content)
    lines = [preprocess_glued_syntax(l) for l in raw_lines]

    # First Pass: Build the Symbol Table
    cur_address = 0
    instructions = []
    
    for line in lines:
        if line.startswith("."):
            label = line[1:].strip()
            # Special case for .breakpoint, which compiles to a NOP (0x00000000) or special handling
            if label.lower() == "breakpoint":
                instructions.append((cur_address, ["ADD", "%r31", "%r31", "%r31"]))
                cur_address += 4
            else:
                symbol_table[label] = cur_address
        else:
            # Split tokens by space or commas
            tokens = [t for t in re.split(r'[,\s]+', line) if t]
            if tokens:
                instructions.append((cur_address, tokens))
                cur_address += 4

    # Second Pass: Translate instructions to binary machine code
    binary_instructions = []
    for addr, tokens in instructions:
        try:
            bin_str = convert_inst(tokens, addr)
            binary_instructions.append(bin_str)
        except Exception as e:
            print(f"Assembly Error at PC=0x{addr:04X} | Instruction: {' '.join(tokens)}", file=sys.stderr)
            print(f"Reason: {str(e)}", file=sys.stderr)
            sys.exit(1)

    # Formatted Output Generation
    output_lines = []
    
    if args.format == "hex":
        for b in binary_instructions:
            val = int(b, 2)
            output_lines.append(f"{val:08x}")
            
    elif args.format == "binary_string":
        output_lines = binary_instructions
        
    elif args.format == "verilog":
        # Generate $readmemh memory file starting from address 0
        output_lines.append("// Verilog Memory Initialization File ($readmemh format)")
        for i, b in enumerate(binary_instructions):
            val = int(b, 2)
            output_lines.append(f"@{i:X} {val:08x}")
            
    elif args.format == "bin":
        # Raw bytes format
        byte_data = bytearray()
        for b in binary_instructions:
            val = int(b, 2)
            # Big Endian (matching 32-bit word alignment)
            byte_data.extend(val.to_bytes(4, byteorder='big'))
        
        output_path = args.output if args.output else args.input_file.rsplit('.', 1)[0] + ".bin"
        with open(output_path, "wb") as f_out:
            f_out.write(byte_data)
        print(f"Successfully assembled: {len(binary_instructions)} instructions -> {output_path} (Raw Bytes)")
        return

    # Text formats output
    output_content = "\n".join(output_lines) + "\n"
    if args.output:
        with open(args.output, "w") as f_out:
            f_out.write(output_content)
        print(f"Successfully assembled: {len(binary_instructions)} instructions -> {args.output} ({args.format.upper()})")
    else:
        sys.stdout.write(output_content)

if __name__ == "__main__":
    main()
