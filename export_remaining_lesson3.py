# -*- coding: utf-8 -*-
"""
DA-OD1RP — Tu dong XUAT remaining_lesson3 tu SQL Server ra CSV (CO header chuan).
Thay hoan toan buoc export tay trong SSMS -> het loi thieu cot / sai thu tu / thieu dong.

CHI DOC (SELECT) — KHONG sua DB. Chay SAU khi DA1RP da chay xong.
Output: da1rp_remaining_lesson3.csv  (seed cho build_dashboard.py)
"""
import sys
import pandas as pd
from config import DA1RP_SEED

# --- Ket noi giong DA1RP (Windows auth). Doi SERVER_NAME neu chay may khac. ---
DRIVER_NAME = "ODBC Driver 17 for SQL Server"
SERVER_NAME = "DESKTOP-711LV1D"
DATABASE_NAME = "palfish"
CONN_STR = (
    f"DRIVER={{{DRIVER_NAME}}};SERVER={SERVER_NAME};"
    f"DATABASE={DATABASE_NAME};Trusted_Connection=yes;"
)

# Lay dung cac cot build_dashboard can, CO header -> map theo TEN, khong bao gio lech.
QUERY = """
SELECT uid, order_id, end_date_n, remain_lesson_number, status_renew,
       teacher, sale, depart7_name_sale, order_price_vnd, purchase_time,
       order_num, type_lesson, type_sale, package_name, payment_number_n_1,
       last_class_time
FROM remaining_lesson3
"""


def main():
    try:
        import pyodbc
    except ImportError:
        sys.exit("X Thieu pyodbc. Cai: pip install pyodbc")
    try:
        conn = pyodbc.connect(CONN_STR)
    except Exception as e:
        sys.exit(
            f"X Khong ket noi duoc SQL Server ({SERVER_NAME}/{DATABASE_NAME}).\n"
            "   Kiem tra: SQL Server dang chay + dung SERVER_NAME.\n"
            f"   Chi tiet: {e}")

    cur = conn.cursor()
    cur.execute(QUERY)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()
    df = pd.DataFrame.from_records([tuple(r) for r in rows], columns=cols)

    n = len(df)
    end_ok = pd.to_datetime(df["end_date_n"], errors="coerce").notna().sum()
    df.to_csv(DA1RP_SEED, index=False, encoding="utf-8-sig")
    print(f"OK Da xuat {n} dong -> {DA1RP_SEED}")
    print(f"   end_date_n hop le: {end_ok}/{n} ({end_ok * 100 // max(n, 1)}%)")
    if n < 8000:
        print("   !! It hon 8000 dong — kiem tra DA1RP da chay xong chua.")


if __name__ == "__main__":
    main()
