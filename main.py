from instruction import Instruction
from pipeline import Pipeline
from copy import deepcopy

# benchmark = [
#     Instruction("ADD", rd="R1", rs="R2", rt="R3"),        # I1: ADD R1, R2, R3        ; R1 = R2 + R3
#     Instruction("SUB", rd="R4", rs="R1", rt="R5"),        # I2: SUB R4, R1, R5        ; R4 = R1 - R5
#     Instruction("ADD", rd="R6", rs="R4", rt="R7"),        # I3: ADD R6, R4, R7        ; R6 = R4 + R7
#     Instruction("SUB", rd="R8", rs="R6", rt="R9"),        # I4: SUB R8, R6, R9        ; R8 = R6 - R9
#     Instruction("ADD", rd="R10", rs="R8", rt="R11"),      # I5: ADD R10, R8, R11      ; R10 = R8 + R11
#     Instruction("SUB", rd="R12", rs="R10", rt="R13"),     # I6: SUB R12, R10, R13     ; R12 = R10 - R13
#     Instruction("ADD", rd="R14", rs="R12", rt="R15"),     # I7: ADD R14, R12, R15     ; R14 = R12 + R15
#     Instruction("SUB", rd="R16", rs="R14", rt="R17"),     # I8: SUB R16, R14, R17     ; R16 = R14 - R17
#     Instruction("ADD", rd="R18", rs="R16", rt="R19"),     # I9: ADD R18, R16, R19     ; R18 = R16 + R19
#     Instruction("SUB", rd="R20", rs="R18", rt="R21"),     # I10: SUB R20, R18, R21    ; R20 = R18 - R21
# ]

# #  no branch - testing stall in no forwarding 
# p1 = Pipeline(instructions=deepcopy(benchmark), enable_forwarding=False)
# p1.run()

# # no branch - test stall in forwarding
# p2 = Pipeline(instructions=deepcopy(benchmark), enable_forwarding=True)
# p2.run()


# benchmark = [
#     Instruction("ADD", rd="R1", rs="R2", rt="R3"),       # I1: R1 = R2 + R3
#     Instruction("SUB", rd="R4", rs="R1", rt="R5"),       # I2: R4 = R1 - R5 (RAW با I1)
#     Instruction("BEQ", rs="R4", rt="R6", imm=2),         # I3: BEQ R4, R6, +2 ← انشعاب و flush
#     Instruction("ADD", rd="R7", rs="R8", rt="R9"),       # I4: باید flush شود
#     Instruction("SUB", rd="R10", rs="R11", rt="R12"),    # I5: اولین دستور واقعی بعد از flush
#     Instruction("ADD", rd="R13", rs="R10", rt="R14"),    # I6: وابسته به I5
# ]

# # with branch - no forwarding 
# p1 = Pipeline(instructions=deepcopy(benchmark), enable_forwarding=False)
# p1.run()

# # with branch - forwarding
# p2 = Pipeline(instructions=deepcopy(benchmark), enable_forwarding=True)
# p2.run()


benchmark = [
    Instruction("ADD", rd="R1", rs="R2", rt="R3"),       # I1: R1 = R2 + R3
    Instruction("SUB", rd="R4", rs="R1", rt="R5"),       # I2: R4 = R1 - R5 ← RAW با I1
    Instruction("LW",  rd="R6", rs="R4", imm=8),         # I3: R6 = Mem[R4 + 8] ← RAW با I2
    Instruction("ADD", rd="R7", rs="R6", rt="R8"),       # I4: R7 = R6 + R8 ← RAW با I3 (مهم: فوروارد در LW)
    Instruction("BEQ", rs="R7", rt="R9", imm=2),         # I5: BEQ R7, R9, +2 → باید Flush بده
    Instruction("ADD", rd="R10", rs="R11", rt="R12"),    # I6: Flush بشه (به خاطر BEQ)
    Instruction("SUB", rd="R13", rs="R14", rt="R15"),    # I7: Flush بشه (به خاطر BEQ)
    Instruction("ADD", rd="R16", rs="R17", rt="R18"),    # I8: مستقل
    Instruction("SUB", rd="R19", rs="R16", rt="R20"),    # I9: RAW با I8
    Instruction("ADD", rd="R21", rs="R22", rt="R23"),    # I10: مستقل
]

# final test 
# #  no forwarding 
p1 = Pipeline(instructions=deepcopy(benchmark), enable_forwarding=False)
p1.run()

# #  forwarding
p2 = Pipeline(instructions=deepcopy(benchmark), enable_forwarding=True)
p2.run()