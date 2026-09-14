from app.application.analysis_service import build_analysis_report


def test_analysis_report_from_csv():
    content = b"""date,amount,direction,description,counterparty,category
2026-01-01,10000,in,Sales payment,Customer A,Sales
2026-01-02,3000,out,Office expense,Supplier A,Expense
2026-01-03,5000,in,Sales payment,Customer B,Sales
2026-01-04,2000,out,Utilities,Electricity,Expense
"""

    report = build_analysis_report(
        content=content,
        filename="test.csv",
    )

    assert report.features.transaction_count == 4
    assert report.score is not None
    assert report.prediction is not None
    assert isinstance(report.risks, list)
    assert isinstance(report.explanations, list)
    assert isinstance(report.recommendations, list)


def test_analysis_report_handles_small_dataset():
    content = b"""date,amount,direction,description,counterparty,category
2026-01-01,10000,in,Sales payment,Customer A,Sales
2026-01-02,2000,out,Office expense,Supplier A,Expense
"""

    report = build_analysis_report(
        content=content,
        filename="small.csv",
    )

    assert report.features.transaction_count == 2
    assert report.score is not None
    assert report.prediction is not None