# # fu.py  –  Functional Unit

# FORMAT_HEADER = (
#     "UNIT     Clks Busy   Fi  Fj  Fk   Qj        Qk        Rj  Rk\n"
#     "----------------------------------------------------------------"
# )

# class FunctionalUnit:
#     def __init__(self, fu_type:str, latency:int):
#         self.type = fu_type
#         self.default_clock = latency
#         self.clear()

#     # ---------- info ----------
#     def __str__(self):
#         return (f"{self.type:<7}{self.clocks:>5} {str(self.busy):<4} "
#                 f"{self.fi or '-':<3} {self.fj or '-':<3} {self.fk or '-':<3} "
#                 f"{repr(self.qj) or '-':<9} {repr(self.qk) or '-':<9} "
#                 f"{self.rj:<3} {self.rk:<3}")

#     def __repr__(self):
#         return self.type

#     # ---------- core ops ----------
#     def clear(self):
#         self.busy=False; self.clocks=self.default_clock
#         self.fi=self.fj=self.fk=None
#         self.qj=self.qk=None; self.rj=self.rk=True
#         self.inst_pc=-1; self.lock=False

#     def issued(self):   # آیا هنوز در حال اجراست؟
#         return self.busy and self.clocks>0

#     def issue(self, inst, reg_status:dict):
#         self.busy=True
#         self.fi, self.fj, self.fk = inst.fi, inst.fj, inst.fk

#         if self.fj and reg_status.get(self.fj):
#             self.qj, self.rj = reg_status[self.fj], False
#         if self.fk and reg_status.get(self.fk):
#             self.qk, self.rk = reg_status[self.fk], False

#     def read_operands(self):
#         self.rj=self.rk=False

#     def execute(self):
#         if self.busy and self.clocks>0:
#             self.clocks -= 1

#     def write_back(self, fu_list):
#         for f in fu_list:
#             if f.qj is self:
#                 f.qj=None; f.rj=True
#             if f.qk is self:
#                 f.qk=None; f.rk=True

# fu.py  – واحد تابعی

# FORMAT_HEADER=("UNIT  Clks Busy Fi Fj Fk   Qj        Qk        Rj Rk\n"
#                "------------------------------------------------------------")

# class FunctionalUnit:
#     def __init__(self, typ, lat):
#         self.type=typ; self.default_clock=lat; self.clear()
#     def __str__(self):
#         return (f"{self.type:<5}{self.clocks:>5} {str(self.busy):<4} "
#                 f"{self.fi or '-':<2} {self.fj or '-':<2} {self.fk or '-':<2} "
#                 f"{repr(self.qj) or '-':<9}{repr(self.qk) or '-':<9}"
#                 f"{self.rj:<2} {self.rk:<2}")
#     def __repr__(self): return self.type
#     # ---- state ops ----
#     def clear(self):
#         self.busy=False; self.clocks=self.default_clock
#         self.fi=self.fj=self.fk=None
#         self.qj=self.qk=None; self.rj=self.rk=True
#         self.inst_pc=-1; self.lock=False
#     def issue(self,inst,regstat):
#         self.busy=True; self.fi,self.fj,self.fk=inst.fi,inst.fj,inst.fk
#         if self.fj and regstat.get(self.fj): self.qj=regstat[self.fj]; self.rj=False
#         if self.fk and regstat.get(self.fk): self.qk=regstat[self.fk]; self.rk=False
#     def read_operands(self): self.rj=self.rk=False
#     def execute(self):       self.clocks-=1 if self.busy and self.clocks>0 else None
#     def release(self,fu_list):
#         for f in fu_list:
#             if f.qj is self: f.qj=None; f.rj=True
#             if f.qk is self: f.qk=None; f.rk=True


# fu.py  –  functional‑unit model

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
