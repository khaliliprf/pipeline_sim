# ------------------ رسم نمودار + سه جدول دریک ردیف ------------------
import matplotlib.pyplot as plt, matplotlib.patches as mpatches
from collections import defaultdict
import os

# ------------------ رسم نمودار + سه جدول دریک ردیف ------------------
import matplotlib.pyplot as plt, matplotlib.patches as mpatches
from collections import defaultdict
import os

def draw_scoreboard_timeline_grid(sb, console_lines):
    instrs = sb.instructions
    fus    = sb.units

    fig = plt.figure(figsize=(15, 0.75*len(instrs)+4))
    gs  = fig.add_gridspec(2, 3, height_ratios=[0.55, 0.45], hspace=0.4)

    # ── 1) Timeline ───────────────────────────────────────────────────
    ax_tl = fig.add_subplot(gs[0, :])          # ردیف۰، سه ستون
    colors = {"IS":"tab:blue", "RO":"tab:orange",
              "EX":"tab:green", "WB":"tab:red"}

    for idx, ins in enumerate(instrs):
        segs = [("IS", ins.issue-1, ins.issue),
                ("RO", ins.read_ops-1, ins.read_ops),
                ("EX", ins.read_ops,  ins.ex_cmplt),
                ("WB", ins.write_res-1, ins.write_res)]
        for p,s,e in segs:
            ax_tl.broken_barh([(s, e-s)], (idx, .7),
                              facecolors=colors[p], edgecolor='black', lw=.6)
    ax_tl.set_yticks([i+.35 for i in range(len(instrs))])
    ax_tl.set_yticklabels([f"I{i+1}" for i in range(len(instrs))])
    xmax = max(i.write_res for i in instrs)+1
    ax_tl.set_xlim(0, xmax); ax_tl.set_xticks(range(0, xmax+1))
    ax_tl.set_xlabel("cycle")
    ax_tl.set_title("Scoreboard Pipeline Execution Timeline")
    ax_tl.grid(True, axis='x', ls='--', color='lightgrey', lw=.7)
    ax_tl.legend([mpatches.Patch(color=c) for c in colors.values()],
                 list(colors.keys()), loc='upper right')

    # ── 2) Instruction Map ────────────────────────────────────────────
    ax_instr = fig.add_subplot(gs[1, 0]); ax_instr.axis('off')
    instr_tbl = [[f"I{i+1}", ins.text] for i,ins in enumerate(instrs)]
    ax_instr.table(cellText=instr_tbl,
                   colLabels=["ID","Instruction"],
                   cellLoc='left', loc='center')
    ax_instr.set_title("Instruction Map")

    # ── 3) Functional Units ───────────────────────────────────────────
    ax_fu = fig.add_subplot(gs[1, 1]); ax_fu.axis('off')
    info = defaultdict(list)
    for fu in fus: info[fu.type].append(fu.default_clock)
    fu_tbl = [[typ, len(lst), lst[0]] for typ,lst in info.items()]
    ax_fu.table(cellText=fu_tbl,
                colLabels=["FU Type","Count","Latency"],
                loc='center')
    ax_fu.set_title("Functional Units")

    # ── 4) Console Timing Table ───────────────────────────────────────
    ax_cons = fig.add_subplot(gs[1, 2]); ax_cons.axis('off')
    ax_cons.text(0, 1, "\n".join(console_lines),
                 va='top', fontfamily='monospace', fontsize=9)
    ax_cons.set_title("Console Timing Table", loc='left', pad=2)

    # ── Save ──────────────────────────────────────────────────────────
    plt.tight_layout()
    os.makedirs("stats", exist_ok=True)
    out_path = "stats/scoreboard_grid.png"
    plt.savefig(out_path, dpi=150)
    print(f"saved → {out_path}")

# ----------- فراخوانی -------------
# console_lines همان رشته‌هایی است که پیش از این در کنسول چاپ می‌کنی


# ---------- constants ----------
FORMAT_HEADER = ("UNIT  Clks Busy Fi Fj Fk   Qj        Qk        Rj Rk\n"
                 "------------------------------------------------------------")

