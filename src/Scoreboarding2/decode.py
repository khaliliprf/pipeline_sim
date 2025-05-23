import re
class Instruction:
    def __init__(self, txt, op, dst=None, src1=None, src2=None, imm=None):
        self.issue=self.read_ops=self.ex_cmplt=self.write_res=-1
        self.op,self.fi,self.fj,self.fk,self.imm=op,dst,src1,src2,imm
        self.text=txt
    def __str__(self):
        return f"{self.text:<20}{self.issue:>6}{self.read_ops:>6}{self.ex_cmplt:>9}{self.write_res:>7}"

def toks(s): return [t for t in re.split(r'[,\s]+',s.strip()) if t]

def _li(l):  t=toks(l); return Instruction(l,"INT",dst=t[1],imm=int(t[2],0))
def _ld(l):  t=toks(l); off,base=re.match(r'(-?\d+)\(([RF]\d+)\)',t[2]).groups();return Instruction(l,"INT",dst=t[1],src1=base,imm=int(off))
def _st(l):  t=toks(l); off,base=re.match(r'(-?\d+)\(([RF]\d+)\)',t[2]).groups();return Instruction(l,"INT",src1=t[1],src2=base,imm=int(off))
def _r (l):  t=toks(l); return Instruction(l,"INT",dst=t[1],src1=t[2],src2=t[3])
def _sh(l):  t=toks(l); return Instruction(l,"INT",dst=t[1],src1=t[2],imm=int(t[3],0))
def _nt(l):  t=toks(l); return Instruction(l,"INT",dst=t[1],src1=t[2])
def _mul(l): t=toks(l); return Instruction(l,"MULT",dst=t[1],src1=t[2],src2=t[3])
def _div(l): t=toks(l); return Instruction(l,"DIV" ,dst=t[1],src1=t[2],src2=t[3])

DECODER={"LI":_li,"LD":_ld,"ST":_st,
         "ADD":_r,"SUB":_r,"AND":_r,"OR":_r,"XOR":_r,
         "SHL":_sh,"SHR":_sh,"NOT":_nt,
         "MUL":_mul,"DIV":_div}

def decode(line:str)->Instruction:
    op=toks(line)[0].upper()
    if op not in DECODER: raise ValueError(op)
    return DECODER[op](line)
