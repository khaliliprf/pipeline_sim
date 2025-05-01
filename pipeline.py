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
        self.clock += 1

        # مرحله WB: دستوراتی که وارد WB بودن کامل می‌شن
        wb_instr = self.pipeline_registers["WB"]
        self.pipeline_registers["WB"] = []
        for instr in wb_instr:
            instr.finished = True
            self.completed_instructions.append(instr)

        # MEM ← WB
        self.pipeline_registers["WB"] = self.pipeline_registers["MEM"]

        # EX ← MEM
        self.pipeline_registers["MEM"] = self.pipeline_registers["EX"]

        # بررسی RAW hazard برای ID → EX
        if self.pipeline_registers["ID"]:
            curr_instr = self.pipeline_registers["ID"][0]
            if self.has_raw_hazard(curr_instr):
                self.pipeline_registers["EX"] = []  # Stall
                self.stall_count += 1               # ← شمارش استال
                self.log_pipeline_stage(curr_instr, "ID")
            else:
                self.pipeline_registers["EX"] = self.pipeline_registers["ID"]
                self.pipeline_registers["ID"] = []
        else:
            self.pipeline_registers["EX"] = []

        # ID ← IF (فقط اگر ID خالی باشه)
        if not self.pipeline_registers["ID"]:
            self.pipeline_registers["ID"] = self.pipeline_registers["IF"]
            self.pipeline_registers["IF"] = []

        # IF ← دستور جدید فقط اگر IF خالی باشه
        if len(self.instructions) > 0 and not self.pipeline_registers["IF"]:
            next_instr = self.instructions.pop(0)
            self.pipeline_registers["IF"].append(next_instr)

        # ثبت همه مراحل
        for stage in ["IF", "ID", "EX", "MEM", "WB"]:
            for instr in self.pipeline_registers[stage]:
                self.log_pipeline_stage(instr, stage)


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

        # سطر اول: شماره سیکل‌ها
        header = ["     "]
        for c in range(1, max_cycle + 1):
            header.append(f"C{c:<3}")
        print(" ".join(header))

        # سطرهای دستورها
        for instr in all_instrs:
            row = [f"I{instr.id:<3}|"]
            for c in range(1, max_cycle + 1):
                stage = self.pipeline_matrix[instr].get(c, "")
                row.append(f"{stage:<4}")
            print(" ".join(row))
