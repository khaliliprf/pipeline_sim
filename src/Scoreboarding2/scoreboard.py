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

    
