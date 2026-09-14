from app.domain.recommend.recommend import recommend_for_risk


def test_cash_runway_recommendation():
    result = recommend_for_risk("CF-001", "CRITICAL")

    assert result.risk_id == "CF-001"
    assert result.priority == "CRITICAL"
    assert "expenses" in result.action.lower()
    assert "runway" in result.reason.lower()


def test_anomaly_recommendation():
    result = recommend_for_risk("ANOMALY_001", "HIGH")

    assert result.risk_id == "ANOMALY_001"
    assert result.priority == "HIGH"
    assert "transactions" in result.action.lower()
    assert "statistical" in result.reason.lower()


def test_debt_recommendation():
    result = recommend_for_risk("CD-001", "HIGH")

    assert result.risk_id == "CD-001"
    assert result.priority == "HIGH"
    assert "debt" in result.action.lower()


def test_unknown_risk_fallback():
    result = recommend_for_risk("UNKNOWN", "LOW")

    assert result.risk_id == "UNKNOWN"
    assert result.priority == "LOW"
    assert "review" in result.action.lower()