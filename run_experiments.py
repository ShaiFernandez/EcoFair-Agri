import json
import random
from typing import Dict, Any

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
from extract_metrics import extract_metrics


def run_one(scenario_key: str, seed: int = 42) -> Dict[str, Any]:
    scenario = SCENARIOS[scenario_key]

    random.seed(seed)                 # makes distances reproducible
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

    return extract_metrics(
        scenario_key=scenario_key,
        scenario=scenario,
        suppliers=suppliers,
        logger=logger,
        seed=seed,
    )


def run_all(seed: int = 42) -> Dict[str, Dict[str, Any]]:
    results = {}
    for key in SCENARIOS.keys():
        results[key] = run_one(key, seed=seed)
    return results


if __name__ == "__main__":
    results = run_all(seed=42)
    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Saved results.json")
