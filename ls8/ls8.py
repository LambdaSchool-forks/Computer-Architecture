#!/usr/bin/env python3

"""Main."""

import sys
from cpu import *

cpu = CPU()

cpu.load()
cpu.run()


memory = [0] * 256
register = [0] * 8   # like variables R0-R7
​
# Load program into memory
address = 0
​
with open(program_filename) as f:
	for line in f:
		line = line.split('#')
		line = line[0].strip()
​
		if line == '':
			continue
​
		memory[address] = int(line)
​
		address += 1