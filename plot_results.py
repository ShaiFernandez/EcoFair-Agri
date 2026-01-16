import json
import os
from typing import Dict, Any, List, Tuple

import matplotlib.pyplot as plt


# -------------------------
# Helpers
# -------------------------
def load_results(path: str = "results.json") -> Dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def scenario_order(results: Dict[str, Any]) -> List[str]:
    # Default order aligned with paper narrative
    preferred = ["S1", "S2A", "S2B", "S3", "S4A"]
    #preferred = ["S1", "S2A", "S2B", "S3", "S4A", "S4B", "S4C"]
    return [k for k in preferred if k in results] + [k for k in results if k not in preferred]


def scenario_label(key: str, results: Dict[str, Any]) -> str:
    # Short labels for plots
    # You can edit these if you prefer longer names
    mapping = {
        "S1": "S1",
        "S2A": "S2A",
        "S2B": "S2B",
        "S3": "S3",
        "S4A": "S4",
        #"S4B": "S4 (Disp)",
        #"S4C": "S4 (Rot)",
    }
    return mapping.get(key, key)


def get_summary(results: Dict[str, Any], key: str) -> Dict[str, Any]:
    return results[key]["summary"]


def get_suppliers_group(results: Dict[str, Any], key: str) -> Dict[str, Any]:
    return results[key]["suppliers"]["by_group"]


def save_fig(fig, outdir: str, name: str) -> None:
    png = os.path.join(outdir, f"{name}.png")
    pdf = os.path.join(outdir, f"{name}.pdf")
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)


# -------------------------
# Figures
# -------------------------
def fig_total_co2_bar(results: Dict[str, Any], outdir: str) -> None:
    keys = scenario_order(results)
    labels = [scenario_label(k, results) for k in keys]
    values = [get_summary(results, k)["co2_total_sum"] for k in keys]

    fig = plt.figure(figsize=(7.0, 3.2))
    ax = fig.add_subplot(111)
    ax.bar(labels, values)
    ax.set_ylabel("Total CO₂ (sum over T)")
    ax.set_xlabel("Scenario")
    #ax.set_title("Total system emissions by scenario")
    ax.tick_params(axis="x", rotation=0)
    fig.tight_layout()
    save_fig(fig, outdir, "fig1_total_co2")


def fig_co2_breakdown_stacked(results: Dict[str, Any], outdir: str) -> None:
    keys = scenario_order(results)
    labels = [scenario_label(k, results) for k in keys]
    prod = [get_summary(results, k)["co2_prod_sum"] for k in keys]
    trans = [get_summary(results, k)["co2_trans_sum"] for k in keys]

    fig = plt.figure(figsize=(7.0, 3.2))
    ax = fig.add_subplot(111)
    ax.bar(labels, prod, label="Production CO₂")
    ax.bar(labels, trans, bottom=prod, label="Transport CO₂")
    ax.set_ylabel("CO₂ (sum over T)")
    ax.set_xlabel("Scenario")
    #ax.set_title("Emissions breakdown (production vs transport)")
    ax.legend(frameon=False)
    fig.tight_layout()
    save_fig(fig, outdir, "fig2_co2_breakdown")


def fig_cost_bar(results: Dict[str, Any], outdir: str) -> None:
    keys = scenario_order(results)
    labels = [scenario_label(k, results) for k in keys]
    values = [get_summary(results, k)["cost_total_mean"] for k in keys]

    fig = plt.figure(figsize=(7.0, 3.2))
    ax = fig.add_subplot(111)
    ax.bar(labels, values)
    ax.set_ylabel("Mean cost per timestep")
    ax.set_xlabel("Scenario")
    #ax.set_title("Average procurement cost by scenario")
    fig.tight_layout()
    save_fig(fig, outdir, "fig3_cost_mean")


