# -*- coding: utf-8 -*-
"""Stage 3-5: due date (end_date_N) + value_chain + status. Port cong thuc DA1RP, khong DB.
Co che 'dong bang' don da het: thay snapshot DB bang file state cuc bo (state/snapshot_prev.csv).
"""
import pandas as pd
import numpy as np
from datetime import timedelta
from config import SNAPSHOT_PREV

TODAY = pd.Timestamp.now().normalize()
YESTERDAY = TODAY - pd.Timedelta(days=1)

def _normkey(s):
    s = str(s).strip()
    return s[:-2] if s.endswith('.0') else s


def _dur(lessons):
    """duration ngay = (n//2)*7 + (n%2)*3.5  -- giong het DA1RP (gia dinh 2 buoi/tuan)."""
    lessons = pd.to_numeric(lessons, errors="coerce").fillna(0).astype(int)
    return (lessons // 2) * 7 + (lessons % 2) * 3.5


def build_orders(rl):
    """rl = remaining_lesson da lam sach (tu ingest.load_remaining_lesson).
    Tra ve DataFrame don hang voi end_date_N, value_chain, status."""
    df = rl.copy()
    df = df.rename(columns={"Remain lesson Number": "Remain_Lesson"})
    df["Total Lesson"] = pd.to_numeric(df["Total Lesson"], errors="coerce").fillna(0).astype(int)
    df["Remain_Lesson"] = pd.to_numeric(df["Remain_Lesson"], errors="coerce").fillna(0).astype(int)
    df["payment_N"] = pd.to_datetime(df["Purchase Time"], errors="coerce")
    df = df.sort_values(["UID", "payment_N"]).reset_index(drop=True)

    # order_num (cong don tron doi moi UID) -- giong DA1RP
    df["order_num"] = df.groupby("UID").cumcount() + 1
    df["max_order"] = df.groupby("UID")["order_num"].transform("max")

    # neu don cuoi cua UID con remain>0 -> cac don truoc coi nhu da dung het (remain=0)
    uid_max_has_remain = (df["order_num"] == df["max_order"]) & (df["Remain_Lesson"] > 0)
    uid_max_has_remain = uid_max_has_remain.groupby(df["UID"]).transform("max")
    df.loc[(df["order_num"] < df["max_order"]) & uid_max_has_remain, "Remain_Lesson"] = 0

    df["duration"] = _dur(df["Total Lesson"])
    df["duration_remain"] = _dur(df["Remain_Lesson"])

    # ---- end_date_N: don cuoi+con buoi -> hom nay + duration_remain; con lai -> purchase + duration (noi tiep) ----
    end_dates = []
    prev_end = {}
    for row in df.itertuples():
        uid = row.UID
        is_max = row.order_num == row.max_order
        if is_max and row.Remain_Lesson > 0:
            new_end = TODAY + pd.to_timedelta(float(row.duration_remain), unit="D")
        else:
            base = row.payment_N + pd.to_timedelta(float(row.duration), unit="D") if pd.notna(row.payment_N) else pd.NaT
            pe = prev_end.get(uid)
            if pd.notna(base) and pe is not None and pd.notna(pe) and row.payment_N <= pe:
                new_end = pe + (base - row.payment_N)
            else:
                new_end = base
        end_dates.append(new_end)
        prev_end[uid] = new_end
    df["end_date_N"] = pd.to_datetime(pd.Series(end_dates, index=df.index))

    # ---- Co On-hold (con buoi nhung nghi >90 ngay): KHONG chieu end_date = hom nay + remain ----
    _last = pd.to_datetime(df["Last class time"], errors="coerce")
    _idle = (TODAY - _last).dt.days
    df["_onhold"] = (df["Remain_Lesson"] > 0) & ((_idle > 90) | (_last.isna()))

    # ---- DONG BANG bang state cuc bo (thay snapshot DB): don da het HOAC On-hold ----
    df = _apply_freeze(df)

    # ---- value_chain (reset khi gap > 90 ngay) ----
    df = df.sort_values(["UID", "payment_N", "order_num"]).reset_index(drop=True)
    prev_end_s = df.groupby("UID")["end_date_N"].shift(1)
    gap = (df["payment_N"] - prev_end_s).dt.days
    new_chain = prev_end_s.isna() | (gap > 90)
    df["_vc_idx"] = new_chain.groupby(df["UID"]).cumsum().astype(int)
    df["value_chain"] = "VC-" + df["_vc_idx"].apply(lambda x: f"{int(x):02d}")
    df["vc_order_num"] = df.groupby(["UID", "_vc_idx"]).cumcount() + 1

    # ---- status ----
    df["end_date_N+1"] = df.groupby("UID")["end_date_N"].shift(-1)
    df["payment_N+1"] = df.groupby("UID")["payment_N"].shift(-1)
    diff = (df["end_date_N"].dt.floor("D") - df["payment_N+1"].dt.floor("D")) / pd.Timedelta(days=1)
    df["status_renew"] = np.select(
        [diff > 30, (diff >= 1) & (diff <= 30), (diff >= -90) & (diff < 1), diff < -90],
        ["Early Renewal", "On-time Renewal", "Late Renewal", "Return after End_date 90 days"],
        default=None)
    df.loc[df["Remain_Lesson"].eq(0) & df["status_renew"].isna(), "status_renew"] = "Expired"

    last = pd.to_datetime(df["Last class time"], errors="coerce")
    idle = (TODAY - last).dt.days
    df["type_lesson"] = np.select(
        [(df["Remain_Lesson"] > 0) & ((idle > 90) | (last.isna())),
         (df["Remain_Lesson"] <= 0),
         (df["Remain_Lesson"] > 0) & (idle <= 90) & (last.notna())],
        ["On hold", "Expired", "In progress"], default="Unknown")

    is_maxacc = df["order_num"].eq(df.groupby("UID")["order_num"].transform("max"))
    df["account_status"] = np.select(
        [is_maxacc & (df["Remain_Lesson"] == 0), is_maxacc],
        ["Expired", "Active"], default=None)

    df["month_end_date"] = df["end_date_N"].dt.strftime("%Y-%m")
    return df.drop(columns=["_vc_idx"])


def _apply_freeze(df):
    """Neu don da tung 'het' (remain=0) trong lan chay truoc -> giu nguyen end_date cu.
    Tranh end_date nhay thang giua cac ngay. Luu/doc state cuc bo (state/snapshot_prev.csv)."""
    key = df["UID"].astype(str).map(_normkey) + "|" + df["Order ID"].astype(str).map(_normkey)
    if SNAPSHOT_PREV.exists():
        prev = pd.read_csv(SNAPSHOT_PREV, dtype=str)
        prev_map = dict(zip(prev["key"], prev["end_date_N"]))
        prev_rem = dict(zip(prev["key"], pd.to_numeric(prev["remain"], errors="coerce")))
        frozen = []
        onhold_list = df["_onhold"].tolist() if "_onhold" in df.columns else [False] * len(df)
        for k, cur_end, rem, oh in zip(key, df["end_date_N"], df["Remain_Lesson"], onhold_list):
            pe = prev_map.get(k)
            # Don da het (remain=0) HOAC On-hold (nghi >90 ngay) + co trong snapshot
            # -> dung end_date da dong bang (giong DA1RP). Chi don dang hoc that moi tinh hom nay + remain.
            if (rem == 0 or oh) and pe and str(pe) not in ("", "nan", "NaT"):
                fe = pd.to_datetime(pe, errors="coerce")
                frozen.append(fe if pd.notna(fe) else cur_end)
            else:
                frozen.append(cur_end)
        df["end_date_N"] = pd.to_datetime(pd.Series(frozen, index=df.index))
    # ghi state moi cho lan sau
    out = pd.DataFrame({"key": key, "end_date_N": df["end_date_N"].astype(str),
                        "remain": df["Remain_Lesson"].astype(int)})
    out.to_csv(SNAPSHOT_PREV, index=False, encoding="utf-8-sig")
    return df
