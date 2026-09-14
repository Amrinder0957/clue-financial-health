from app.application.pipeline import run_data_pipeline

csv = """date,amount,direction
2024-03-01,"? 1,23,456.78",in
2024-03-02,"Rs. 2,000",out
2024-03-03,"INR 50.25",in
2024-03-04,"(1,000.00)",out
"""

ledger = run_data_pipeline(csv.encode("utf-8"), "ledger.csv")

print("TRANSACTIONS:")
for txn in ledger.transactions:
    print(txn.source_row, txn.amount)

print("\nQUARANTINED:")
for row in ledger.quarantined:
    print(row.source_row, row.reason)
