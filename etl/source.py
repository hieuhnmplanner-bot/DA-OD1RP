# -*- coding: utf-8 -*-
"""Stage 8: nguon (source) cho moi don = Type tu revenue, gan theo UID + ngay mua gan nhat."""
import pandas as pd


def attach_source(orders, revenue):
    o = orders.copy()
    o["payment_N"] = pd.to_datetime(o["payment_N"], errors="coerce")
    rev = revenue.copy()
    rev["Pay Time"] = pd.to_datetime(rev["Pay Time"], errors="coerce")
    rev = rev.dropna(subset=["UID", "Pay Time"]).sort_values("Pay Time")
    o_sorted = o.dropna(subset=["payment_N"]).sort_values("payment_N")
    merged = pd.merge_asof(
        o_sorted, rev[["UID", "Pay Time", "Type", "Sale_pay"]].rename(columns={"Type": "source_type"}),
        left_on="payment_N", right_on="Pay Time", by="UID",
        tolerance=pd.Timedelta(days=14), direction="nearest")
    merged["source_type"] = merged["source_type"].fillna("Other")
    keep = ["UID", "Order ID", "source_type", "Sale_pay"]
    return o.merge(merged[keep].drop_duplicates(["UID", "Order ID"]),
                   on=["UID", "Order ID"], how="left")
