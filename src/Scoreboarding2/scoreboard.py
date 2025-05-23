# # scoreboard.py  –  Scoreboard simulator

# from decode import decode
# from fu import FunctionalUnit, FORMAT_HEADER

# ASM_FILE = 'scoreboard.asm'

# # ---------------- parser -----------------
# class ScoreboardParser:
#     def __init__(self, asm_file): self.sb, self.asm = Scoreboard(), asm_file

#     def _parse_fu(self, toks):
#         t = toks[0][1:].upper(); n=int(toks[1]); lat=int(toks[2])
#         for _ in range(n):
#             fu = FunctionalUnit(t, lat)
#             self.sb.units.append(fu)

#     def _parse_inst(self, toks):
#         ins=decode(' '.join(toks))
#         self.sb.instructions.append(ins)

#     def _parse_line(self, line):
#         if not line or line.startswith('#'): return
#         tk=line.split()
#         (self._parse_fu if tk[0].startswith('.') else self._parse_inst)(tk)

#     @staticmethod
#     def scoreboard_for_asm(path):
#         p=ScoreboardParser(path)
#         with open(path) as f:
#             for ln in f: p._parse_line(ln.strip())
#         return p.sb

# # ---------------- scoreboard core -------------
# class Scoreboard:
#     def __init__(self):
#         self.units, self.instructions = [], []
#         self.reg_status = {}; self.pc=0; self.clock=1

#     def done(self):
#         return self.pc>=len(self.instructions) and all(not fu.busy for fu in self.units)

#     # ---------- helpers ----------
#     def can_issue(self, inst, fu):
#         if not inst or fu.busy or inst.op!=fu.type: return False
#         return not (inst.fi and inst.fi in self.reg_status)

#     def can_read(self, fu):     return fu.busy and fu.rj and fu.rk
#     def can_exec(self, fu):     return fu.busy and not fu.rj and not fu.rk and fu.clocks>0
#     # def can_wb(self, fu):
#     #     if fu.fi is None: return True
#     #     return all((other.qj!=fu and other.qk!=fu) for other in self.units)

#     # ---------- pipeline stages ----------
#     def issue(self, inst, fu):
#         fu.issue(inst,self.reg_status)
#         if inst.fi: self.reg_status[inst.fi]=fu
#         inst.issue=self.clock; fu.inst_pc=self.pc; self.pc+=1

#     def read(self,fu):
#         fu.read_operands()
#         self.instructions[fu.inst_pc].read_ops=self.clock

#     # def exec(self,fu):
#     #     fu.execute()
#     #     if fu.clocks==0:
#     #         self.instructions[fu.inst_pc].ex_cmplt=self.clock
#     def exec(self, fu):
#         fu.execute()

#         # اگر اجرای FU تمام شد (clocks == 0)
#         if fu.clocks == 0:
#             self.instructions[fu.inst_pc].ex_cmplt = self.clock

#             # ⬇️  نتیجه را روی باس پخش کن؛ دیگران آزاد می‌شوند
#             for other in self.units:
#                 if other.qj is fu:
#                     other.qj = None
#                     other.rj = True
#                 if other.qk is fu:
#                     other.qk = None
#                     other.rk = True


#     def wb(self,fu):
#         self.instructions[fu.inst_pc].write_res=self.clock
#         fu.write_back(self.units)
#         if fu.fi in self.reg_status: del self.reg_status[fu.fi]
#         fu.clear()

#     # ---------- clock tick ----------
#     def can_wb(self, fu):
#         # اگر دستور مقصد ثبات ندارد (HALT/NOP/Store) مانعی نیست
#         if fu.fi is None:
#             return True
#         for other in self.units:
#             if other.qj == fu or other.qk == fu:
#                 return False
#         return True

#     def tick(self):
#         # 1. unlock
#         for fu in self.units:
#             fu.lock = False

#         nxt = self.instructions[self.pc] if self.pc < len(self.instructions) else None

