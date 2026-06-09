# -*- coding: utf-8 -*-
"""DA-OD1RP standalone pipeline: file tho -> outputs/dashboard_data.csv (KHONG DB/gsheet).

Chay:  python run_etl.py            (day du, co pace - cham vi doc file 77MB)
       python run_etl.py --no-pace  (nhanh, bo qua toc do hoc thuc te)
"""
import sys
import pandas as pd
import numpy as np
from config import find_latest_files, OUTPUT_DIR
from etl import ingest, due_date, dims, source as src_mod

NO_PACE = "--no-pace" in sys.argv


def main():
    lat = find_latest_files(require_today=False)
    print("Files:", {k: v.split("/")[-1].split("\\")[-1] for k, v in lat.items()})

    # 1-2. Ingest
    revenue = ingest.load_revenue(lat)
    rl = ingest.load_remaining_lesson(lat)

    # 3-5. Due date + value_chain + status
    orders = due_date.build_orders(rl)
    orders = due_date.recompute_status_renew(orders, revenue)  # renewal tinh ca tu doanh thu

    # [GIONG DA1RP] Loai don gia tri thap: end_date >= 2026-02-01 VA gia < 300.000d
    _price = pd.to_numeric(orders["Order Price VND"], errors="coerce").fillna(0)
    _drop = (orders["end_date_N"] >= pd.Timestamp("2026-02-01")) & (_price < 300000)
    orders = orders[~_drop].reset_index(drop=True)
    print(f"  Loai {int(_drop.sum())} don gia tri thap (giong DA1RP)")

    # 6. Team (tu dim_sale)
    team_map = dims.load_team_map()
    orders["team"] = dims.map_team(orders["Sale"], team_map)

    # 8. Source
    orders = src_mod.attach_source(orders, revenue)

    # 7. Pace (tuy chon - doc file 77MB)
    orders["lessons_per_week_real"] = np.nan
    if not NO_PACE and lat.get("complete_homework_data"):
        try:
            from etl import pace
            pdf = pace.compute_pace(lat["complete_homework_data"])[["UID", "lessons_per_week_real"]]
            orders = orders.drop(columns=["lessons_per_week_real"]).merge(pdf, on="UID", how="left")
            print("  pace: gan cho", int(orders["lessons_per_week_real"].notna().sum()), "don")
        except Exception as e:
            if "lessons_per_week_real" not in orders.columns:
                orders["lessons_per_week_real"] = np.nan
            print("  pace bo qua (loi/cham):", e)

    # 9. Chuan hoa ve schema dashboard
    out = pd.DataFrame()
    out["uid"] = orders["UID"].astype(str)
    out["team"] = orders["team"].fillna("Other")
    out["sale"] = orders["Sale"].fillna("")
    out["teacher"] = orders.get("Teacher", "").fillna("")
    out["package"] = orders.get("Package Name", "").fillna("")
    out["order_id"] = orders["Order ID"].astype(str)
    out["value_chain"] = orders["value_chain"]
    out["vc_order_num"] = orders["vc_order_num"]
    out["end_date"] = pd.to_datetime(orders["end_date_N"], errors="coerce")
    out["end_month"] = orders["month_end_date"]
    out["pay_month"] = pd.to_datetime(orders["payment_N"], errors="coerce").dt.strftime("%Y-%m")
    out["real_money"] = pd.to_numeric(orders.get("Order Price VND"), errors="coerce").fillna(0)
    out["status"] = orders["type_lesson"]
    out["account_status"] = orders["account_status"]
    out["status_renew"] = orders["status_renew"]
    out["remain_lesson"] = pd.to_numeric(orders["Remain_Lesson"], errors="coerce")
    out["order_num"] = pd.to_numeric(orders["order_num"], errors="coerce")
    out["purchase_time"] = pd.to_datetime(orders["payment_N"], errors="coerce")
    out["source_type"] = orders.get("source_type", "Other")
    if "lessons_per_week_real" not in orders.columns:
        orders["lessons_per_week_real"] = np.nan
    out["lessons_per_week_real"] = orders["lessons_per_week_real"]

    # renewed = da gia han theo DA1RP: status_renew thuoc {Early, On-time, Late}
    out = out.sort_values(["uid", "value_chain", "vc_order_num"])
    out["renewed"] = out["status_renew"].isin(["Early Renewal", "On-time Renewal", "Late Renewal"])
    # ngay mua don ke tiep cung chain (de tinh timing)
    pay_dt = pd.to_datetime(orders.set_index([orders["UID"].astype(str), orders["Order ID"].astype(str)])["payment_N"], errors="coerce")
    out["_pay_dt"] = pd.to_datetime(orders["payment_N"].values, errors="coerce")
    out["next_pay_dt"] = out.groupby(["uid", "value_chain"])["_pay_dt"].shift(-1)
    out["next_pay_month"] = out["next_pay_dt"].dt.strftime("%Y-%m")
    out["days_to_renew"] = (out["next_pay_dt"] - out["end_date"]).dt.days

    def timing(x):
        if pd.isna(x): return ""
        if x < -7: return "Som (truoc han)"
        if x <= 7: return "Dung han"
        if x <= 90: return "Tre"
        return "Rat tre (>90d)"
    out["renew_timing"] = out["days_to_renew"].apply(timing)
    out = out.drop(columns=["_pay_dt", "next_pay_dt"])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    full = OUTPUT_DIR / "orders_full.csv"
    dash = OUTPUT_DIR / "dashboard_data.csv"
    orders.to_csv(full, index=False, encoding="utf-8-sig")
    out.to_csv(dash, index=False, encoding="utf-8-sig")
    print(f"\nDa ghi:\n  {full}  ({len(orders)} don, full cols)\n  {dash}  ({len(out)} don, schema dashboard)")
    print("end_month range:", out["end_month"].dropna().min(), "->", out["end_month"].dropna().max())


if __name__ == "__main__":
    main()
