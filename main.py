from instruction import Instruction
from pipeline import Pipeline
from copy import deepcopy


# benchmark = [
#     Instruction("ADD", rd="R3", rs="R1", rt="R2"),         # I1: R3 = R1 + R2
#     Instruction("SUB", rd="R5", rs="R3", rt="R4"),         # I2: R5 = R3 - R4 ← RAW با I1
#     Instruction("LW",  rd="R7", rs="R6", imm=4),           # I3: R7 = Mem[R6 + 4]
#     Instruction("SW",  rs="R7", rt="R8", imm=8),           # I4: Mem[R7 + 8] = R8 ← RAW با I3
#     Instruction("BEQ", rs="R5", rt="R1", imm=2),           # I5: If R5 == R1 ← RAW با I2
#     Instruction("ADD", rd="R9", rs="R10", rt="R11"),       # I6: مستقل ← بدون RAW
#     Instruction("SUB", rd="R12", rs="R9", rt="R13"),       # I7: R12 = R9 - R13 ← RAW با I6
#     Instruction("ADD", rd="R14", rs="R12", rt="R15"),      # I8: RAW زنجیره‌ای ← وابسته به I7
#     Instruction("SUB", rd="R16", rs="R14", rt="R17"),      # I9: RAW زنجیره‌ای ← وابسته به I8
#     Instruction("ADD", rd="R18", rs="R20", rt="R21"),      # I10: مستقل ← بدون RAW
# ]


# print("=== WITHOUT FORWARDING ===")
# p1 = Pipeline(instructions=deepcopy(benchmark), enable_forwarding=False)
# p1.run()

# print("\n=== WITH FORWARDING ===")
# p2 = Pipeline(instructions=deepcopy(benchmark), enable_forwarding=True)
# p2.run()


benchmark = [
    Instruction("ADD", rd="R1", rs="R2", rt="R3"),       # I1: ADD R1, R2, R3       ; R1 = R2 + R3
    Instruction("SUB", rd="R4", rs="R1", rt="R5"),       # I2: SUB R4, R1, R5       ; R4 = R1 - R5
    Instruction("BEQ", rs="R4", rt="R6", imm=2),         # I3: BEQ R4, R6, +2       ; if R4 == R6 → PC += 2
    Instruction("ADD", rd="R7", rs="R8", rt="R9"),       # I4: ADD R7, R8, R9       ; R7 = R8 + R9
    Instruction("SUB", rd="R10", rs="R11", rt="R12"),    # I5: SUB R10, R11, R12    ; R10 = R11 - R12
]


print("=== WITH BRANCH FLUSHING ===")
p = Pipeline(instructions=deepcopy(benchmark), enable_forwarding=False)
p.run(max_cycles=13)