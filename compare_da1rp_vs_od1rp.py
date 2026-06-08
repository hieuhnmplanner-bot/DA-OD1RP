# -*- coding: utf-8 -*-
"""
So sanh OD1RP vs DA1RP: vi sao "khach den han" thang X / team Y lech nhau.
Chay tren file chi tiet theo tung don cua OD1RP:
    Order 1 - Order 2/Output/GMV_x_REM_end_date.csv
Muc tieu: tai hien cach DEM cua 2 du an tren CUNG 1 tap du lieu de boc tach
nguyen nhan lech (anchor order khac nhau + thang dao han bi "dong bang").
"""
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

_CANDIDATES = [
    Path(r"C:\Users\ASUS\Desktop\Palfish data"),
    Path(__file__).resolve().parent.parent,
]
BASE = next((p for p in _CANDIDATES if (p / "Order 1 - Order 2").exists()), _CANDIDATES[0])
SRC = BASE / "Order 1 - Order 2" / "Output" / "GMV_x_REM_end_date.csv"
OUT = BASE / "DA-OD1RP" / "HCM_2026-06_audit.csv"

TARGET_MONTH = "2026-06"
TARGET_TEAM = "HCM team"


def f(v):
    return (v or "").strip()


def i(v):
    try:
        return int(float(v))
    except Exception:
        return None


def eligible(r):
    """OD1RP loai Frozen / On-hold khoi KPI."""
    fr = i(r.get("Is Frozen"))
    st = f(r.get("Status_of_order_id"))
    return not ((fr is not None and fr > 0) or st == "On-hold")


def purchase_dt(r):
    s = f(r.get("Purchase Time")) or f(r.get("pay_time"))
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return datetime.min


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
    by_uid = defaultdict(list)
    for r in rows:
        by_uid[f(r.get("Uid_final"))].append(r)

    od1 = [
        r for r in rows
        if f(r.get("order_number_of_value_chain")) == "1"
        and f(r.get("Final_Reporting_Month")) == TARGET_MONTH
        and f(r.get("Team")) == TARGET_TEAM
        and eligible(r)
    ]
    od1_uids = {f(r.get("Uid_final")) for r in od1}

    da_active, da_any = set(), set()
    for uid, rs in by_uid.items():
        if not uid:
            continue
        last = max(rs, key=purchase_dt)
        if f(last.get("Team")) != TARGET_TEAM:
            continue
        if f(last.get("Final_Reporting_Month")) == TARGET_MONTH:
            da_any.add(uid)
            rem = i(last.get("Remain lesson Number"))
            if rem is not None and rem > 0:
                da_active.add(uid)

    print("== %s / %s ==" % (TARGET_TEAM, TARGET_MONTH))
    print("OD1RP (neo Order-1)                  : %d" % len(od1_uids))
    print("DA1RP-mo phong (don moi nhat, active): %d" % len(da_active))
    print("DA1RP-mo phong (don moi nhat, moi tt): %d" % len(da_any))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    cat_renewed = "Da gia han OD2+ (DA1RP xep sang thang khac)"
    cat_finished = "Da hoc het remain<=0 (DA1RP danh Expired)"
    cat_both = "Con active, OD1 = don moi nhat (ca 2 deu dem)"
    with open(OUT, "w", encoding="utf-8-sig", newline="") as fo:
        w = csv.writer(fo)
        w.writerow([
            "Uid_final", "so_don_tong", "OD1_Final_Reporting_Month",
            "don_moi_nhat_Final_Reporting_Month", "don_moi_nhat_remain",
            "don_moi_nhat_status", "phan_loai",
        ])
        for uid in sorted(od1_uids):
            rs = by_uid[uid]
            last = max(rs, key=purchase_dt)
            n = len(rs)
            rem = i(last.get("Remain lesson Number"))
            last_m = f(last.get("Final_Reporting_Month"))
            st = f(last.get("Status_of_order_id"))
            if n > 1 and last_m != TARGET_MONTH:
                cat = cat_renewed
            elif rem is None or rem <= 0:
                cat = cat_finished
            else:
                cat = cat_both
            w.writerow([uid, n, TARGET_MONTH, last_m, rem, st, cat])
    print("\nDa xuat audit: %s" % OUT)


if __name__ == "__main__":
    main()
