from app.domain.explain.explain import explain_risk


def test_cash_runway_explanation():
    result = explain_risk(
        "CF-001",
        "CRITICAL",
        {"runway_days": 11},
    )

    assert result.title == "Cash Runway Risk"
    assert "11.0 days" in result.explanation


def test_anomaly_explanation():
    result = explain_risk(
        "ANOMALY_001",
        "HIGH",
        {"max_z_score_amount": 4.2},
    )

    assert result.title == "Unusual Transaction Amount"
    assert "4.20" in result.explanation


def test_debt_explanation():
    result = explain_risk(
        "CD-001",
        "HIGH",
        {"debt_service_burden": 0.32},
    )

    assert result.title == "Debt Service Burden"
    assert "32%" in result.explanation


def test_unknown_risk_has_fallback():
    result = explain_risk(
        "UNKNOWN",
        "LOW",
        {},
    )

    assert result.title == "Financial Risk"
    assert "uploaded financial data" in result.explanation