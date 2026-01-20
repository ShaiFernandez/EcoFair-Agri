# EcoFair-Agri

**EcoFair-Agri** is an agent-based simulation framework designed to evaluate the trade-offs between economic efficiency, environmental sustainability, and social fairness in agricultural supply chains.

The project simulates a marketplace of agricultural suppliers (farmers) and buyers to analyze how different policy interventions—such as environmental taxation and fairness-aware algorithms—impact market inequality (Gini coefficient), resource usage (Water/Energy), food waste, and supply chain resilience.

## 🚀 Key Features

* **Multi-Agent Simulation**: Models interactions between different types of suppliers (e.g., Indoor/Type A vs. Outdoor/Type B) and buyers.
* **Scenario Analysis**: Compares three distinct market configurations:
    * **S1 (Baseline)**: Purely cost-driven optimization.
    * **S2 (Taxation)**: Incorporates environmental taxes based on water and energy footprints.
    * **S3 (Fairness)**: A balanced approach optimizing for cost, sustainability, and supplier equity.
* **Fairness Metrics**: Calculates the Gini coefficient to measure market inequality and uses a "Fairness Module" to distribute contracts more equitably.
* **Environmental Impact**: Tracks water usage, energy consumption, and carbon footprints.
* **Resilience Testing**: Simulates seasonal disruptions (e.g., "Winter Collapse") and weather shocks (droughts) to test supply chain security.
* **Visualization**: Automatically generates plots for market share, inequality, supply resilience, and waste generation.

## 📂 Project Structure

* `main.py`: Main entry point for running single simulation tests.
* `run_experiments.py`: Runs the full suite of scenarios (S1, S2, S3) and saves data to `results.json`.
* `simulation.py`: Core logic containing agent definitions (`Supplier`, `Buyer`), `MarketplaceModule`, `FairnessModule`, and the simulation loop.
* `scenarios.py`: Configuration details for the three primary scenarios (Baseline, Taxation, Fairness).
* `extract_metrics.py`: Helper functions to calculate Gini coefficients, waste, and aggregated costs from simulation logs.
* `plot_results.py`: Generates visualization figures (Market Share, Gini, Time-series resilience) from `results.json`.
* `run_sensitivity.py`: Performs sensitivity analysis on the fairness weight (Gamma) and plots the Pareto frontier.
* `make_table.py`: Converts simulation results into LaTeX table format.

## ⚙️ Scenarios

The simulation compares three primary policy scenarios defined in `scenarios.py`:

| Scenario | Name | Description | Allocation Mode |
| :--- | :--- | :--- | :--- |
| **S1** | Baseline (Cost-Driven) | Minimizes procurement cost only. Favors cheap, outdoor producers. | Sequential |
| **S2** | Dynamic Taxation | Adds tax penalties for high water/energy use. Shifts demand to eco-friendly options. | Sequential |
| **S3** | Fairness-Aware | Balances Cost, Reputation, and Fairness. Uses proportional allocation to support smaller farms. | Proportional |

## 📦 Installation & Usage

### Prerequisites
You will need Python 3.x and the following libraries:
```bash
pip install numpy matplotlib
