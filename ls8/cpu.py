"""CPU functionality."""

import sys
import time

# Instructions

ADD = 0b10100000  # 0
# AND  = 0b10101000  # 8
CALL = 0b01010000  # 0
# CMP  = 0b10100111  # 7
DEC  = 0b01100110  # 6
# DIV  = 0b10100011  # 3
HLT = 0b00000001  # 1
INC  = 0b01100101  # 5
INT  = 0b01010010  # 2
IRET = 0b00010011  # 3
JEQ  = 0b01010101  # 5
JGE  = 0b01011010  # 10
JGT  = 0b01010111  # 7
JLE  = 0b01011001  # 9
JLT  = 0b01011000  # 8
JMP = 0b01010100  # 4
JNE  = 0b01010110  # 6
# LD   = 0b10000011  # 3
LDI = 0b10000010  # 2
# MOD  = 0b10100100  # 4
MUL = 0b10100010  # 2
# NOP  = 0b00000000  # 0
# NOT  = 0b01101001  # 9
# OR   = 0b10101010  # 10
POP = 0b01000110  # 6
# PRA  = 0b01001000  # 8
PRN = 0b01000111  # 7
PUSH = 0b01000101  # 5
RET = 0b00010001  # 1
# SHL  = 0b10101100  # 12
# SHR  = 0b10101101  # 13
ST = 0b10000100  # 4
# SUB  = 0b10100001  # 1
# XOR  = 0b10101011  # 11

# Other constants
IM = 5
IS = 6
SP = 7


HARDCODE_PROGRAM = [
        0b10000010, # LDI R0,8
        0b00000000,
        0b00001000,
        0b01000111, # PRN R0
        0b00000000,
        0b00000001, # HLT
    ]

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        
        # registers R0 thru R7
        # R5 is reserved as the interrupt mask (IM)
        # R6 is reserved as the interrupt status (IS)
        # R7 is reserved as the stack pointer (SP)
        self.registers = [0b0] * 8

        # internal registers
        self.pc = 0 # PC: Program Counter
        self.ir = None # IR: Instruction Register
        self.mar = None # MAR: Memory Address Register
        self.mdr = None # MDR: Memory Data Register
        self.spl = None # stack pointer location
        self.interrupts_enabled = True

        self.ram = [0b0] * 0xFF
        self.spl = 8 - 1
        self.registers[self.spl] = 0xF4


        self.branchtable = {
            ADD:  self.add,
            CALL: self.call,
            HLT:  self.hlt,
            LDI:  self.ldi,
            MUL:  self.mul,
            POP:  self.pop,
            PRN:  self.prn,
            PUSH: self.push,
            RET:  self.ret,
            ST:   self.st,
        }

#################################################################################
#
#                          Basic Emulator Functions
#
#################################################################################

    def load(self, program=HARDCODE_PROGRAM):
        """Load a program into memory."""

        address = 0
        if program != HARDCODE_PROGRAM:
            try:
                with open(program, 'r') as f:
                    for line in f:
                        instruction = line.split('#')[0].strip()
                        if instruction == '':
                            continue
                        self.ram[address] = int(instruction, base=2)
                        address += 1

            except FileNotFoundError:
                print(f'File not found. path: {program}')
                sys.exit(2)
        else:
            for instruction in program:
                self.ram[address] = instruction
                address += 1
    
    def ram_read(self, MAR):
        return self.ram[MAR]

    def ram_write(self, MDR, MAR):
        self.ram[MAR] = self.ram[MDR]

    def invoke_instruction(self):
        if self.ir in self.branchtable:
            self.branchtable[self.ir]()
        else:
            print(f"I did not understand that ir: {bin(self.ir)}")
            sys.exit(1)

    def move_pc(self):
        instruction_sets_pc = ((self.ir << 3) & 255) >> 7
        if not instruction_sets_pc:
            self.pc += (self.num_operands + 1)
    
    def check_interrupts(self):
        masked_interrupts = self.registers[IM] & self.registers[IS]
        for i in range(8):
            interrupt_happened = ((masked_interrupts >> i) & 1) == 1
            if interrupt_happened:
                self.interrupts_enabled = False
                self.registers[IS] = self.registers[IS] & (255 - 2**i)
                self.registers[SP] -= 1
                self.ram[self.reg[SP]] = self.registers[self.pc]
                self.registers[SP] -= 1
                self.ram[self.reg[SP]] = self.registers[self.fl]
                for j in range(7):
                    self.registers[SP] -= 1
                    self.ram[self.registers[SP]] = self.registers[j]
                self.pc = self.ram[0xF8 + i]

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.registers[i], end='')

        print()

    def set_operands(self):
        self.num_operands = self.ir >> 6
        if self.num_operands == 1:
            self.operand_a = self.ram_read(self.pc + 1)
        elif self.num_operands == 2:
            self.operand_a = self.ram_read(self.pc + 1)
            self.operand_b = self.ram_read(self.pc + 2)

    def alu(self, op, reg_a, reg_b=None):
        """ALU operations."""
        print(op)
        if op == "ADD":
            self.registers[reg_a] += self.registers[reg_b]
        elif op == "SUB":
            self.registers[reg_a] -= self.registers[reg_b]
        elif op == "MUL":
            self.registers[reg_a] *= self.registers[reg_b]
        else:
            raise Exception("Unsupported ALU operation")

        self.registers[reg_a] = self.registers[reg_a] & 0xFF

#################################################################################
#
#                                   Ops
#
#################################################################################
    def ldi(self):
        self.registers[self.operand_a] = self.operand_b

    def prn(self):
        print(self.registers[self.operand_a])

    def hlt(self):
        sys.exit(0)

    def add(self):
        self.alu('ADD', self.operand_a, self.operand_b)

    def mul(self):
        self.alu('MUL', self.operand_a, self.operand_b)

    def st(self):
        self.ram_write(self.reg[self.operand_b], self.reg[self.operand_a])

    def push(self):
        self.registers[SP] -= 1
        self.ram[self.registers[SP]] = self.registers[self.operand_a]
    
    def pop(self):
        if self.registers[SP] > 0xF3:
            print('Error: the stack is empty')
            sys.exit(3)
        else:
            self.registers[self.operand_a] = self.ram[self.registers[SP]]
            self.registers[SP] += 1

    def call(self):
        self.registers[SP] -= 1
        self.ram[self.registers[SP]] = self.pc + 2
        self.jmp()
    
    def jmp(self):
        self.pc = self.registers[self.operand_a]

    def ret(self):
        self.pc = self.ram[self.registers[SP]]

#################################################################################
#
#                                  Emulator run
#
#################################################################################

    def run(self):
        """Run the CPU."""
        running = True
        interrupt_time = time.time() + 60

        timer = True

        while True:
            if timer:
                if time.time() > interrupt_time:
                    self.reg[6] = self.reg[6] | 0b00000001
                    interrupt_time = time.time() + 60
            if self.interrupts_enabled:
                self.check_interrupts()
            self.ir = self.ram_read(self.pc)
            self.set_operands()
            self.invoke_instruction()
            self.move_pc()
                
        pass