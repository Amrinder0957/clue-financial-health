from app.domain.prediction.simulator import simulate_expense_reduction


def test_expense_reduction_improves_runway():
    result = simulate_expense_reduction(
        current_balance=20000,
        average_daily_inflow=1000,
        average_daily_outflow=3000,
        reduction_percent=20,
    )

    assert result.original_runway_days == 10
    assert round(result.scenario_runway_days, 2) == 14.29
    assert round(result.runway_change_days, 2) == 4.29


def test_large_expense_reduction_stops_depletion():
    result = simulate_expense_reduction(
        current_balance=20000,
        average_daily_inflow=1000,
        average_daily_outflow=2000,
        reduction_percent=50,
    )

    assert result.scenario_runway_days == float("inf")


def test_invalid_reduction():
    try:
        simulate_expense_reduction(
            current_balance=20000,
            average_daily_inflow=1000,
            average_daily_outflow=2000,
            reduction_percent=120,
        )
        assert False
    except ValueError:
        assert True