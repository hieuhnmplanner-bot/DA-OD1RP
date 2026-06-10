# -*- coding: utf-8 -*-
"""
DA-OD1RP — Build dashboard ĐỒNG NHẤT 100% với DA1RP.

Doc THANG file export remaining_lesson3 cua DA1RP (cung universe + end_date + status + team),
chi TINH THEM value_chain / vc_order_num de co view OD1 -> OD2. Khong tinh lai tu file tho.

Input:  da1rp_remaining_lesson3.csv  (export remaining_lesson3, NEN co header)
Output: outputs/dashboard_data.csv

Export goi y (BAT header khi luu trong SSMS):
  SELECT uid, order_id, end_date_n, remain_lesson_number, status_renew,
         teacher, sale, depart7_name_sale, order_price_vnd, purchase_time,
         order_num, type_lesson, type_sale, package_name
  FROM remaining_lesson3
"""
import io, re
import pandas as pd
import numpy as np
from pathlib import Path
from config import OUTPUT_DIR, DA1RP_SEED

RENEWAL = ["Early Renewal", "On-time Renewal", "Late Renewal"]

# ten cot trong file -> ten chuan (nhan dien linh hoat, khong phan biet hoa/thuong/khoang trang)
ALIASES = {
    "uid": ["uid"],
    "order_id": ["order_id", "orderid"],
    "end_date_n": ["end_date_n", "end_date", "enddate", "end_date_n_n"],
    "remain_lesson": ["remain_lesson_number", "remain_lesson", "remain lesson", "remainlesson"],
    "status_renew": ["status_renew", "status renewal", "statusrenewal"],
    "teacher": ["teacher", "advisor", "ten_gvcn"],
    "sale": ["sale"],
    "team": ["depart7_name_sale", "sale_team", "sale team", "saleteam", "team"],
    "real_money": ["order_price_vnd", "gmv_latest", "gmv latest", "gmv"],
    "purchase_time": ["purchase_time", "payment_n", "purchase time"],
    "order_num": ["order_num", "order_number", "ordernum"],
    "status": ["type_lesson", "status"],
    "source_type": ["type_sale", "source_name", "source_type"],
    "package": ["package_name", "package"],
    "renewal_payment": ["payment_number_n_1", "payment_number_n1", "renewal_payment", "payment_n_1"],
}


def _norm(c):
    return re.sub(r"\s+", "", str(c).strip().lower()).replace("-", "_")


def _decode(path):
    raw = open(path, "rb").read()
    if not raw:
        raise SystemExit(f"❌ File rong: {path}")
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff") or raw.count(b"\x00") > len(raw) * 0.2:
        enc = "utf-16"
    elif raw[:3] == b"\xef\xbb\xbf":
        enc = "utf-8-sig"
    else:
        enc = "utf-8"
    return raw.decode(enc, errors="replace").replace("\r\n", "\n").replace("\r", "\n").lstrip("﻿")


def _resolve(df):
    cols = {_norm(c): c for c in df.columns}
    out = {}
    for std, al in ALIASES.items():
        for a in al:
            if _norm(a) in cols:
                out[std] = cols[_norm(a)]
                break
    return out


