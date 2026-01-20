import numpy as np
import matplotlib.pyplot as plt
import random
from simulation import *
from scenarios import SCENARIOS
from extract_metrics import extract_metrics, gini


def run_sensitivity_sweep():
    print("Running Sensitivity Analysis (Gamma 0.0 -> 1.0)...")

    gammas = np.linspace(0.0, 1.0, 11)  # [0.0, 0.1, ... 1.0]
    results_gini = []
    results_cost = []

    base_scenario = SCENARIOS["S3"]  # Use S3 as base, modify gamma

    for g in gammas:
        # Create temp scenario config
        cfg = ScenarioConfig(
            name=f"Sens_G{g:.1f}", T=100,
            scarcity_cost_water=0.05, scarcity_cost_energy=0.10,
            alpha=0.5, beta=0.2, gamma=g,  # <--- VARYING GAMMA
            use_individualized_lca=True, use_fairness=True,
            allocation_mode="proportional", delta=0.5
        )

        # Run Simulation
        random.seed(42)
        suppliers = create_farmers_AB()
        buyers = [create_example_buyer()]
        # (Setup modules like in main.py...)
        env = EnvironmentalDataModule(0, {}, 0)
        fair = FairnessModule(0.5)
        pol = PolicyScoringModule(cfg)
        mkt = MarketplaceModule(env, fair, pol)
        log = Logger()

        sim = Simulation(suppliers, buyers, env, fair, pol, mkt, log, cfg)
        sim.run()

        # Extract Gini & Cost
        metrics = extract_metrics("temp", cfg, suppliers, log, 42)
        results_gini.append(metrics["summary"]["share_gini"])
        results_cost.append(metrics["summary"]["cost_mean"])

        print(f"Gamma={g:.1f} -> Gini={results_gini[-1]:.3f}, Cost={results_cost[-1]:.0f}")

    # PLOT PARETO FRONTIER
    fig, ax1 = plt.subplots(figsize=(8, 5))

    color = 'tab:red'
    ax1.set_xlabel('Fairness Weight (Gamma)')
    ax1.set_ylabel('Market Inequality (Gini)', color=color)
    ax1.plot(gammas, results_gini, color=color, marker='o', label="Inequality")
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Avg Procurement Cost ($)', color=color)
    ax2.plot(gammas, results_cost, color=color, marker='s', linestyle='--', label="Cost")
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title("Sensitivity Analysis: The Cost of Fairness")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("figures/fig4_sensitivity.png", dpi=300)
    print("Saved figures/fig4_sensitivity.png")


if __name__ == "__main__":
    run_sensitivity_sweep()