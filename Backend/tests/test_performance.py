import pandas as pd

from app.domain.performance.performance import calculate_business_performance


def test_profitable_business():
    data = [
        {"date": "2026-01-05", "amount": 10000.0, "direction": "in"},
        {"date": "2026-01-10", "amount": 4000.0, "direction": "out"},
    ]

    result = calculate_business_performance(pd.DataFrame(data))

    assert result["summary"]["revenue"] == 10000.0
    assert result["summary"]["expenses"] == 4000.0
    assert result["summary"]["net_profit"] == 6000.0
    assert result["summary"]["profit_margin_pct"] == 60.0
    assert result["summary"]["status"] == "Profitable"


def test_loss_making_business():
    data = [
        {"date": "2026-02-01", "amount": 2000.0, "direction": "in"},
        {"date": "2026-02-15", "amount": 5000.0, "direction": "out"},
    ]

    result = calculate_business_performance(pd.DataFrame(data))

    assert result["summary"]["revenue"] == 2000.0
    assert result["summary"]["expenses"] == 5000.0
    assert result["summary"]["net_profit"] == -3000.0
    assert result["summary"]["profit_margin_pct"] == -150.0
    assert result["summary"]["status"] == "Loss-making"


def test_zero_revenue():
    data = [
        {"date": "2026-03-01", "amount": 0.0, "direction": "in"},
        {"date": "2026-03-05", "amount": 1500.0, "direction": "out"},
    ]

    result = calculate_business_performance(pd.DataFrame(data))

    assert result["summary"]["revenue"] == 0.0
    assert result["summary"]["expenses"] == 1500.0
    assert result["summary"]["net_profit"] == -1500.0
    assert result["summary"]["profit_margin_pct"] == 0.0
    assert result["summary"]["status"] == "Loss-making"


def test_empty_dataset():
    result = calculate_business_performance(pd.DataFrame())

    assert result["summary"]["revenue"] == 0.0
    assert result["summary"]["expenses"] == 0.0
    assert result["summary"]["net_profit"] == 0.0
    assert result["summary"]["profit_margin_pct"] == 0.0
    assert result["summary"]["status"] == "Break-even"
    assert result["monthly_trends"] == []


def test_monthly_aggregation_and_invalid_dates():
    data = [
        {"date": "2026-01-10", "amount": 5000.0, "direction": "in"},
        {"date": "2026-01-20", "amount": 2000.0, "direction": "out"},
        {"date": "2026-02-05", "amount": 8000.0, "direction": "in"},
        {"date": "2026-02-12", "amount": 3000.0, "direction": "out"},
        {"date": "invalid-date", "amount": 1000.0, "direction": "in"},
    ]

    result = calculate_business_performance(pd.DataFrame(data))

    assert result["summary"]["revenue"] == 14000.0
    assert result["summary"]["expenses"] == 5000.0
    assert result["summary"]["net_profit"] == 9000.0

    trends = result["monthly_trends"]

    assert len(trends) == 2

    assert trends[0]["month"] == "2026-01"
    assert trends[0]["revenue"] == 5000.0
    assert trends[0]["expenses"] == 2000.0
    assert trends[0]["net_profit"] == 3000.0

    assert trends[1]["month"] == "2026-02"
    assert trends[1]["revenue"] == 8000.0
    assert trends[1]["expenses"] == 3000.0
    assert trends[1]["net_profit"] == 5000.0