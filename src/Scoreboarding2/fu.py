FORMAT_HEADER = ("UNIT  Clks Busy Fi Fj Fk   Qj        Qk        Rj Rk\n"
                 "------------------------------------------------------------")

class FunctionalUnit:
    def __init__(self, typ:str, latency:int):
        self.type = typ
        self.default_clock = latency
        self.clear()

    # pretty‑print (for debug / future use)
    def __str__(self):
        return (f"{self.type:<5}{self.clocks:>5} {str(self.busy):<4} "
                f"{self.fi or '-':<2} {self.fj or '-':<2} {self.fk or '-':<2} "
                f"{repr(self.qj) or '-':<9}{repr(self.qk) or '-':<9}"
                f"{self.rj:<2} {self.rk:<2}")
    def __repr__(self): return self.type

    # ---------- state ops ----------
    def clear(self):
        self.busy=False; self.clocks=self.default_clock
        self.fi=self.fj=self.fk=None
        self.qj=self.qk=None; self.rj=self.rk=True
        self.inst_pc=-1; self.lock=False        # lock used by main loop

    def issue(self, inst, regstat:dict):
        self.busy=True
        self.fi,self.fj,self.fk = inst.fi,inst.fj,inst.fk
        if self.fj and regstat.get(self.fj): self.qj=regstat[self.fj]; self.rj=False
        if self.fk and regstat.get(self.fk): self.qk=regstat[self.fk]; self.rk=False

    def read_operands(self): self.rj=self.rk=False
    def execute(self):       self.clocks -= 1 if self.busy and self.clocks>0 else None

    # آزاد کردن مصرف‌کننده‌هایی که منتظر این FU هستند
    def release(self, fu_list):
        for f in fu_list:
            if f.qj is self: f.qj=None; f.rj=True
            if f.qk is self: f.qk=None; f.rk=True