# ---------- functional unit ----------
class FunctionalUnit:
    def __init__(self, typ: str, latency: int):
        self.type = typ
        self.default_clock = latency
        self.clear()

    def __str__(self):
        return (f"{self.type:<5}{self.clocks:>5} {str(self.busy):<4} "
                f"{self.fi or '-':<2} {self.fj or '-':<2} {self.fk or '-':<2} "
                f"{repr(self.qj) or '-':<9}{repr(self.qk) or '-':<9}"
                f"{self.rj:<2} {self.rk:<2}")
    def __repr__(self): return self.type

    # ---------- state ops ----------
    def clear(self):
        self.busy = False
        self.clocks = self.default_clock
        self.fi = self.fj = self.fk = None
        self.qj = self.qk = None      # تولیدکنندهٔ عملوند
        self.rj = self.rk = True      # آماده‌بودن عملوند‌ها
        self.inst_pc = -1
        self.lock = False             # برای جلوگیری از دوباره‌کاری در یک تیک

    def issue(self, inst, regstat: dict):
        self.busy = True
        self.fi, self.fj, self.fk = inst.fi, inst.fj, inst.fk
        if self.fj and regstat.get(self.fj):
            self.qj = regstat[self.fj]
            self.rj = False           # منتظر Fj
        if self.fk and regstat.get(self.fk):
            self.qk = regstat[self.fk]
            self.rk = False           # منتظر Fk

    def read_operands(self):
        # پس از خواندن، در اسکوربورد اصلی Rj/Rk را FALSE می‌گذارند
        self.rj = self.rk = False

    def execute(self):
        if self.busy and self.clocks > 0:
            self.clocks -= 1
            

    # آزاد کردن مصرف‌کننده‌هایی که منتظر این FU هستند
    def release(self, fu_list):
        for f in fu_list:
            if f.qj is self: f.qj = None; f.rj = True
            if f.qk is self: f.qk = None; f.rk = True

# ---------- decoder & helpers ----------
import re
class Instruction:
    def __init__(self, txt, op, dst=None, src1=None, src2=None, imm=None):
        self.issue = self.read_ops = self.ex_cmplt = self.write_res = -1
        self.op, self.fi, self.fj, self.fk, self.imm = op, dst, src1, src2, imm
        self.text = txt
    def __str__(self):
        return (f"{self.text:<20}{self.issue:>6}{self.read_ops:>6}"
                f"{self.ex_cmplt:>9}{self.write_res:>7}")

def toks(s): return [t for t in re.split(r'[,\s]+', s.strip()) if t]

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

# ---------- parser ----------
class ScoreboardParser:
    def __init__(self, path):
        self.sb, self.path = Scoreboard(), path
    def _fu(self, tok):
        typ = tok[0][1:].upper(); n, lat = int(tok[1]), int(tok[2])
        for _ in range(n): self.sb.units.append(FunctionalUnit(typ, lat))
    def _inst(self, tok):
        self.sb.instructions.append(decode(' '.join(tok)))
    def _line(self, l):
        if not l or l.startswith('#'): return
        tok = l.split()
        (self._fu if tok[0].startswith('.') else self._inst)(tok)
    @staticmethod
    def build(path):
        p = ScoreboardParser(path)
        with open(path) as f:
            for ln in f: p._line(ln.strip())
        return p.sb

