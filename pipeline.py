# pipeline.py

from instruction import Instruction

class Pipeline:
    def __init__(self, instructions,enable_forwarding=False):
        
        self.instructions = instructions
        self.stall_count = 0
        self.enable_forwarding = enable_forwarding

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
        sources = [curr_instr.rs, curr_instr.rt]  # رجیسترهایی که نیاز داریم

        for stage in ["EX", "MEM", "WB"]:
            for instr in self.pipeline_registers[stage]:
                if not instr.rd:
                    continue

                for src in sources:
                    if src and src == instr.rd:
                        if self.enable_forwarding:
                            # بررسی شرایط خاص forwarding
                            if stage == "EX":
                                if instr.instr_type == "LW":
                                    return True  # ← استثنا: LW هنوز آماده نیست
                                else:
                                    continue  # ← فوروارد از ALU (EX) مجازه
                            elif stage in ["MEM", "WB"]:
                                continue  # ← داده قابل فوروارد شدن هست
                        return True  # ← اگر فورواردینگ غیرفعاله، استال نیاز داریم
        return False

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

            # بررسی برای EX ← ID
            if self.pipeline_registers["ID"]:
                curr_instr = self.pipeline_registers["ID"][0]

                # بررسی دستور BEQ برای Flush
                if curr_instr.instr_type == "BEQ":
                    branch_taken = False  # در اینجا فرض می‌کنیم انشعاب انجام نمی‌شه

                    if not branch_taken:
                        # دستور BEQ و دستورهای بعدی در IF/ID حذف می‌شن
                        for stage in ["IF", "ID"]:
                            for flushed_instr in self.pipeline_registers[stage]:
                                flushed_instr.is_flushed = True
                        self.pipeline_registers["IF"] = []
                        self.pipeline_registers["ID"] = []
                        self.pipeline_registers["EX"] = []
                    else:
                        self.pipeline_registers["EX"] = self.pipeline_registers["ID"]
                        self.pipeline_registers["ID"] = []

                elif self.has_raw_hazard(curr_instr):
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
        print(f"CPI              : {cpi:.2f}")

    def total_instruction_count(self):
        return len(self.completed_instructions) + sum(len(lst) for lst in self.pipeline_registers.values()) + len(self.instructions)

    def run(self, max_cycles=100):
        # print(f"[RUN] Pipeline starting — Forwarding: {self.enable_forwarding}")
        while not self.is_done() and self.clock < max_cycles:
            # print(f"[TICK {self.clock+1}] Remaining: {len(self.instructions)} | IF: {self.pipeline_registers['IF']} | ID: {self.pipeline_registers['ID']}")
            self.tick()
        self.print_pipeline_matrix()
        self.print_stats()



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

