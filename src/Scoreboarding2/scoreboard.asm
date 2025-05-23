.INT   1 1       
.MULT  2 10      
.DIV  1 40     

LD    F6,   34(R2)
LD    F2,   45(R3)
MUL F0,   F2, F4
SUB  F8,   F6, F2
DIV  F10,  F0, F6
ADD  F6,   F8, F2