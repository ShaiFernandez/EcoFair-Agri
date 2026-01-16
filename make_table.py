import json
from typing import Dict, Any, List


def load_results(path: str = "results.json") -> Dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


def scenario_order(results: Dict[str, Any]) -> List[str]:
    preferred = ["S1", "S2A", "S2B", "S3", "S4A", "S4B", "S4C"]
    return [k for k in preferred if k in results] + [k for k in results if k not in preferred]


def scenario_label(key: str) -> str:
    mapping = {
        "S1": "S1",
        "S2A": "S2A",
        "S2B": "S2B",
        "S3": "S3",
        "S4A": "S4",
        "S4B": "S4 (Disp)",
        "S4C": "S4 (Rot)",
    }
    return mapping.get(key, key)


def fmt(x: float, nd: int = 3) -> str:
    return f"{x:.{nd}f}"


def build_table_ii(results: Dict[str, Any]) -> str:
    keys = scenario_order(results)

    lines = []
    lines.append(r"\begin{table}[t]")
    lines.append(r"\caption{Summary outcomes across policy scenarios.}")
    lines.append(r"\label{tab:results_summary}")
    lines.append(r"\centering")
    lines.append(r"\resizebox{\columnwidth}{!}{%")
    lines.append(r"\begin{tabular}{lrrrrrr}")
    lines.append(r"\hline")
    lines.append(r"Scenario & Total CO$_2$ & Mean CO$_2$/t & Mean Cost/t & Part. rate & Gini$(H)$ & Max$(H)$ \\")
    lines.append(r"\hline")

    for k in keys:
        summary = results[k]["summary"]
        params = results[k].get("params", {})

        use_fairness = bool(params.get("use_fairness", False))

        # Participation rate (always meaningful)
        part = summary.get("participation_rate", 0.0)

        # Fairness metrics: only meaningful when fairness is enabled
        if use_fairness:
            gini_str = fmt(float(summary.get("share_gini", 0.0)), 3)
            max_str = fmt(float(summary.get("share_max", 0.0)), 3)
        else:
            gini_str = r"--"
            max_str = r"--"

        row = " & ".join([
            scenario_label(k),
            fmt(float(summary["co2_total_sum"]), 2),
            fmt(float(summary["co2_total_mean"]), 2),
            fmt(float(summary["cost_total_mean"]), 2),
            fmt(float(part), 2),
            gini_str,
            max_str,
        ]) + r" \\"
        lines.append(row)

    lines.append(r"\hline")
    lines.append(r"\end{tabular}%")
    lines.append(r"}")
    lines.append(r"\end{table}")
    lines.append("")
    return "\n".join(lines)

def build_table_i(results: Dict[str, Any]) -> str:
    keys = scenario_order(results)

    lines = []
    lines.append(r"\begin{table}[t]")
    lines.append(r"\caption{Summary outcomes across policy scenarios.}")
    lines.append(r"\label{tab:results_summary}")
    lines.append(r"\centering")
    lines.append(r"\resizebox{\columnwidth}{!}{%")
    lines.append(r"\begin{tabular}{lrrr|rrr}")
    lines.append(r"\hline")

    # Grouped headers
    lines.append(r" & \multicolumn{3}{c|}{\textbf{Efficiency}} & \multicolumn{3}{c}{\textbf{Fairness}} \\")
    lines.append(r"\textbf{Scenario} & Total CO$_2$ & Mean CO$_2$/t & Mean Cost/t & Partic. & Gini$(H)$ & Max$(H)$ \\")
    lines.append(r"\hline")

    for k in keys:
        s = results[k]["summary"]
        row = " & ".join([
            scenario_label(k),
            fmt(float(s["co2_total_sum"]), 2),
            fmt(float(s["co2_total_mean"]), 2),
            fmt(float(s["cost_total_mean"]), 2),
            fmt(float(s["participation_rate"]), 3),
            fmt(float(s["share_gini"]), 3),
            fmt(float(s["share_max"]), 3),
        ]) + r" \\"
        lines.append(row)

    lines.append(r"\hline")
    lines.append(r"\end{tabular}%")
    lines.append(r"}")
    lines.append(r"\end{table}")
    lines.append("")
    return "\n".join(lines)


def main():
    results = load_results("results.json")
    table_tex = build_table_ii(results)
    table_tex_i = build_table_i(results)

    out_path = "table_ii.tex"
    with open(out_path, "w") as f:
        f.write(table_tex)

    print(f"Wrote LaTeX table to: {out_path}")

    out_path = "table_i.tex"
    with open(out_path, "w") as f:
        f.write(table_tex_i)

    print(f"Wrote LaTeX table to: {out_path}")


if __name__ == "__main__":
    main()