def main():
    # thu tu cot khi export KHONG co header (dung dung thu tu nay trong cau SQL)
    POS = ["uid", "order_id", "end_date_n", "remain_lesson_number", "status_renew",
           "teacher", "sale", "depart7_name_sale", "order_price_vnd", "purchase_time",
           "order_num", "type_lesson", "payment_number_n_1"]
    need = ["uid", "order_id", "end_date_n", "status_renew", "team"]
    text = _decode(str(DA1RP_SEED))
    df = pd.read_csv(io.StringIO(text), dtype=str)
    m = _resolve(df)
    if any(k not in m for k in need):
        # Khong co header -> doc lai theo vi tri cot
        df = pd.read_csv(io.StringIO(text), dtype=str, header=None)
        df = df.iloc[:, :len(POS)]
        df.columns = POS[:df.shape[1]]
        m = _resolve(df)
        print("  (file khong co header -> dung thu tu cot mac dinh)")
    missing = [k for k in need if k not in m]
    if missing:
        raise SystemExit(
            "❌ File thieu cot bat buoc: " + ", ".join(missing) +
            "\n   Export remaining_lesson3 (CO header cang tot) voi cac cot theo thu tu:\n   " +
            ", ".join(POS) + "\n   Cot doc duoc: " + ", ".join(map(str, df.columns)))

    # --- Chan doan: giup phat hien export thieu dong / sai cot ---
    n = len(df)
    end_ok = pd.to_datetime(df[m["end_date_n"]], errors="coerce").notna().sum()
    print(f"  [check] {n} dong | {end_ok} dong co end_date hop le ({end_ok*100//max(n,1)}%)")
    if n < 8000:
        print(f"  ⚠️  CHI CO {n} dong — co ve export BI THIEU/LOC. remaining_lesson3 thuong > 16000 dong.")
    if end_ok < n * 0.5:
        print("  ⚠️  Qua nhieu end_date trong — co the SAI COT (export khong header + sai thu tu). "
              "Hay export CO HEADER.")

    g = lambda k: df[m[k]] if k in m else ""
    out = pd.DataFrame()
    out["uid"] = g("uid").map(lambda x: re.sub(r"\.0$", "", str(x)).strip())
    out["team"] = g("team").fillna("").replace("", "Other") if "team" in m else "Other"
    out["sale"] = g("sale").fillna("") if "sale" in m else ""
    out["teacher"] = g("teacher").fillna("") if "teacher" in m else ""
    out["package"] = g("package").fillna("") if "package" in m else ""
    out["order_id"] = g("order_id").astype(str)
    out["end_date"] = pd.to_datetime(g("end_date_n"), errors="coerce")
    out["purchase_time"] = pd.to_datetime(g("purchase_time"), errors="coerce") if "purchase_time" in m else pd.NaT
    out["end_month"] = out["end_date"].dt.strftime("%Y-%m")
    out["pay_month"] = out["purchase_time"].dt.strftime("%Y-%m")
    out["real_money"] = pd.to_numeric(g("real_money"), errors="coerce").fillna(0) if "real_money" in m else 0
    out["remain_lesson"] = pd.to_numeric(g("remain_lesson"), errors="coerce") if "remain_lesson" in m else np.nan
    out["order_num"] = pd.to_numeric(g("order_num"), errors="coerce") if "order_num" in m else np.nan
    out["status"] = g("status").fillna("") if "status" in m else ""
    out["status_renew"] = g("status_renew").where(g("status_renew").notna(), "")
    out["source_type"] = g("source_type").fillna("") if "source_type" in m else ""
    out["renewal_payment"] = pd.to_numeric(g("renewal_payment"), errors="coerce").fillna(0) if "renewal_payment" in m else 0

    # ---- TINH THEM value_chain / vc_order_num (reset khi nghi > 90 ngay) ----
    out = out.sort_values(["uid", "purchase_time", "order_num"]).reset_index(drop=True)
    prev_end = out.groupby("uid")["end_date"].shift(1)
    gap = (out["purchase_time"] - prev_end).dt.days
    new_chain = prev_end.isna() | (gap > 90)
    idx = new_chain.groupby(out["uid"]).cumsum().astype(int)
    out["value_chain"] = "VC-" + idx.map(lambda x: f"{int(x):02d}")
    out["vc_order_num"] = out.groupby([out["uid"], idx]).cumcount() + 1

    out["renewed"] = out["status_renew"].isin(RENEWAL)

    # CHOT CHAN: neu qua nhieu end_date rong -> sai cot (export headerless sai thu tu)
    _valid = float(out["end_date"].notna().mean())
    if _valid < 0.5:
        raise SystemExit(
            f"❌ Chi {_valid*100:.0f}% dong co end_date hop le -> NHIEU KHA NANG SAI COT.\n"
            "   Nguyen nhan: file export KHONG co header va thu tu cot khac voi ky vong,\n"
            "   nen end_date bi doc nham tu cot khac.\n"
            "   CACH SUA: export remaining_lesson3 CO HEADER (bat 'Include column headers' trong SSMS).\n"
            "   Khi co header, build map theo TEN cot -> khong bao gio lech. File HONG nay KHONG duoc ghi.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dash = OUTPUT_DIR / "dashboard_data.csv"
    out.to_csv(dash, index=False, encoding="utf-8-sig")
    print(f"✅ Da ghi {dash}  ({len(out)} don)")
    print("   Khop 100% voi DA1RP (cung remaining_lesson3) + da co value_chain OD1->OD2.")
    j = out[out["end_month"] == "2026-06"]
    print("   Check 2026-06 status_renew:", j["status_renew"].value_counts().to_dict())
    pm = out[out["end_month"].fillna("").str.startswith("2026")].groupby("end_month")["uid"].nunique()
    print("   Khach den han per-thang 2026 (chart):", pm.to_dict())


if __name__ == "__main__":
    main()
