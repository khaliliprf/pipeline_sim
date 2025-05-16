from instruction import Instruction
from pipeline import Pipeline
from copy import deepcopy

benchmark_no_hazard_simple = [
    Instruction("ADD", rd="R1", rs="R2", rt="R3"),   # I1: R1 = R2 + R3
    Instruction("SUB", rd="R4", rs="R5", rt="R6"),   # I2: R4 = R5 - R6
    Instruction("AND", rd="R7", rs="R8", rt="R9"),   # I3: R7 = R8 & R9
]


raw_no_forwarding_simple = [
    Instruction("ADD", rd="R1", rs="R2", rt="R3"),       # I1: R1 = R2 + R3
    Instruction("SUB", rd="R4", rs="R1", rt="R5"),       # I2: R4 = R1 - R5 ← وابسته به R1
    Instruction("ADD", rd="R6", rs="R7", rt="R8"),       # I3: مستقل ← اجرا می‌شود بعد از رفع استال
]

flush_test_1 = [
    Instruction("ADD", rd="R1", rs="R2", rt="R3"),       # I1: ADD R1, R2, R3
    Instruction("BEQ", rs="R1", rt="R4", imm=2),         # I2: BEQ R1, R4, +2 (فرض می‌کنیم شرط برقرار نیست ⇒ flush)
    Instruction("SUB", rd="R5", rs="R6", rt="R7"),       # I3: باید flush شود
    Instruction("ADD", rd="R8", rs="R9", rt="R10"),      # I4: باید flush شود
    Instruction("SUB", rd="R11", rs="R12", rt="R13"),    # I5: اولین دستور واقعی بعد از branch
]


#  no branch - testing stall in no forwarding 
p = Pipeline(instructions=deepcopy(flush_test_1), enable_forwarding=True)
p.run()