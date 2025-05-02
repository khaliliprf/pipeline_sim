# pipeline.py

from instruction import Instruction
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from datetime import datetime
import pandas as pd

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

            # بررسی برای EX ← ID
            if self.pipeline_registers["ID"]:
                curr_instr = self.pipeline_registers["ID"][0]

                # ex_busy = bool(self.pipeline_registers["EX"])
                # mem_busy = bool(self.pipeline_registers["MEM"])

                # if ex_busy or mem_busy:
                #     self.structural_stalls += 1
                #     self.stall_count += 1
                #     self.log_pipeline_stage(curr_instr, "ID")  # دستور در ID بمونه
                # بررسی دستور BEQ برای Flush
                if curr_instr.instr_type == "BEQ":
                    branch_taken = False  # در اینجا فرض می‌کنیم انشعاب انجام نمی‌شه

                    if not branch_taken:
                        # دستور BEQ و دستورهای بعدی در IF/ID حذف می‌شن
                        for stage in ["IF", "ID"]:
                            for flushed_instr in self.pipeline_registers[stage]:
                                flushed_instr.is_flushed = True
                                self.flush_count += 1  # ← شمارش flush

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
        print(f"Total Flushes    : {self.flush_count}")
        print(f"Total Forwards   : {self.forward_count}")
        print(f"Structural Stalls: {self.structural_stalls}")
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
        stats = {
            "Total Cycles": self.clock,
            "Total Instructions": self.input_instructions_count,
            "Stalls": self.stall_count,
            "Flushes": getattr(self, 'flush_count', 0),
            "Forwards": getattr(self, 'forward_count', 0),
            "CPI": self.clock / len(self.completed_instructions) if self.completed_instructions else float("inf")
        }
        export_simulation_image(self.pipeline_matrix, stats, self.enable_forwarding, simulation_count=1)
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



def export_simulation_image(pipeline_matrix, stats, enable_forwarding, simulation_count=1):
    stage_colors = {
        "IF": "#a6cee3",
        "ID": "#fdbf6f",
        "EX": "#b2df8a",
        "MEM": "#cab2d6",
        "WB": "#fb9a99",
        "--": "#999999",
        None: "#ffffff"
    }

    # تبدیل ماتریس به DataFrame
    instructions = sorted(pipeline_matrix.keys(), key=lambda x: x.id)
    max_cycle = max(max(cycles.keys()) for cycles in pipeline_matrix.values())
    df = pd.DataFrame(index=[f"I{instr.id}" for instr in instructions], columns=range(1, max_cycle+1))

    for instr in instructions:
        for cycle, stage in pipeline_matrix[instr].items():
            df.at[f"I{instr.id}", cycle] = "--" if getattr(instr, "is_flushed", False) else stage

    # رسم گرافیکی ترکیبی
    fig, (ax1, ax2) = plt.subplots(nrows=2, figsize=(14, 8), gridspec_kw={"height_ratios": [3, 1]})

    for i, instr in enumerate(df.index):
        for j, cycle in enumerate(df.columns):
            stage = df.loc[instr, cycle]
            color = stage_colors.get(stage, "#ffffff")
            ax1.add_patch(plt.Rectangle((j, i), 1, 1, color=color, ec='black'))
            if stage:
                ax1.text(j + 0.5, i + 0.5, stage, ha='center', va='center', fontsize=9)

    ax1.set_xlim(0, len(df.columns))
    ax1.set_ylim(0, len(df.index))
    ax1.set_xticks([x + 0.5 for x in range(len(df.columns))])
    ax1.set_xticklabels([f"C{c}" for c in df.columns])
    ax1.set_yticks([y + 0.5 for y in range(len(df.index))])
    ax1.set_yticklabels(df.index)
    ax1.invert_yaxis()
    ax1.xaxis.tick_top()
    ax1.set_title("Pipeline Execution Timeline", pad=30)

    legend_handles = [Patch(color=color, label=stage) for stage, color in stage_colors.items() if stage]
    ax1.legend(handles=legend_handles, bbox_to_anchor=(1.01, 1), loc='upper left')

    # جدول آماری
    ax2.axis('tight')
    ax2.axis('off')
    table_data = [[k, v] for k, v in stats.items()]
    table = ax2.table(cellText=table_data, colLabels=["Metric", "Value"], cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.5)
    ax2.set_title("Pipeline Simulation Statistics", pad=30)

    plt.tight_layout()

    # ذخیره فایل
    os.makedirs("stats", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"simulation{simulation_count}_{stats['Total Instructions']}instr_{stats['Total Cycles']}cyc_{'forwarding' if enable_forwarding else 'noforwarding'}_{timestamp}.png"
    filepath = os.path.join("stats", filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[✔] Saved pipeline result image to: {filepath}")