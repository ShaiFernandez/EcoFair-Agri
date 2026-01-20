import json
import os
import matplotlib.pyplot as plt


def load_results(path="results.json"):
    with open(path, "r") as f: return json.load(f)


def save_fig(fig, name):
    os.makedirs("figures", exist_ok=True)
    fig.savefig(f"figures/{name}.png", bbox_inches="tight", dpi=300)
    plt.close(fig)


def fig_impact_bar(results):
    keys = ["S1", "S2", "S3"]
    labels = ["S1 (Base)", "S2 (Tax)", "S3 (Fair)"]

    water = [results[k]["summary"]["total_water"] for k in keys]
    energy = [results[k]["summary"]["total_energy"] for k in keys]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Water Plot
    ax1.bar(labels, water, color='#3498db', alpha=0.8)
    ax1.set_title("Total Water Usage (Liters)")
    ax1.set_ylabel("Liters")
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    # Energy Plot
    ax2.bar(labels, energy, color='#e67e22', alpha=0.8)
    ax2.set_title("Total Energy Usage (kWh)")
    ax2.set_ylabel("kWh")
    ax2.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    save_fig(fig, "fig1_impacts")


def fig_market_share(results):
    keys = ["S1", "S2", "S3"]
    labels = ["S1 (Base)", "S2 (Tax)", "S3 (Fair)"]

    indoor = [results[k]["groups"]["Indoor"] for k in keys]
    outdoor = [results[k]["groups"]["Outdoor"] for k in keys]

    fig, ax = plt.subplots(figsize=(8, 5))

    # Stacked Bar Chart
    ax.bar(labels, indoor, label="Indoor (Type A)", color='#088941')
    ax.bar(labels, outdoor, bottom=indoor, label="Outdoor (Type B)", color='#e67e22')

    ax.set_ylabel("Market Share (0.0 - 1.0)")
    ax.set_title("Market Dominance by Scenario")
    ax.legend(loc='upper right')
    ax.set_ylim(0, 1.0)

    save_fig(fig, "fig2_market_share")


def fig_gini(results):
    keys = ["S1", "S2", "S3"]
    labels = ["S1 (Base)", "S2 (Tax)", "S3 (Fair)"]
    gini = [results[k]["summary"]["share_gini"] for k in keys]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, gini, color='#3498db', alpha=0.8)

    ax.set_ylabel("Gini Coefficient")
    ax.set_title("Market Inequality (Lower is Better)")
    ax.set_ylim(0, 1.0)

    # Add values on top
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height + 0.02,
                f'{height:.3f}', ha='center', va='bottom', fontweight='bold')

    save_fig(fig, "fig3_gini_inequality")


# --- NEW FUNCTIONS FOR FIGURES 5 & 6 ---

def fig_security_timeseries(results):
    # FIG 5: Shows the "Winter Collapse"
    # S1 should crash at t=80. S3 should stay stable.

    s1_supply = results["S1"]["timeseries"]["supply"]
    s3_supply = results["S3"]["timeseries"]["supply"]

    t = range(1, len(s1_supply) + 1)

    fig, ax = plt.subplots(figsize=(10, 5))

    # Plot S1
    ax.plot(t, s1_supply, label="S1: Cost-Driven (Outdoor Only)",
            color='#e74c3c', linestyle='-', linewidth=2)

    # Plot S3
    ax.plot(t, s3_supply, label="S3: Fairness-Aware (Hybrid)",
            color='#2ecc71', linestyle='-', linewidth=2, alpha=0.9)

    # Highlight Winter
    ax.axvspan(80, 100, color='gray', alpha=0.2, label="Winter Season")

    ax.set_xlabel("Simulation Round (Week)")
    ax.set_ylabel("Total Food Secured (Units)")
    ax.set_title("Supply Chain Resilience: The Winter Collapse")
    ax.legend(loc="lower left")
    ax.grid(True, linestyle='--', alpha=0.5)

    save_fig(fig, "fig5_security_timeseries")


def fig_waste_bar(results):
    # FIG 6: Shows Waste (Spoilage)
    # S1 should be high (long distance). S3 should be lower (local mix).

    keys = ["S1", "S2", "S3"]
    labels = ["S1 (Base)", "S2 (Tax)", "S3 (Fair)"]
    waste = [results[k]["summary"]["total_waste"] for k in keys]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(labels, waste, color='#7f8c8d', alpha=0.8)

    ax.set_ylabel("Food Waste (Spoiled Units)")
    ax.set_title("Food Waste Generation (Distance Spoilage)")

    # Add values
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h, f'{h:.0f}',
                ha='center', va='bottom')

    save_fig(fig, "fig6_waste_analysis")


if __name__ == "__main__":
    results = load_results()
    print("Generating figures...")
    fig_impact_bar(results)
    fig_market_share(results)
    fig_gini(results)
    fig_security_timeseries(results)  # <--- NEW
    fig_waste_bar(results)  # <--- NEW
    print("Done! Figures saved to figures/ folder.")