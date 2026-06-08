# -*- coding: utf-8 -*-
"""Nap moi (seed) state/snapshot_prev.csv MOT LAN tu export DA1RP remaining_lesson3.
Sau khi seed, DA-OD1RP ke thua end_date 'da dong bang' cua DA1RP cho cac don da xong,
roi tu duy tri -> KHONG can DB nua.

Cach dung:
  1) Export remaining_lesson3 ra CSV. Can it nhat 4 cot (theo thu tu hoac co header):
     uid, order_id, end_date_n, remain_lesson_number
  2) Dat file ten 'da1rp_remaining_lesson3.csv' canh file nay (hoac sua SRC ben duoi).
  3) python seed_snapshot.py
Chiu duoc encoding UTF-16/UTF-8(-BOM) va xuong dong kieu \\r (SSMS).
"""
import io
import re
import pandas as pd
from pathlib import Path
from config import SNAPSHOT_PREV

HERE = Path(__file__).resolve().parent
SRC = HERE / "da1rp_remaining_lesson3.csv"   # doi ten o day neu can

EXPECT = ["uid", "order_id", "end_date_n", "remain_lesson_number"]


def _decode(path):
    raw = open(path, "rb").read()
    if not raw:
        raise SystemExit(f"❌ File rong (0 byte): {path}. Hay chep lai file that vao day.")
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff") or raw.count(b"\x00") > len(raw) * 0.2:
        enc = "utf-16"
    elif raw[:3] == b"\xef\xbb\xbf":
        enc = "utf-8-sig"
    else:
        enc = "utf-8"
    try:
        text = raw.decode(enc, errors="replace")
    except Exception:
        text = raw.decode("utf-8", errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n").lstrip("﻿")


def _clean(x):
    return re.sub(r"\.0$", "", str(x)).strip()


def main():
    if not SRC.exists():
        print(f"❌ Khong thay {SRC.name}. Dat file export remaining_lesson3 vao thu muc nay.")
        return
    text = _decode(SRC)
    # Doc co header truoc
    df = pd.read_csv(io.StringIO(text), dtype=str)
    low = {c.lower().strip(): c for c in df.columns}
    have = all(any(k == col for col in low) for k in ["uid", "order_id"]) and \
           any("end_date" in col for col in low)
    if not have:
        # Khong co header -> doc lai theo vi tri 4 cot dau
        df = pd.read_csv(io.StringIO(text), dtype=str, header=None)
        df = df.iloc[:, :4]
        df.columns = EXPECT
        c_uid, c_oid, c_end, c_rem = EXPECT
        print("  (file khong co header -> dung 4 cot theo thu tu)")
    else:
        c_uid = low.get("uid")
        c_oid = low.get("order_id", low.get("order id"))
        c_end = next(low[c] for c in low if "end_date" in c)
        c_rem = next((low[c] for c in low if "remain" in c), None)

    out = pd.DataFrame({
        "key": df[c_uid].map(_clean) + "|" + df[c_oid].map(_clean),
        "end_date_N": pd.to_datetime(df[c_end], errors="coerce").astype(str),
        "remain": pd.to_numeric(df[c_rem], errors="coerce").fillna(0).astype(int) if c_rem else 0,
    })
    out = out[(out["end_date_N"].notna()) & (out["end_date_N"] != "NaT") & (out["key"] != "|")]
    SNAPSHOT_PREV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(SNAPSHOT_PREV, index=False, encoding="utf-8-sig")
    print(f"✅ Da seed {len(out)} don vao {SNAPSHOT_PREV}")
    print("   Chay tiep: python run_etl.py")


if __name__ == "__main__":
    main()
