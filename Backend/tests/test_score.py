from app.domain.score.score import (
    score_runway,
    score_inflow_outflow_ratio,
    calculate_cash_flow_score,
    calculate_anomaly_score,
    score_debt_service_burden,
    calculate_overall_score,
)


def test_runway_scoring():
    assert score_runway(100) == 100
    assert score_runway(60) == 80
    assert score_runway(20) == 50
    assert score_runway(10) == 20
    assert score_runway(0) == 0


def test_ratio_scoring():
    assert score_inflow_outflow_ratio(1.5) == 100
    assert score_inflow_outflow_ratio(1.1) == 80
    assert score_inflow_outflow_ratio(0.9) == 50
    assert score_inflow_outflow_ratio(0.5) == 20


def test_cash_flow_score():
    # Runway 20 = 50
    # Ratio 1.1 = 80
    # Average = 65
    assert calculate_cash_flow_score(20, 1.1) == 65


def test_anomaly_score():
    # 2 z-score + 1 round-number + 1 off-hours
    # 100 - 20 - 5 - 5 = 70
    assert calculate_anomaly_score(2, 1, 1) == 70


def test_debt_score():
    assert score_debt_service_burden(0.10, 100000, 10000) == 90
    assert score_debt_service_burden(0.25, 100000, 25000) == 70
    assert score_debt_service_burden(0.40, 100000, 40000) == 40
    assert score_debt_service_burden(0.50, 100000, 50000) == 0


def test_overall_score():
    result = calculate_overall_score(
        cash_flow_score=80,
        anomaly_score=100,
        credit_debt_score=70,
    )

    assert result.overall_score == 83
    assert result.band == "Stable"