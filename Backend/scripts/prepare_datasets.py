import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "datasets")
PROCESSED_DIR = os.path.join(BASE_DIR, "datasets", "processed")

os.makedirs(PROCESSED_DIR, exist_ok=True)

CANONICAL_COLUMNS = [
    "date",
    "amount",
    "direction",
    "description",
    "counterparty",
    "category",
    "account",
    "txn_id",
    "balance",
]


def process_coffee_shop():
    raw_path = os.path.join(RAW_DIR, "checking_account_main.csv")
    out_path = os.path.join(PROCESSED_DIR, "small_business_good.csv")

    if not os.path.exists(raw_path):
        print("Skipping Dataset 1: file not found.")
        return

    df = pd.read_csv(raw_path)

    df["txn_id"] = df["transaction_id"]
    df["direction"] = df["type"].astype(str).str.lower()
    df["account"] = "Checking Account"
    df["counterparty"] = ""

    df_out = df[CANONICAL_COLUMNS]
    df_out.to_csv(out_path, index=False)

    print(f"Saved: {out_path} ({len(df_out)} rows)")


def process_indian_banking():
    raw_path = os.path.join(
    RAW_DIR,
    "transactions_Dataset.csv"
)

    if not os.path.exists(raw_path):
        print("Skipping Dataset 2: file not found.")
        return

    df = pd.read_csv(raw_path)

    df["date"] = pd.to_datetime(
        df["transaction_date"],
        errors="coerce"
    )

    df = df.dropna(subset=["date"])

    # Find a customer with enough transactions AND enough date coverage.
    customer_stats = (
        df.groupby("customer_id")["date"]
        .agg(["count", "min", "max"])
        .reset_index()
    )

    customer_stats["days"] = (
        customer_stats["max"] - customer_stats["min"]
    ).dt.days

    candidates = customer_stats[
        (customer_stats["count"] >= 20) &
        (customer_stats["days"] >= 30)
    ]

    if len(candidates) == 0:
        # Fallback: use a 60-day overall subset.
        start_date = df["date"].min()
        df_sub = df[
            (df["date"] >= start_date) &
            (df["date"] <= start_date + pd.Timedelta(days=60))
        ].copy()

        selected_customer = "multiple"
    else:
        # Choose the customer with the most transactions.
        selected_customer = candidates.sort_values(
            "count",
            ascending=False
        ).iloc[0]["customer_id"]

        customer_df = df[
            df["customer_id"] == selected_customer
        ].copy()

        start_date = customer_df["date"].min()

        df_sub = customer_df[
            (customer_df["date"] >= start_date) &
            (customer_df["date"] <= start_date + pd.Timedelta(days=60))
        ].copy()

    df_sub["date"] = df_sub["date"].dt.strftime("%Y-%m-%d")
    df_sub["amount"] = pd.to_numeric(
        df_sub["transaction_amount"],
        errors="coerce"
    )
    df_sub["direction"] = (
        df_sub["transaction_direction"]
        .astype(str)
        .str.lower()
    )
    df_sub["description"] = df_sub["transaction_type"]
    df_sub["category"] = df_sub["merchant_category"]
    df_sub["txn_id"] = df_sub["transaction_id"]
    df_sub["account"] = df_sub["account_type"]
    df_sub["balance"] = pd.to_numeric(
        df_sub["account_balance"],
        errors="coerce"
    )
    df_sub["counterparty"] = (
        df_sub["customer_id"].astype(str)
    )

    df_out = df_sub[CANONICAL_COLUMNS]
    df_out.to_csv(out_path, index=False)

    print(
        f"Saved: {out_path} "
        f"({len(df_out)} rows, customer {selected_customer})"
    )


def process_high_risk():
    # CORRECT filename
    raw_path = os.path.join(
        RAW_DIR,
        "Fraud Detection Dataset.csv"
    )

    out_path = os.path.join(
        PROCESSED_DIR,
        "high_risk.csv"
    )

    if not os.path.exists(raw_path):
        print("Skipping Dataset 3: file not found.")
        return

    df = pd.read_csv(raw_path)

    df["debit"] = pd.to_numeric(
        df["debit"],
        errors="coerce"
    ).fillna(0)

    df["credit"] = pd.to_numeric(
        df["credit"],
        errors="coerce"
    ).fillna(0)

    # Convert debit/credit into CLUE's amount + direction.
    df["amount"] = df["credit"]
    df["direction"] = "in"

    debit_mask = df["credit"] <= 0

    df.loc[debit_mask, "amount"] = df.loc[
        debit_mask, "debit"
    ]

    df.loc[debit_mask, "direction"] = "out"

    df["date"] = pd.to_datetime(
        df["date"],
        dayfirst=True,
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df["description"] = df["description"]
    df["counterparty"] = ""
    df["category"] = ""
    df["account"] = "Bank Account"
    df["txn_id"] = [
        f"HIGH-RISK-{i+1:06d}"
        for i in range(len(df))
    ]
    df["balance"] = pd.to_numeric(
        df["balance"],
        errors="coerce"
    )

    df["fraud_label"] = df["isSuspicious"]

    cols = CANONICAL_COLUMNS + ["fraud_label"]

    df_out = df[cols]
    df_out.to_csv(out_path, index=False)

    print(
        f"Saved: {out_path} "
        f"({len(df_out)} rows)"
    )


if __name__ == "__main__":
    print("Preparing datasets for CLUE...")

    process_coffee_shop()
    process_indian_banking()
    process_high_risk()

    print("Processing complete.")