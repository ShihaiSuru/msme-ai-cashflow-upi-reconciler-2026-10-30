"""
MSME AI Cash-Flow UPI Reconciler — Starter Script
Demonstrates practical matching of UPI payments to invoices and a simple cash-flow forecast.
Designed for Indian MSMEs; extend with real data sources as needed.
"""

import pandas as pd
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Sample data (replace with real CSV loads or API calls later)
# ---------------------------------------------------------------------------

# Open invoices (typical MSME sales invoices)
invoices = pd.DataFrame([
    {"invoice_id": "INV-204", "customer": "Modern Apparels", "amount": 21240, "due_date": "2026-10-18", "status": "open"},
    {"invoice_id": "INV-205", "customer": "Spice Traders",     "amount": 8750,  "due_date": "2026-10-15", "status": "open"},
    {"invoice_id": "INV-206", "customer": "Urban Hardware",    "amount": 15600, "due_date": "2026-11-05", "status": "open"},
    {"invoice_id": "INV-207", "customer": "Green Foods",       "amount": 9800,  "due_date": "2026-10-25", "status": "open"},
])

# Recent UPI credits received
upi_txns = pd.DataFrame([
    {"txn_id": "UPI-8812", "date": "2026-10-17", "amount": 21240, "note": "INV-204 Modern", "payer": "Modern Apparels"},
    {"txn_id": "UPI-8813", "date": "2026-10-20", "amount": 15600, "note": "Payment Urban",  "payer": "Urban Hardware"},
    {"txn_id": "UPI-8814", "date": "2026-10-22", "amount": 12400, "note": "Advance",        "payer": "New Client"},
    {"txn_id": "UPI-8815", "date": "2026-10-28", "amount": 9800,  "note": "INV-207",        "payer": "Green Foods"},
])

# Known near-term outflows (vendors, rent, etc.)
outflows = pd.DataFrame([
    {"desc": "Vendor payment — fabric", "amount": 18000, "due": "2026-11-08"},
    {"desc": "Shop rent",                "amount": 12000, "due": "2026-11-01"},
    {"desc": "Electricity + GST",        "amount": 4500,  "due": "2026-11-10"},
])

# ---------------------------------------------------------------------------
# Reconciliation logic (simple exact + note matching; ready for fuzzy upgrade)
# ---------------------------------------------------------------------------

def reconcile(invoices_df: pd.DataFrame, upi_df: pd.DataFrame) -> pd.DataFrame:
    """Match UPI credits to invoices by amount and optional note reference."""
    results = []
    matched_invoices = set()

    for _, txn in upi_df.iterrows():
        match = invoices_df[
            (invoices_df["amount"] == txn["amount"]) &
            (~invoices_df["invoice_id"].isin(matched_invoices))
        ]

        # Prefer match if invoice ID appears in the UPI note
        if not match.empty:
            note_match = match[match["invoice_id"].apply(lambda x: x in str(txn["note"]))]
            if not note_match.empty:
                match = note_match

        if not match.empty:
            inv = match.iloc[0]
            results.append({
                "txn_id": txn["txn_id"],
                "amount": txn["amount"],
                "matched_invoice": inv["invoice_id"],
                "customer": inv["customer"],
                "status": "matched"
            })
            matched_invoices.add(inv["invoice_id"])
        else:
            results.append({
                "txn_id": txn["txn_id"],
                "amount": txn["amount"],
                "matched_invoice": None,
                "customer": txn["payer"],
                "status": "unmatched"
            })

    return pd.DataFrame(results)

# ---------------------------------------------------------------------------
# Cash-flow forecast (next 30 days)
# ---------------------------------------------------------------------------

def forecast_cashflow(reconciled: pd.DataFrame, invoices_df: pd.DataFrame, outflows_df: pd.DataFrame) -> dict:
    """Simple 30-day view: expected collections vs known outflows."""
    today = datetime(2026, 10, 30)
    horizon = today + timedelta(days=30)

    # Expected inflows: unmatched open invoices due within horizon
    open_inv = invoices_df[invoices_df["status"] == "open"].copy()
    open_inv["due_date"] = pd.to_datetime(open_inv["due_date"])
    expected_in = open_inv[open_inv["due_date"] <= horizon]["amount"].sum()

    # Add any unmatched UPI as immediate inflow
    unmatched_upi = reconciled[reconciled["status"] == "unmatched"]["amount"].sum()

    # Outflows due in horizon
    outflows_df["due"] = pd.to_datetime(outflows_df["due"])
    expected_out = outflows_df[outflows_df["due"] <= horizon]["amount"].sum()

    net = unmatched_upi + expected_in - expected_out

    return {
        "unmatched_upi_inflow": unmatched_upi,
        "expected_invoice_collections": expected_in,
        "expected_outflows": expected_out,
        "net_30_day": net,
        "gap": max(0, -net)
    }

# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("MSME AI Cash-Flow UPI Reconciler — Demo")
    print("Date: 30 October 2026")
    print("=" * 60)

    reconciled = reconcile(invoices, upi_txns)
    print("\nReconciliation Results:")
    print(reconciled.to_string(index=False))

    overdue = invoices[pd.to_datetime(invoices["due_date"]) < datetime(2026, 10, 30)]
    if not overdue.empty:
        print("\nOverdue Invoices:")
        print(overdue[["invoice_id", "customer", "amount", "due_date"]].to_string(index=False))

    fc = forecast_cashflow(reconciled, invoices, outflows)
    print("\n30-Day Cash-Flow Forecast:")
    print(f"  Unmatched UPI already received : ₹{fc['unmatched_upi_inflow']:,.0f}")
    print(f"  Expected invoice collections   : ₹{fc['expected_invoice_collections']:,.0f}")
    print(f"  Expected outflows              : ₹{fc['expected_outflows']:,.0f}")
    print(f"  Net position                   : ₹{fc['net_30_day']:,.0f}")
    if fc["gap"] > 0:
        print(f"  ⚠ Cash-flow gap               : ₹{fc['gap']:,.0f}")
        print("  Suggested action: Follow up on overdue invoices and review short-term working-capital options.")
    else:
        print("  ✓ No immediate gap projected.")

    print("\n---")
    print("This is a starter demo. Replace sample data with real UPI statements and GST invoices.")
    print("Next: add fuzzy matching, Account Aggregator integration, or a simple ML delay predictor.")

if __name__ == "__main__":
    main()
