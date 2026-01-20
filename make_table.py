import json


import json


def build_table(results):
    keys = ["S1", "S2", "S3"]
    labels = {"S1": "Baseline", "S2": "Taxation", "S3": "Fairness"}

    lines = []
    lines.append(r"\begin{table}[h]")
    lines.append(r"\caption{Simulation Results: Efficiency vs Fairness}")
    lines.append(r"\centering")
    lines.append(r"\begin{tabular}{lcccc}")
    lines.append(r"\hline")
    lines.append(
        r"\textbf{Scenario} & \textbf{Cost (\$)} & \textbf{Water (L)} & \textbf{Energy (kWh)} & \textbf{Gini} \\")
    lines.append(r"\hline")

    for k in keys:
        s = results[k]["summary"]
        row = f"{labels[k]} & {s['cost_mean']:.2f} & {s['total_water']:.0f} & {s['total_energy']:.0f} & {s['share_gini']:.3f} \\\\"
        lines.append(row)

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    return "\n".join(lines)

def build_tablei(results):
    keys = ["S1", "S2", "S3"]
    labels = {"S1": "Baseline", "S2": "Taxation", "S3": "Fairness"}

    lines = []
    lines.append(r"\begin{table}[h]")
    lines.append(r"\caption{Simulation Results: Efficiency, Waste, and Fairness}")
    lines.append(r"\centering")
    lines.append(r"\resizebox{\columnwidth}{!}{%")
    lines.append(r"\begin{tabular}{lccccc}")  # Added one more 'c'
    lines.append(r"\hline")
    # Added "Waste" Column
    lines.append(
        r"\textbf{Scenario} & \textbf{Cost (\$)} & \textbf{Water (L)} & \textbf{Energy (kWh)} & \textbf{Waste (Units)} & \textbf{Gini} \\")
    lines.append(r"\hline")

    for k in keys:
        s = results[k]["summary"]
        # Added s['total_waste']
        row = f"{labels[k]} & {s['cost_mean']:.2f} & {s['total_water']:.0f} & {s['total_energy']:.0f} & {s['total_waste']:.0f} & {s['share_gini']:.3f} \\\\"
        lines.append(row)

    lines.append(r"\hline")
    lines.append(r"\end{tabular}%")
    lines.append(r"}")
    lines.append(r"\end{table}")

    return "\n".join(lines)


if __name__ == "__main__":
    with open("results.json", "r") as f:
        results = json.load(f)

    tex = build_table(results)
    texi = build_tablei(results)
    with open("table_results.tex", "w") as f:
        f.write(tex)
    with open("table_resultsi.tex", "w") as f:
        f.write(texi)
    print("Table saved to table_results.tex")




def build_table(results):
    keys = ["S1", "S2", "S3"]
    labels = {"S1": "Baseline", "S2": "Taxation", "S3": "Fairness"}

    lines = []
    lines.append(r"\begin{table}[h]")
    lines.append(r"\caption{Simulation Results: Efficiency vs Fairness}")
    lines.append(r"\centering")
    lines.append(r"\begin{tabular}{lcccc}")
    lines.append(r"\hline")
    lines.append(
        r"\textbf{Scenario} & \textbf{Cost (\$)} & \textbf{Water (L)} & \textbf{Energy (kWh)} & \textbf{Gini} \\")
    lines.append(r"\hline")

    for k in keys:
        s = results[k]["summary"]
        row = f"{labels[k]} & {s['cost_mean']:.2f} & {s['total_water']:.0f} & {s['total_energy']:.0f} & {s['share_gini']:.3f} \\\\"
        lines.append(row)

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    return "\n".join(lines)


if __name__ == "__main__":
    with open("results.json", "r") as f:
        results = json.load(f)

    tex = build_table(results)
    with open("table_results.tex", "w") as f:
        f.write(tex)
    print("Table saved to table_results.tex")