def fig_group_shares(results: Dict[str, Any], outdir: str) -> None:
    keys = scenario_order(results)
    labels = [scenario_label(k, results) for k in keys]

    # Extract H shares by group for each scenario
    groups = ["A", "B", "C"]
    group_H = {g: [] for g in groups}
    for k in keys:
        by_group = get_suppliers_group(results, k)
        for g in groups:
            group_H[g].append(float(by_group.get(g, {}).get("H", 0.0)))

    # grouped bars
    x = list(range(len(keys)))
    width = 0.25

    fig = plt.figure(figsize=(7.2, 3.2))
    ax = fig.add_subplot(111)

    ax.bar([i - width for i in x], group_H["A"], width=width, label="Group A")
    ax.bar(x, group_H["B"], width=width, label="Group B")
    ax.bar([i + width for i in x], group_H["C"], width=width, label="Group C")

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Allocation share H (sum to 1)")
    ax.set_xlabel("Scenario")
    #ax.set_title("Supplier participation shares by group (A/B/C)")
    ax.legend(frameon=False)
    fig.tight_layout()
    save_fig(fig, outdir, "fig4_group_shares")


def fig_fairness_compare_s4(results: Dict[str, Any], outdir: str) -> None:
    # Only plot if these exist
    keys = [k for k in ["S4A", "S4B", "S4C"] if k in results]
    if not keys:
        return

    labels = ["Balanced (δ=0.5)", "Disparity (δ=0)", "Rotation (δ=1)"]
    gini_vals = [get_summary(results, k)["share_gini"] for k in keys]
    maxshare_vals = [get_summary(results, k)["share_max"] for k in keys]

    x = list(range(len(keys)))
    width = 0.35

    fig = plt.figure(figsize=(6.2, 3.2))

    ax = fig.add_subplot(111)
    ax.bar([i - width / 2 for i in x], gini_vals, width=width, label="Gini(H)")
    ax.bar([i + width / 2 for i in x], maxshare_vals, width=width, label="Max share(H)")
    # Optional: give a little headroom
    ymax = max(max(gini_vals), max(maxshare_vals))
    ax.set_ylim(0, ymax * 1.08)

    # Value labels on bars (makes small differences visible)
    for i, (g, m) in enumerate(zip(gini_vals, maxshare_vals)):
        ax.text(i - width / 2, g + 0.005, f"{g:.3f}", ha="center", va="bottom", fontsize=8)
        ax.text(i + width / 2, m + 0.005, f"{m:.3f}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Inequality metrics")
    ax.set_xlabel("Scenario")
    #ax.set_title("Fairness ablations (S4 variants): inequality outcomes")
    ax.legend(
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2
    )
    fig.tight_layout()

    save_fig(fig, outdir, "fig5_fairness_s4_compare")

def fig_participation_rate(results: Dict[str, Any], outdir: str) -> None:
    keys = scenario_order(results)
    labels = [scenario_label(k, results) for k in keys]
    #values = [float(get_summary(results, k).get("participation_rate", 0.0)) for k in keys]
    values = [get_summary(results, k)["participation_rate"] for k in keys]

    fig = plt.figure(figsize=(7.0, 3.2))
    ax = fig.add_subplot(111)
    ax.bar(labels, values)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Participation rate")
    ax.set_xlabel("Scenario")
    #ax.set_title("Supplier participation rate (fraction with Q > 0)")
    fig.tight_layout()
    save_fig(fig, outdir, "fig6_participation_rate")

# -------------------------
# Main
# -------------------------
def main():
    results = load_results("results.json")
    outdir = "figures"
    ensure_dir(outdir)

    fig_total_co2_bar(results, outdir)
    fig_co2_breakdown_stacked(results, outdir)
    fig_cost_bar(results, outdir)
    fig_group_shares(results, outdir)
    #fig_fairness_compare_s4(results, outdir)
    fig_participation_rate(results, outdir)

    print(f"Saved figures to: {outdir}/ (PNG + PDF)")


if __name__ == "__main__":
    main()