#         # 2. Issue / RO / EX
#         for fu in self.units:
#             if not fu.lock and self.can_issue(nxt, fu):
#                 self.issue(nxt, fu); fu.lock = True
#             elif not fu.lock and self.can_read(fu):
#                 self.read(fu); fu.lock = True
#             elif not fu.lock and self.can_exec(fu):
#                 self.exec(fu); fu.lock = True

#         # 3. Write‑Back
#         for fu in self.units:
#             if fu.busy and fu.clocks == 0 and self.can_wb(fu):
#                 self.wb(fu)

#         self.clock += 1


# # ---------------- main -----------------
# if __name__ == '__main__':
#     sb = ScoreboardParser.scoreboard_for_asm(ASM_FILE)

#     while not sb.done():
#         sb.tick()

#     print("                               Read      Execute   Write")
#     print("                        Issued  Operands  Complete  Result")
#     print("                    ----------------------------------------")
#     for ins in sb.instructions:
#         print(str(ins))

# scoreboard.py

# from decode import decode
# from fu import FunctionalUnit, FORMAT_HEADER
# import matplotlib.pyplot as plt
# import matplotlib.patches as mpatches
# from tabulate import tabulate

# ASM_FILE='scoreboard.asm'

# # ---------- parser ----------
# class ScoreboardParser:
#     def __init__(self,p): self.sb,self.asm=Scoreboard(),p
#     def _fu(self,t):
#         typ=t[0][1:].upper(); n,lat=int(t[1]),int(t[2])
#         for _ in range(n): self.sb.units.append(FunctionalUnit(typ,lat))
#     def _inst(self,t): self.sb.instructions.append(decode(' '.join(t)))
#     def _line(self,l):
#         if not l or l.startswith('#'): return
#         tk=l.split(); (self._fu if tk[0].startswith('.') else self._inst)(tk)
#     @staticmethod
#     def build(path):
#         p=ScoreboardParser(path)
#         with open(path) as f:
#             for ln in f: p._line(ln.strip())
#         return p.sb

# # ---------- scoreboard ----------
# class Scoreboard:
#     def __init__(self):
#         self.units=[]; self.instructions=[]; self.reg_status={}
#         self.pc=0; self.clock=1
#     def done(self): return self.pc>=len(self.instructions) and all(not f.busy for f in self.units)

#     # --- helpers ---
#     def _can_issue(self,inst,fu):
#         if not inst or fu.busy or inst.op!=fu.type: return False
#         return not (inst.fi and inst.fi in self.reg_status)
#     def _can_read(self,fu): return fu.busy and fu.rj and fu.rk
#     def _can_exec(self,fu): return fu.busy and not fu.rj and not fu.rk and fu.clocks>0
#     def _can_wb(self,fu):
#         if fu.fi is None: return True          # store / nop
#         # اگر مصرف‌کننده‌ای هنوز اپراند را نخوانده مانع شو
#         for other in self.units:
#             if not other.busy: continue
#             if (other.fj==fu.fi and other.rj) or (other.fk==fu.fi and other.rk):
#                 return False
#         # فاصلهٔ یک کلاک: WB فقط اگر حداقل یک سیکل از ex_cmplt گذشته
#         return self.clock > self.instructions[fu.inst_pc].ex_cmplt

#     # --- pipeline stages ---
#     def _issue(self,inst,fu):
#         fu.issue(inst,self.reg_status)
#         if inst.fi: self.reg_status[inst.fi]=fu
#         inst.issue=self.clock; fu.inst_pc=self.pc; self.pc+=1
#     def _read(self,fu):
#         fu.read_operands(); self.instructions[fu.inst_pc].read_ops=self.clock
#     def _exec(self,fu):
#         fu.execute()
#         if fu.clocks==0:
#             self.instructions[fu.inst_pc].ex_cmplt=self.clock
#             fu.release(self.units)   # پخش نتیجه برای RAW
#     def _wb(self,fu):
#         self.instructions[fu.inst_pc].write_res=self.clock
#         if fu.fi in self.reg_status: del self.reg_status[fu.fi]
#         fu.clear()

