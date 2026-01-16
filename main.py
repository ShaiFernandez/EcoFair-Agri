import json
import random

from simulation import (
    create_farmers_AB,  # Changed from create_suppliers_ABC
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


def run_single(scenario_key: str = "S1", seed: int = 42):
    scenario = SCENARIOS[scenario_key]
    random.seed(seed)

    # USE THE NEW FARMER FUNCTION
    suppliers = create_farmers_AB()
    buyers = [create_example_buyer()]

    # Dummy environmental data module (values are now inside Supplier agents)
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
    print(f"Total Allocated: {s['total_allocated']:.1f}")
    print(f"Gini(Fairness): {s['share_gini']:.3f} (Lower is better)")

    return metrics


if __name__ == "__main__":
    # Test all 3 scenarios to verify the logic
    for s in ["S1", "S2", "S3"]:

        run_single(s, seed=42)
