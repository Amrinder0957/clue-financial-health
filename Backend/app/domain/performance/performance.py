from typing import Any, Dict

import pandas as pd


def calculate_business_performance(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates a cash-based business performance view from
    normalized transaction data.

    This is NOT a formal accounting or GAAP Profit & Loss statement.
    """

    if df.empty:
        return {
            "summary": {
                "revenue": 0.0,
                "expenses": 0.0,
                "net_profit": 0.0,
                "profit_margin_pct": 0.0,
                "status": "Break-even",
            },
            "monthly_trends": [],
        }

    df_clean = df.copy()

    if "amount" not in df_clean.columns:
        df_clean["amount"] = 0.0

    df_clean["amount"] = pd.to_numeric(
        df_clean["amount"], errors="coerce"
    ).fillna(0.0)

    if "direction" not in df_clean.columns:
        df_clean["direction"] = ""

    inflows = df_clean.loc[
        df_clean["direction"] == "in", "amount"
    ].sum()

    outflows = df_clean.loc[
        df_clean["direction"] == "out", "amount"
    ].sum()

    revenue = round(float(inflows), 2)
    expenses = round(float(outflows), 2)
    net_profit = round(revenue - expenses, 2)

    if revenue > 0:
        profit_margin_pct = round(
            (net_profit / revenue) * 100.0, 2
        )
    else:
        profit_margin_pct = 0.0

    if net_profit > 0:
        status = "Profitable"
    elif net_profit < 0:
        status = "Loss-making"
    else:
        status = "Break-even"

    monthly_trends = []

    if "date" in df_clean.columns:
        df_clean["date_parsed"] = pd.to_datetime(
            df_clean["date"], errors="coerce"
        )

        valid_dates = df_clean.dropna(
            subset=["date_parsed"]
        ).copy()

        if not valid_dates.empty:
            valid_dates["month"] = (
                valid_dates["date_parsed"]
                .dt.strftime("%Y-%m")
            )

            for month, group in valid_dates.groupby("month"):
                month_revenue = round(
                    float(
                        group.loc[
                            group["direction"] == "in",
                            "amount",
                        ].sum()
                    ),
                    2,
                )

                month_expenses = round(
                    float(
                        group.loc[
                            group["direction"] == "out",
                            "amount",
                        ].sum()
                    ),
                    2,
                )

                month_net = round(
                    month_revenue - month_expenses, 2
                )

                monthly_trends.append(
                    {
                        "month": month,
                        "revenue": month_revenue,
                        "expenses": month_expenses,
                        "net_profit": month_net,
                    }
                )

            monthly_trends.sort(
                key=lambda item: item["month"]
            )

    return {
        "summary": {
            "revenue": revenue,
            "expenses": expenses,
            "net_profit": net_profit,
            "profit_margin_pct": profit_margin_pct,
            "status": status,
        },
        "monthly_trends": monthly_trends,
    }