#     # --- tick ---
#     def tick(self):
#         for fu in self.units: fu.lock=False
#         cur=self.instructions[self.pc] if self.pc<len(self.instructions) else None
#         for fu in self.units:
#             if not fu.lock and self._can_issue(cur,fu): self._issue(cur,fu); fu.lock=True
#             elif not fu.lock and self._can_read(fu):    self._read(fu);  fu.lock=True
#             elif not fu.lock and self._can_exec(fu):    self._exec(fu);  fu.lock=True
#         for fu in self.units:
#             if fu.busy and fu.clocks==0 and self._can_wb(fu): self._wb(fu)
#         self.clock+=1

# # ---------- run ----------
# if __name__=='__main__':
#     sb=ScoreboardParser.build(ASM_FILE)
#     while not sb.done(): sb.tick()

#     # ---- جدول متنی ----
#     head="Instr                 IS   RO  EX‑Cmp  WB"
#     print(head); print('-'*len(head))
#     for ins in sb.instructions: print(ins)

#     # ---- نمودار ----
#     colors={"IS":"tab:blue","RO":"tab:orange","EX":"tab:green","WB":"tab:red"}
#     fig,ax=plt.subplots(figsize=(10,0.5*len(sb.instructions)+1))
#     y=0
#     # for ins in sb.instructions:
#     #     phases=[("IS",ins.issue,ins.issue),
#     #             ("RO",ins.read_ops,ins.read_ops),
#     #             ("EX",ins.read_ops,ins.ex_cmplt),
#     #             ("WB",ins.write_res,ins.write_res)]
#     #     for ph,s,e in phases:
#     #         ax.broken_barh([(s,e-s+1)],(y,0.8),facecolors=colors[ph])
#     #     ax.text(0,y+0.4,ins.text,va='center',ha='left')
#     #     y+=1
#     hdr = ["Instr","IS","RO","EX‑Cmp","WB"]
#     rows = [[i.text,i.issue,i.read_ops,i.ex_cmplt,i.write_res] for i in sb.instructions]
#     print(tabulate(rows, headers=hdr, tablefmt="github"))

#     #  visual output
#     handles = [mpatches.Patch(color=c) for c in colors.values()]
#     labels  = list(colors.keys())
#     ax.legend(handles, labels, loc='upper right')



# scoreboard.py  –  scoreboarding simulator with matplotlib output

from decode import decode
from fu      import FunctionalUnit, FORMAT_HEADER
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

ASM_FILE = 'scoreboard.asm'      # ← change if needed

# ---------- parser ----------
class ScoreboardParser:
    def __init__(self, path): self.sb, self.path = Scoreboard(), path
    def _fu(self,tok):
        typ=tok[0][1:].upper(); n,lat = int(tok[1]), int(tok[2])
        for _ in range(n): self.sb.units.append(FunctionalUnit(typ,lat))
    def _inst(self,tok): self.sb.instructions.append(decode(' '.join(tok)))
    def _line(self,l):
        if not l or l.startswith('#'): return
        tok=l.split()
        (self._fu if tok[0].startswith('.') else self._inst)(tok)
    @staticmethod
    def build(path):
        p=ScoreboardParser(path)
        with open(path) as f:
            for ln in f: p._line(ln.strip())
        return p.sb

