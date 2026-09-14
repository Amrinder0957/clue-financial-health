from app.domain.risk.risk import detect_cash_flow_risks


def test_critical_runway_risk():
    risks = detect_cash_flow_risks(
        runway_days=10,
        ending_balance=10000,
        inflow_outflow_ratio=1.0,
        net_cash_flow=0,
    )

    assert any(
        risk.risk_id == "CF-001"
        and risk.severity == "CRITICAL"
        for risk in risks
    )


def test_operating_deficit_risk():
    risks = detect_cash_flow_risks(
        runway_days=100,
        ending_balance=100000,
        inflow_outflow_ratio=0.50,
        net_cash_flow=-50000,
    )

    assert any(
        risk.risk_id == "CF-002"
        and risk.severity == "CRITICAL"
        for risk in risks
    )


def test_revenue_concentration_risk():
    risks = detect_cash_flow_risks(
        runway_days=100,
        ending_balance=100000,
        inflow_outflow_ratio=1.5,
        net_cash_flow=50000,
        top_inflow_counterparty_ratio=0.80,
    )

    assert any(
        risk.risk_id == "CF-004"
        and risk.severity == "CRITICAL"
        for risk in risks
    )


def test_healthy_cash_flow_has_no_risks():
    risks = detect_cash_flow_risks(
        runway_days=100,
        ending_balance=100000,
        inflow_outflow_ratio=1.5,
        net_cash_flow=50000,
        balance_slope=0,
        average_daily_outflow=1000,
        top_inflow_counterparty_ratio=0.20,
    )

    assert risks == []
from app.domain.risk.risk import detect_anomaly_risks


def test_statistical_outlier():
    risks = detect_anomaly_risks(4.5, 0, 0, 0)
    assert risks[0].risk_id == "ANOMALY-001"
    assert risks[0].severity == "CRITICAL"


def test_round_number_pattern():
    risks = detect_anomaly_risks(0, 25, 0, 0)
    assert any(r.risk_id == "ANOMALY-002" for r in risks)


def test_off_hours_activity():
    risks = detect_anomaly_risks(0, 0, 20, 0)
    assert any(r.risk_id == "ANOMALY-003" for r in risks)


def test_counterparty_concentration():
    risks = detect_anomaly_risks(0, 0, 0, 0.80)
    assert any(r.risk_id == "ANOMALY-004" for r in risks)
from app.domain.risk.risk import detect_credit_debt_risks


def test_high_debt_service_burden():
    risks = detect_credit_debt_risks(
        debt_service_burden=0.50,
        min_balance=50000,
        average_daily_outflow=1000,
        penalty_fee_count=0,
        total_inflow=100000,
        debt_outflow=50000,
    )

    assert any(
        r.risk_id == "CD-001"
        and r.severity == "CRITICAL"
        for r in risks
    )


def test_overdraft_distress():
    risks = detect_credit_debt_risks(
        debt_service_burden=0,
        min_balance=-5000,
        average_daily_outflow=1000,
        penalty_fee_count=0,
        total_inflow=100000,
        debt_outflow=0,
    )

    assert any(
        r.risk_id == "CD-002"
        and r.severity == "CRITICAL"
        for r in risks
    )


def test_penalty_fee_frequency():
    risks = detect_credit_debt_risks(
        debt_service_burden=0,
        min_balance=50000,
        average_daily_outflow=1000,
        penalty_fee_count=4,
        total_inflow=100000,
        debt_outflow=0,
    )

    assert any(
        r.risk_id == "CD-003"
        and r.severity == "CRITICAL"
        for r in risks
    )