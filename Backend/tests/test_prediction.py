from app.domain.prediction.prediction import calculate_prediction


def test_cash_depletion_prediction():
    result = calculate_prediction(
        current_balance=20000,
        average_daily_inflow=1000,
        average_daily_outflow=3000,
        balance_trend="DETERIORATING",
        confidence="HIGH",
    )

    assert result.runway_days == 10
    assert result.trend == "DETERIORATING"
    assert "15 days" in result.warning


def test_no_cash_depletion():
    result = calculate_prediction(
        current_balance=50000,
        average_daily_inflow=5000,
        average_daily_outflow=3000,
        balance_trend="IMPROVING",
        confidence="HIGH",
    )

    assert result.runway_days == float("inf")
    assert result.trend == "IMPROVING"


def test_zero_balance():
    result = calculate_prediction(
        current_balance=0,
        average_daily_inflow=1000,
        average_daily_outflow=3000,
        balance_trend="DETERIORATING",
        confidence="LOW",
    )

    assert result.runway_days == 0
    assert result.confidence == "LOW"