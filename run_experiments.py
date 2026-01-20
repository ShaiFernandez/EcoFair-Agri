import json
import random
from typing import Dict, Any

from simulation import (
    create_farmers_AB,
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

    random.seed(seed)
    suppliers = create_farmers_AB()
    buyers = [create_example_buyer()]

    # Dummy environment (values are in Supplier now)
    env = EnvironmentalDataModule(
        static_co2=0.0,
        individualized_co2={},
        co2_per_km=0.0,
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
    # Only run the relevant scenarios
    for key in ["S1", "S2", "S3"]:
        print(f"Running {key}...")
        results[key] = run_one(key, seed=seed)
    return results

if __name__ == "__main__":
    results = run_all(seed=42)
    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Saved results.json")