# ---------- scoreboard core ----------
class Scoreboard:
    def __init__(self):
        self.units=[]; self.instructions=[]; self.reg_status={}
        self.pc=0; self.clock=1

    def done(self):
        return self.pc >= len(self.instructions) and all(not f.busy for f in self.units)

    # ------ guards ------
    def _can_issue(self, inst, fu):
        if not inst or fu.busy or inst.op != fu.type:
            return False
        return not (inst.fi and inst.fi in self.reg_status)    # WAW

    def _can_read(self, fu):
        return fu.busy and fu.rj and fu.rk

    def _can_exec(self, fu):
        return fu.busy and not fu.rj and not fu.rk and fu.clocks > 0
    def _can_wb(self, fu):
        if fu.fi is None:
            return True                        # دستور بدون مقصد ثباتی

        for other in self.units:
            if other is fu or not other.busy:
                continue

            same_reg = (other.fj == fu.fi) or (other.fk == fu.fi)

            # هنوز عملوند را نگرفته
            if same_reg and ((other.fj == fu.fi and other.rj) or
                             (other.fk == fu.fi and other.rk)):
                return False

            # همین کلاک عملوند را خوانده → یک سیکل فاصله لازم
            if same_reg and \
               self.instructions[other.inst_pc].read_ops == self.clock:
                return False

        return self.clock > self.instructions[fu.inst_pc].ex_cmplt


    # def _can_wb(self, fu):
    #     """
    #     اجازهٔ نوشتن روی CDB وقتی است که:
    #     ۱) اگر ثبات مقصد وجود دارد، هیچ دستورِ «منتظری» هنوز عملوندش را نخوانده باشد
    #        (read_ops == -1 ⇒ مرحلهٔ RO انجام نشده است)
    #     ۲) حداقل یک سیکل بعد از پایان EX باشد
    #     """
    #     if fu.fi is None:      # دستور مقصد‑ندار (Store و …)
    #         return True

    #     for other in self.units:
    #         if other is fu or not other.busy:
    #             continue
    #         inst_o = self.instructions[other.inst_pc]
    #         waiting_for_fi = (
    #             (inst_o.fj == fu.fi and inst_o.read_ops == -1) or
    #             (inst_o.fk == fu.fi and inst_o.read_ops == -1)
    #         )
    #         if waiting_for_fi:
    #             return False   # WAR هنوز برقرار است

    #     # فاصلهٔ حداقل یک سیکل بین EX و WB
    #     return self.clock > self.instructions[fu.inst_pc].ex_cmplt

    # ------ stages ------
    def _issue(self, inst, fu):
        fu.issue(inst, self.reg_status)
        if inst.fi: self.reg_status[inst.fi] = fu
        inst.issue = self.clock
        fu.inst_pc = self.pc
        self.pc += 1

    def _read(self, fu):
        fu.read_operands()
        self.instructions[fu.inst_pc].read_ops = self.clock

    def _exec(self, fu):
        fu.execute()
        if fu.clocks == 0:
            self.instructions[fu.inst_pc].ex_cmplt = self.clock
            # RAW: نتیجه تا WB روی CDB منتشر نمی‌شود

    def _wb(self, fu):
        # انتشار نتیجه و آزادسازی مصرف‌کننده‌ها
        fu.release(self.units)
        self.instructions[fu.inst_pc].write_res = self.clock
        if fu.fi in self.reg_status:
            del self.reg_status[fu.fi]
        fu.clear()

    # ------ clock tick ------
    def tick(self):
        # فاز ۱: Issue / Read / Execute
        for fu in self.units: fu.lock = False
        nxt = self.instructions[self.pc] if self.pc < len(self.instructions) else None
        for fu in self.units:
            if not fu.lock and self._can_issue(nxt, fu):
                self._issue(nxt, fu); fu.lock = True
            elif not fu.lock and self._can_read(fu):
                self._read(fu); fu.lock = True
            elif not fu.lock and self._can_exec(fu):
                self._exec(fu); fu.lock = True

        # فاز ۲: Write‑Back (CDB)
        for fu in self.units:
            if fu.busy and fu.clocks == 0 and self._can_wb(fu):
                self._wb(fu)

        self.clock += 1

# ---------- run ----------
if __name__ == '__main__':
    import os, matplotlib.pyplot as plt, matplotlib.patches as mpatches

    ASM_FILE = 'scoreboard.asm'      # ← change if needed
    sb = ScoreboardParser.build(ASM_FILE)
    while not sb.done():
        sb.tick()

    # ---- aligned console table ----
    print(f"{'Instr':<20}{'IS':>6}{'RO':>7}{'EX‑Cmp':>10}{'WB':>6}")
    print('-'*49)
    for ins in sb.instructions:
        print(ins)

    # ---- matplotlib Gantt ----
console_lines = [
    "Instr                     IS    RO   EX‑Cmp    WB",
    "-------------------------------------------------",
    *[str(i) for i in sb.instructions]
]
draw_scoreboard_timeline_grid(sb, console_lines)


