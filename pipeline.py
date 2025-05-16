# pipeline.py

from utils import branch_condition_taken, export_simulation_image

class Pipeline:
    def __init__(self, instructions,enable_forwarding=False):
        self.instructions = instructions
        self.input_instructions_count = len(instructions)
        self.stall_count = 0
        self.enable_forwarding = enable_forwarding
        self.flush_count = 0
        self.forward_count = 0
        self.structural_stalls = 0

        for idx, instr in enumerate(self.instructions):
            instr.id = idx + 1  # شماره‌گذاری برای I1, I2, ...

        self.clock = 0
        self.pipeline_registers = {
            "IF": [],
            "ID": [],
            "EX": [],
            "MEM": [],
            "WB": []
        }
        self.completed_instructions = []
        self.pipeline_matrix = {}  # {instr: {cycle: stage}}
    def log_pipeline_stage(self, instr, stage):
        if instr not in self.pipeline_matrix:
            self.pipeline_matrix[instr] = {}
        self.pipeline_matrix[instr][self.clock] = stage
    def has_raw_hazard(self, curr_instr):
        sources = [curr_instr.rs, curr_instr.rt]
        # این پیدا شدن مخاطره رو مشخص میکند و در ابتدای کار ک هنوز بررسی انجام نشده مقداری f داره
        hazard = False

        for stage in ["EX", "MEM", "WB"]:
            for instr in self.pipeline_registers[stage]:
                if not instr.rd:
                    continue

                for src in sources:
                    if src and src == instr.rd:
                        if self.enable_forwarding:
                            # بررسی استثنا: LW در EX قابل forward نیست
                            if stage == "EX" and instr.instr_type == "LW":
                                hazard = True  # نه forwarding، نه اجرا
                            else:
                                # اگر قابل forward بود → شمارش کنیم
                                self.forward_count += 1
                                continue  # فوروارد می‌گیریم
                        else:
                            hazard = True
        return hazard
    def tick(self):
            # شروع یک کلاک جدید
            self.clock += 1
            print('clock: ',self.clock)
            print('instructions: ',self.instructions)
            print(self.pipeline_registers)

            # WB مرحله: نهایی کردن
            wb_instr = self.pipeline_registers["WB"]
            self.pipeline_registers["WB"] = []
            for instr in wb_instr:
                instr.finished = True
                self.completed_instructions.append(instr)

            # MEM ← WB
            self.pipeline_registers["WB"] = self.pipeline_registers["MEM"]
            # # EX ← MEM
            self.pipeline_registers["MEM"] = self.pipeline_registers["EX"]

            # بررسی انشعاب در EX
            if self.pipeline_registers["EX"]:
                curr_instr = self.pipeline_registers["EX"][0]
                if self.is_conditional_branch(curr_instr):
                    # branch_taken = branch_condition_taken(curr_instr)  # یا هر شرط واقعی‌ای که بخوای
                    branch_taken = True # یا هر شرط واقعی‌ای که بخوای
                    if branch_taken:
                        # Flush مراحل IF و ID
                        for stage in ["IF", "ID"]:
                            for flushed_instr in self.pipeline_registers[stage]:
                                flushed_instr.is_flushed = True
                                self.flush_count += 1
                            self.pipeline_registers[stage] = []

                        # توجه: اگر نیاز داری، PC رو هم به مقصد برنچ ببر
                        # self.set_pc(curr_instr.pc + curr_instr.imm) یا مشابه


            # بررسی برای EX ← ID
            if self.pipeline_registers["ID"]:
                curr_instr = self.pipeline_registers["ID"][0]


                if self.has_raw_hazard(curr_instr):
                    self.pipeline_registers["EX"] = []  # استال
                    self.stall_count += 1
                    self.log_pipeline_stage(curr_instr, "ID")
                else:
                    self.pipeline_registers["EX"] = self.pipeline_registers["ID"]
                    self.pipeline_registers["ID"] = []

            else:
                self.pipeline_registers["EX"] = []

            can_fetch_new = not self.pipeline_registers["ID"] or not self.has_raw_hazard(self.pipeline_registers["ID"][0])


            print("can_fetch_new: ",can_fetch_new)
            if can_fetch_new:
                self.pipeline_registers["ID"] = self.pipeline_registers["IF"]
                self.pipeline_registers["IF"] = []
            # else:
                # self.pipeline_registers["IF"] = []


            if len(self.instructions) > 0 and can_fetch_new:
                next_instr = self.instructions.pop(0)
                self.pipeline_registers["IF"].append(next_instr)


            
                


            # لاگ کردن وضعیت هر دستور
            for stage, instr_list in self.pipeline_registers.items():
                for instr in instr_list:
                    self.log_pipeline_stage(instr, stage)
            print('instructions: ',self.instructions)
            print(self.pipeline_registers)
            print('============================================')
    def is_done(self):
        return len(self.completed_instructions) == self.total_instruction_count()
    def print_stats(self):
        total_cycles = self.clock
        total_instrs = len(self.completed_instructions)
        cpi = total_cycles / total_instrs if total_instrs > 0 else float('inf')

        print("\n=== Pipeline Statistics ===")
        print(f"Total Cycles     : {total_cycles}")
        print(f"Total Instructions: {total_instrs}")
        print(f"Total Stalls     : {self.stall_count}")
        print(f"Total Flushes    : {self.flush_count}")
        print(f"Total Forwards   : {self.forward_count}")
        print(f"Structural Stalls: {self.structural_stalls}")
        print(f"CPI              : {cpi:.2f}")
    def total_instruction_count(self):
        return len(self.completed_instructions) + sum(len(lst) for lst in self.pipeline_registers.values()) + len(self.instructions)
    def run(self, max_cycles=100):
        while not self.is_done() and self.clock < max_cycles:
            self.tick()

        # حذف آخرین cycle اگر خالی بوده و چیزی اجرا نشده
        if all(len(stage) == 0 for stage in self.pipeline_registers.values()):
            self.clock -= 1

        self.print_pipeline_matrix()
        self.print_stats()
        stats = {
            "Total Cycles": self.clock,
            "Total Instructions": self.input_instructions_count,
            "Stalls": self.stall_count,
            "Flushes": getattr(self, 'flush_count', 0),
            "Forwards": getattr(self, 'forward_count', 0),
            "CPI": self.clock / len(self.completed_instructions) if self.completed_instructions else float("inf")
        }
        export_simulation_image(self.pipeline_matrix, stats, self.enable_forwarding)

    def is_conditional_branch(self,instr):
        print('in is_conditional_branch',instr)
        return instr.instr_type in ["BEQ", "BNE", "BLE", "BGE"]
    def print_pipeline_matrix(self):
        print("\nPipeline Matrix:\n")
        max_cycle = self.clock
        all_instrs = sorted(self.pipeline_matrix.keys(), key=lambda x: x.id)

        # سطر اول: شماره کلاک‌ها
        header = ["     "]
        for c in range(1, max_cycle + 1):
            header.append(f"C{c:<3}")
        print(" ".join(header))

        # هر دستور
        for instr in all_instrs:
            row = [f"I{instr.id:<3}|"]
            for c in range(1, max_cycle + 1):
                if instr.is_flushed and c in self.pipeline_matrix[instr]:
                    row.append("--  ")  # نشانه flush
                else:
                    stage = self.pipeline_matrix[instr].get(c, "")
                    row.append(f"{stage:<4}")
            print(" ".join(row))
