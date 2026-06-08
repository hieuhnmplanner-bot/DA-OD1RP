# -*- coding: utf-8 -*-
"""
Chuan hoa du lieu don hang -> dashboard_data.csv (dung cho app.py / Streamlit).

Nguon (uu tien):
  1) DA1RP export da co value-chain  (remaining_lesson_with_vc.csv) -- production
  2) OD1RP detail: Order 1 - Order 2/Output/GMV_x_REM_end_date.csv  -- mac dinh hien tai

Output: dashboard_data.csv (1 dong / 1 don) voi cot chuan:
  uid, team, sale, teacher, package, order_id,
  value_chain, vc_order_num,
  end_date, end_month, pay_month, real_money, status,
  renewed, next_pay_month, days_to_renew, renew_timing
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

_BASE_CANDS = [Path(r"C:\Users\ASUS\Desktop\Palfish data"), Path(__file__).resolve().parent.parent]
BASE = next((p for p in _BASE_CANDS if (p / "Order 1 - Order 2").exists()), _BASE_CANDS[-1])
HERE = Path(__file__).resolve().parent

SRC_DA1RP = HERE / "remaining_lesson_with_vc.csv"
SRC_OD1RP = BASE / "Order 1 - Order 2" / "Output" / "GMV_x_REM_end_date.csv"
OUT = HERE / "dashboard_data.csv"


def _to_dt(s):
    return pd.to_datetime(s, errors="coerce")


def from_od1rp(df):
    d = pd.DataFrame()
    d["uid"] = df["Uid_final"].astype(str).str.strip()
    d["team"] = df.get("Team", "").fillna("").str.strip()
    d["sale"] = df.get("Sale_name", "").fillna("").str.strip()
    d["teacher"] = df.get("Teacher", "").fillna("").str.strip()
    d["package"] = df.get("Study_Package", "").fillna("").str.strip()
    d["order_id"] = df.get("Order ID", "").astype(str).str.strip()
    d["value_chain"] = df.get("Value_chain", "").fillna("")
    d["vc_order_num"] = pd.to_numeric(df.get("order_number_of_value_chain"), errors="coerce")
    fr = df.get("Final_Reporting_date", "").astype(str)
    ce = df.get("contractual_end_date", "")
    d["end_date"] = _to_dt(fr.where(fr.str.len() > 3, ce))
    d["pay_month"] = df.get("Pay_month", "").fillna("")
    d["real_money"] = pd.to_numeric(df.get("real_money"), errors="coerce").fillna(0)
    d["status"] = df.get("Status_of_order_id", "").fillna("")
    d["_pay_dt"] = _to_dt(df.get("Purchase Time").where(df.get("Purchase Time").astype(str).str.len() > 3, df.get("pay_time")))
    return d


def from_da1rp(df):
    # mapping cho export DA1RP (ten cot lowercase tu remaining_lesson3)
    d = pd.DataFrame()
    d["uid"] = df["uid"].astype(str).str.strip()
    d["team"] = df.get("depart7_name_sale", "").fillna("").str.strip()
    d["sale"] = df.get("sale", "").fillna("").str.strip()
    d["teacher"] = df.get("teacher", "").fillna("").str.strip()
    d["package"] = df.get("package_name", "").fillna("").str.strip()
    d["order_id"] = df.get("order_id", "").astype(str).str.strip()
    d["value_chain"] = df.get("value_chain", "").fillna("")
    d["vc_order_num"] = pd.to_numeric(df.get("vc_order_num"), errors="coerce")
    d["end_date"] = _to_dt(df.get("end_date_n"))
    d["pay_month"] = _to_dt(df.get("payment_n")).dt.strftime("%Y-%m")
    d["real_money"] = pd.to_numeric(df.get("order_price_vnd"), errors="coerce").fillna(0)
    d["status"] = df.get("type_lesson", "").fillna("")
    d["_pay_dt"] = _to_dt(df.get("payment_n"))
    return d


def enrich(d):
    d = d[d["uid"].notna() & (d["uid"] != "") & (d["uid"].str.lower() != "nan")].copy()
    d["end_month"] = d["end_date"].dt.strftime("%Y-%m")
    d["chain_key"] = d["uid"] + "|" + d["value_chain"].astype(str)
    d = d.sort_values(["chain_key", "vc_order_num", "_pay_dt"])
    # next order (cung chain) -> renewed + thoi diem mua tiep
    maxno = d.groupby("chain_key")["vc_order_num"].transform("max")
    d["renewed"] = d["vc_order_num"] < maxno
    d["next_pay_dt"] = d.groupby("chain_key")["_pay_dt"].shift(-1)
    d["next_pay_month"] = d["next_pay_dt"].dt.strftime("%Y-%m")
    d["days_to_renew"] = (d["next_pay_dt"] - d["end_date"]).dt.days
    def timing(x):
        if pd.isna(x):
            return ""
        if x < -7:
            return "Som (truoc han)"
        if x <= 7:
            return "Dung han"
        if x <= 90:
            return "Tre"
        return "Rat tre (>90d)"
    d["renew_timing"] = d["days_to_renew"].apply(timing)
    cols = ["uid", "team", "sale", "teacher", "package", "order_id",
            "value_chain", "vc_order_num", "end_date", "end_month", "pay_month",
            "real_money", "status", "renewed", "next_pay_month", "days_to_renew", "renew_timing"]
    return d[cols]


def main():
    if SRC_DA1RP.exists():
        print("Nguon: DA1RP export ->", SRC_DA1RP)
        raw = pd.read_csv(SRC_DA1RP, dtype=str)
        d = from_da1rp(raw)
    else:
        print("Nguon: OD1RP detail ->", SRC_OD1RP)
        raw = pd.read_csv(SRC_OD1RP, dtype=str, encoding="utf-8-sig")
        d = from_od1rp(raw)
    out = enrich(d)
    out.to_csv(OUT, index=False, encoding="utf-8-sig")
    print("Da ghi:", OUT, "| rows:", len(out))
    print("end_month range:", out["end_month"].dropna().min(), "->", out["end_month"].dropna().max())


if __name__ == "__main__":
    main()
