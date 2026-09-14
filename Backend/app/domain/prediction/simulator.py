from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioResult:
    original_runway_days: float
    scenario_runway_days: float
    runway_change_days: float
    scenario_description: str


def simulate_expense_reduction(
    current_balance: float,
    average_daily_inflow: float,
    average_daily_outflow: float,
    reduction_percent: float,
) -> ScenarioResult:

    if reduction_percent < 0 or reduction_percent > 100:
        raise ValueError("Reduction percentage must be between 0 and 100.")

    original_net_daily = (
        average_daily_inflow - average_daily_outflow
    )

    scenario_outflow = average_daily_outflow * (
        1 - reduction_percent / 100
    )

    scenario_net_daily = (
        average_daily_inflow - scenario_outflow
    )

    if original_net_daily >= 0:
        original_runway = float("inf")
    elif current_balance <= 0:
        original_runway = 0.0
    else:
        original_runway = current_balance / abs(original_net_daily)

    if scenario_net_daily >= 0:
        scenario_runway = float("inf")
    elif current_balance <= 0:
        scenario_runway = 0.0
    else:
        scenario_runway = current_balance / abs(scenario_net_daily)

    if original_runway == float("inf") and scenario_runway == float("inf"):
        change = 0.0
    elif original_runway == float("inf"):
        change = 0.0
    elif scenario_runway == float("inf"):
        change = float("inf")
    else:
        change = scenario_runway - original_runway

    return ScenarioResult(
        original_runway_days=original_runway,
        scenario_runway_days=scenario_runway,
        runway_change_days=change,
        scenario_description=(
            f"Reduce daily expenses by {reduction_percent:.0f}%"
        ),
    )