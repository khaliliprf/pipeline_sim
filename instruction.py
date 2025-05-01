class Instruction:
    def __init__(self, instr_type, rd=None, rs=None, rt=None, imm=None, label=None):
        self.instr_type = instr_type  # نوع دستور مثل ADD، LW، BEQ
        self.rd = rd                  # رجیستر مقصد (خروجی)
        self.rs = rs                  # ورودی اول
        self.rt = rt                  # ورودی دوم
        self.imm = imm                # offset یا مقدار immediate
        self.label = label            # برای jump/branch

        self.stage = "IF"             # مرحله فعلی در پایپ‌لاین
        self.cycle_entered = {}       # چرخه ورود به هر مرحله
        self.finished = False         # آیا کامل اجرا شده یا نه
        self.id = None                # شماره دستور برای جدول

    def __str__(self):
        parts = [self.instr_type]
        if self.rd: parts.append(self.rd)
        if self.rs: parts.append(self.rs)
        if self.rt: parts.append(self.rt)
        if self.imm is not None: parts.append(str(self.imm))
        return " ".join(parts)