# ---------- scoreboard ----------
class Scoreboard:
    def __init__(self):
        self.units=[]; self.instructions=[]; self.reg_status={}
        self.pc=0; self.clock=1

    def done(self): return self.pc>=len(self.instructions) and all(not f.busy for f in self.units)

    # ------ guards ------
    def _can_issue(self,inst,fu):
        if not inst or fu.busy or inst.op!=fu.type: return False
        return not (inst.fi and inst.fi in self.reg_status)          # WAW
    def _can_read(self,fu): return fu.busy and fu.rj and fu.rk
    def _can_exec(self,fu): return fu.busy and not fu.rj and not fu.rk and fu.clocks>0
    # def _can_wb(self,fu):
    #     if fu.fi is None: return True
    #     # جلوگیری از WAR
    #     for o in self.units:
    #         if not o.busy: continue
    #         if (o.fj==fu.fi and o.rj) or (o.fk==fu.fi and o.rk):
    #             return False
    #     # فاصلهٔ حداقل یک سیکل
    #     return self.clock > self.instructions[fu.inst_pc].ex_cmplt

    def _can_wb(self, fu):
        """جلوگیری از WAR مطابق پروتکل اصلی"""
        if fu.fi is None:          # دستور مقصد‌‑ندار (Store, ...)
            return True

        for other in self.units:
            if not other.busy or other is fu:
                continue

            waiting_for_fi = (
                (other.fj == fu.fi and other.rj) or   # هنوز Fj را نگرفته
                (other.fk == fu.fi and other.rk)      # هنوز Fk را نگرفته
            )
            if waiting_for_fi:
                return False          # WAR هنوز برقرار است

        # فاصلهٔ حداقل یک سیکل بین پایان EX و WB
        return self.clock > self.instructions[fu.inst_pc].ex_cmplt


    # ------ stages ------
    def _issue(self,inst,fu):
        fu.issue(inst,self.reg_status)
        if inst.fi: self.reg_status[inst.fi]=fu
        inst.issue=self.clock; fu.inst_pc=self.pc; self.pc+=1
    def _read(self,fu):
        fu.read_operands(); self.instructions[fu.inst_pc].read_ops=self.clock
    def _exec(self,fu):
        fu.execute()
        if fu.clocks==0:
            self.instructions[fu.inst_pc].ex_cmplt=self.clock
            # RAW: تا پایان WB آزاد نمی‌کنیم
    def _wb(self,fu):
        # پخش نتیجه و آزادسازی
        fu.release(self.units)
        self.instructions[fu.inst_pc].write_res=self.clock
        if fu.fi in self.reg_status: del self.reg_status[fu.fi]
        fu.clear()

    # ------ clock tick ------
    def tick(self):
        for fu in self.units: fu.lock=False
        nxt=self.instructions[self.pc] if self.pc<len(self.instructions) else None
        for fu in self.units:
            if not fu.lock and self._can_issue(nxt,fu): self._issue(nxt,fu); fu.lock=True
            elif not fu.lock and self._can_read(fu):    self._read(fu);   fu.lock=True
            elif not fu.lock and self._can_exec(fu):    self._exec(fu);   fu.lock=True
        for fu in self.units:
            if fu.busy and fu.clocks==0 and self._can_wb(fu): self._wb(fu)
        self.clock+=1

# ---------- run ----------
if __name__ == '__main__':
    sb = ScoreboardParser.build(ASM_FILE)
    while not sb.done(): sb.tick()

    # ---- aligned console table ----
    print(f"{'Instr':<22}{'IS':>6}{'RO':>6}{'EX‑Cmp':>9}{'WB':>6}")
    print('-'*49)
    for ins in sb.instructions: print(ins)

    # ---- matplotlib Gantt ----
    colors={"IS":"tab:blue","RO":"tab:orange","EX":"tab:green","WB":"tab:red"}
    fig,ax=plt.subplots(figsize=(10,0.6*len(sb.instructions)+1))
    y=0
    for ins in sb.instructions:
        seg=[("IS",ins.issue,ins.issue),
             ("RO",ins.read_ops,ins.read_ops),
             ("EX",ins.read_ops,ins.ex_cmplt),
             ("WB",ins.write_res,ins.write_res)]
        for p,s,e in seg:
            ax.broken_barh([(s,e-s+1)],(y,0.8),facecolors=colors[p])
        ax.text(0,y+0.4,ins.text,va='center',ha='left')
        y+=1
    ax.set_ylim(0,y); ax.set_xlim(0,max(i.write_res for i in sb.instructions)+3)
    ax.set_xlabel("cycle"); ax.set_yticks([]); ax.grid(True,axis='x')
    handles=[mpatches.Patch(color=c) for c in colors.values()]
    labels =list(colors.keys())
    ax.legend(handles,labels,loc='upper right')
    plt.tight_layout()
    os.makedirs("stats", exist_ok=True)

# ➋ مسیرِ مقصد را بساز
    out_path = os.path.join("stats", "scoreboard_timeline.png")

    plt.savefig(out_path, dpi=150)

    
