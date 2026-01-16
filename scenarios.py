from simulation import ScenarioConfig

# states τ > 0 for carbon pricing scenarios, but does not fix a numeric value.
# Choose a positive value used in your experiments and keep it constant.
TAU_CARBON = 1.0

# Paper states the default value used in scenarios is δ = 0.5.
DELTA_DEFAULT = 0.5

# -------------------------
# S1: Baseline (Cost-Driven, Static LCA)
# Table I: τ=0, wf=0, Seq, Static, ranking (1,0,0)
# -------------------------
S1_BASELINE = ScenarioConfig(
    name="S1_Baseline",
    T=200,
    tau=0.0,
    w_c=1.0, w_e=0.0, w_f=0.0,
    alpha=1.0, beta=0.0, gamma=0.0,   # allocation weights not used in sequential scenarios (Table I shows “–”)
    delta=DELTA_DEFAULT,
    use_individualized_lca=False,      # Static LCA
    use_fairness=False,
    allocation_mode="sequential",
)


# -------------------------
# S2A: Carbon Pricing + Static LCA
# Table I: τ>0, wf=0, Seq, Static, ranking (1,0,0)
# -------------------------
S2A_CARBON_STATIC = ScenarioConfig(
    name="S2A_CarbonPricing_StaticLCA",
    T=200,
    tau=TAU_CARBON,
    w_c=1.0, w_e=0.0, w_f=0.0,
    alpha=1.0, beta=0.0, gamma=0.0,   # not used in sequential scenarios (Table I shows “–”)
    delta=DELTA_DEFAULT,
    use_individualized_lca=False,      # Static LCA
    use_fairness=False,
    allocation_mode="sequential",
)


# -------------------------
# S2B: Carbon Pricing + Individualized LCA
# Table I: τ>0, wf=0, Seq, Indiv, ranking (1,0,0)
# -------------------------
S2B_CARBON_INDIV = ScenarioConfig(
    name="S2B_CarbonPricing_IndividualizedLCA",
    T=200,
    tau=TAU_CARBON,
    w_c=1.0, w_e=0.0, w_f=0.0,
    alpha=1.0, beta=0.0, gamma=0.0,   # not used in sequential scenarios (Table I shows “–”)
    delta=DELTA_DEFAULT,
    use_individualized_lca=True,       # Individualized LCA
    use_fairness=False,
    allocation_mode="sequential",
)


# -------------------------
# S3: Fairness-Oriented Allocation (Individualized LCA)
# Table I: τ=0, wf>0, Prop, Indiv
# Allocation weights: (1/3, 1/3, 1/3)
# Ranking weights:   (1/3, 1/3, 1/3)
# -------------------------
S3_FAIRNESS = ScenarioConfig(
    name="S3_FairnessOriented_IndividualizedLCA",
    T=200,
    tau=0.0,
    w_c=1.0/3.0, w_e=1.0/3.0, w_f=1.0/3.0,
    alpha=1.0/3.0, beta=1.0/3.0, gamma=1.0/3.0,
    delta=DELTA_DEFAULT,
    use_individualized_lca=True,
    use_fairness=True,
    allocation_mode="proportional",
)


# -------------------------
# S4: Combined Policy (Carbon Pricing + Fairness, Individualized LCA)
# Table I: τ>0, wf>0, Prop, Indiv
# Allocation weights: (0.3, 0.4, 0.3)
# Ranking weights:   (0.3, 0.4, 0.3)
# -------------------------
S4A_COMBINED_BALANCE = ScenarioConfig(
    name="S4_Combined_CarbonPricingPlusFairness_IndividualizedLCA_Balance",
    T=200,
    tau=TAU_CARBON,
    w_c=0.3, w_e=0.4, w_f=0.3,
    alpha=0.3, beta=0.4, gamma=0.3,
    delta=DELTA_DEFAULT,
    use_individualized_lca=True,
    use_fairness=True,
    allocation_mode="proportional",
)


# -------------------------
# S4: Combined Policy (Carbon Pricing + Fairness, Individualized LCA)
# Table I: τ>0, wf>0, Prop, Indiv
# Allocation weights: (0.3, 0.4, 0.3)
# Ranking weights:   (0.3, 0.4, 0.3)
# -------------------------
S4B_COMBINED_DISPARITY = ScenarioConfig(
    name="S4_Combined_CarbonPricingPlusFairness_IndividualizedLCA_Disparity",
    T=200,
    tau=TAU_CARBON,
    w_c=0.3, w_e=0.4, w_f=0.3,
    alpha=0.3, beta=0.4, gamma=0.3,
    delta=0,                        # disparity-only
    use_individualized_lca=True,
    use_fairness=True,
    allocation_mode="proportional",
)


# -------------------------
# S4: Combined Policy (Carbon Pricing + Fairness, Individualized LCA)
# Table I: τ>0, wf>0, Prop, Indiv
# Allocation weights: (0.3, 0.4, 0.3)
# Ranking weights:   (0.3, 0.4, 0.3)
# -------------------------
S4C_COMBINED_ROTATION = ScenarioConfig(
    name="S4_Combined_CarbonPricingPlusFairness_IndividualizedLCA_Rotation",
    T=200,
    tau=TAU_CARBON,
    w_c=0.3, w_e=0.4, w_f=0.3,
    alpha=0.3, beta=0.4, gamma=0.3,
    delta=1,                        # rotation-only
    use_individualized_lca=True,
    use_fairness=True,
    allocation_mode="proportional",
)


# -------------------------
# Scenario registry (select by key in main.py)
# -------------------------
SCENARIOS = {
    "S1": S1_BASELINE,
    "S2A": S2A_CARBON_STATIC,
    "S2B": S2B_CARBON_INDIV,
    "S3": S3_FAIRNESS,
    "S4A": S4A_COMBINED_BALANCE,
    "S4B": S4B_COMBINED_DISPARITY,
    "S4C": S4C_COMBINED_ROTATION,
}