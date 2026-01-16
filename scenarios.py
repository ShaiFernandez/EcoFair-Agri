from simulation import ScenarioConfig

# 1. Baseline (Cost-Driven)
S1_BASELINE = ScenarioConfig(
    name="Baseline_CostDriven",
    T=100,
    scarcity_cost_water=0.0,
    scarcity_cost_energy=0.0,
    alpha=1.0, beta=0.0, gamma=0.0,
    use_individualized_lca=False,
    use_fairness=False,
    allocation_mode="sequential",
    delta=0.5,
    # Legacy params
    tau=0.0, w_c=0.0, w_e=0.0, w_f=0.0
)

# 2. Dynamic Taxation (Green-Driven)
S2_TAXATION = ScenarioConfig(
    name="Dynamic_Taxation",
    T=100,
    scarcity_cost_water=0.05,
    scarcity_cost_energy=0.10,
    alpha=1.0, beta=0.0, gamma=0.0,
    use_individualized_lca=True,
    use_fairness=False,
    allocation_mode="sequential",
    delta=0.5,
    # Legacy params
    tau=0.0, w_c=0.0, w_e=0.0, w_f=0.0
)

# 3. Fairness-Aware (Balanced)
S3_FAIRNESS = ScenarioConfig(
    name="Fairness_Aware",
    T=100,
    scarcity_cost_water=0.05,
    scarcity_cost_energy=0.10,
    alpha=0.5, beta=0.2, gamma=0.3,
    use_individualized_lca=True,
    use_fairness=True,
    allocation_mode="proportional",
    delta=0.5,
    # Legacy params
    tau=0.0, w_c=0.0, w_e=0.0, w_f=0.0
)

SCENARIOS = {
    "S1": S1_BASELINE,
    "S2": S2_TAXATION,
    "S3": S3_FAIRNESS,
}