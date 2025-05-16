import os
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from datetime import datetime
import pandas as pd


def export_simulation_image(pipeline_matrix, stats, enable_forwarding):
    stage_colors = {
        "IF": "#a6cee3",
        "ID": "#fdbf6f",
        "EX": "#b2df8a",
        "MEM": "#cab2d6",
        "WB": "#fb9a99",
        "--": "#999999",
        None: "#ffffff"
    }

    os.makedirs("stats", exist_ok=True)
    stats_json_path = os.path.join("stats", "stats.json")

    # خواندن شمارنده شبیه‌سازی قبلی
    if os.path.exists(stats_json_path):
        try:
            with open(stats_json_path, 'r') as f:
                data = json.load(f)
                simulation_count = data.get("last_simulation_number", 1)
        except (json.JSONDecodeError, FileNotFoundError, ValueError):
            simulation_count = 1
    else:
        simulation_count = 1

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
    
    # افزودن شمارنده شبیه‌سازی به عنوان تیتر
    ax1.set_title(f"Pipeline Execution Timeline (Simulation #{simulation_count})", pad=30)

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

    # ساخت نام و ذخیره فایل
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"simulation{simulation_count}_{stats['Total Instructions']}instr_{stats['Total Cycles']}cyc_{'forwarding' if enable_forwarding else 'no-forwarding'}.png"
    filepath = os.path.join("stats", filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()

    # به‌روزرسانی شمارنده در فایل json
    with open(stats_json_path, 'w') as f:
        json.dump({"last_simulation_number": simulation_count + 1}, f)

    print(f"[✔] Saved pipeline result image to: {filepath}")

def branch_condition_taken(instr):
    rs_val = instr.rs  # در شبیه‌سازی فرضی مقدار واقعی اینا باید معلوم بشه
    rt_val = instr.rt

    # فرض ساده: مقدار عددی رجیسترها برابر با اسم رجیستر (مثلاً r2 = 2)
    try:
        rs_val = int(rs_val[1:])  # "r2" → 2
        rt_val = int(rt_val[1:])
    except:
        return False

    if instr.instr_type == "BEQ":
        return rs_val == rt_val
    elif instr.instr_type == "BNE":
        return rs_val != rt_val
    elif instr.instr_type == "BLE":
        return rs_val <= rt_val
    elif instr.instr_type == "BGE":
        return rs_val >= rt_val
    else:
        return False
