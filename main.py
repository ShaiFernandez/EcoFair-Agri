import json
import random

from simulation import (
    create_suppliers_ABC,
    create_example_buyer,
    EnvironmentalDataModule,
    FairnessModule,
    PolicyScoringModule,
    MarketplaceModule,
    Logger,
    Simulation,
)
from scenarios import SCENARIOS
from metrics import extract_metrics


def run_single(scenario_key: str = "S1", seed: int = 42):
    scenario = SCENARIOS[scenario_key]

    random.seed(seed)
    suppliers = create_suppliers_ABC()
    buyers = [create_example_buyer()]

    env = EnvironmentalDataModule(
        static_co2=5.0,
        individualized_co2={
            "A1": 4.0, "A2": 4.0, "A3": 4.0,
            "B1": 7.0, "B2": 7.0, "B3": 7.0,
            "C1": 10.0, "C2": 10.0, "C3": 10.0
        },
        co2_per_km=0.01,
    )

    fairness = FairnessModule(delta=scenario.delta, eps=1e-9, disp_cap=5.0)
    policy = PolicyScoringModule(scenario)
    marketplace = MarketplaceModule(env, fairness, policy)
    logger = Logger()

    sim = Simulation(
        suppliers=suppliers,
        buyers=buyers,
        env_module=env,
        fairness_module=fairness,
        policy_module=policy,
        marketplace=marketplace,
        logger=logger,
        scenario=scenario,
    )
    sim.run()

    metrics = extract_metrics(
        scenario_key=scenario_key,
        scenario=scenario,
        suppliers=suppliers,
        logger=logger,
        seed=seed,
    )

    # Quick sanity output
    s = metrics["summary"]
    print(f"\nScenario {scenario_key} ({scenario.name})")
    print(f"Total CO2: {s['co2_total_sum']:.2f}")
    print(f"Mean Cost/t: {s['cost_total_mean']:.2f}")
    print(f"Gini(H): {s['share_gini']:.3f} | Max(H): {s['share_max']:.3f}")
    print(f"Total allocated: {s['total_allocated']:.1f}")

    return metrics


if __name__ == "__main__":
    # Change this key anytime for quick testing
    run_single("S3", seed=42)
